import sys
import json
from typing import List, Tuple, Dict, Any
import pandas as pd
import numpy as np
import re
from collections import Counter


EXPECTED_COLUMNS = ['Unnamed: 0', 'Product', 'Packsize', 'Headoffice ID', 'Barcode', 'OrderList',
                    'Branch Name', 'Dept Fullname', 'Group Fullname', 'Trade Price', 'RRP',
                    'Sale Date', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate',
                    'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 'Refund Qty',
                    'Refund Value']


def load_dataset(file_path: str) -> pd.DataFrame:
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path, delimiter=',')
    return df

# 1) Missing Product Names
def check_missing_values(df: pd.DataFrame) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Detect only error type #1: Missing Product Names.
    - Product is NULL, empty, whitespace, or 'NULL'/'null'
    - Suggest imputation from Barcode when possible.
    """
    messages = []
    issues = []

    if "Product" not in df.columns:
        return messages, issues

    # Precompute barcode → most frequent Product (for imputation)
    barcode_to_product = None
    if "Barcode" in df.columns:
        tmp_df = df.copy()
        tmp_df["Product"] = tmp_df["Product"].astype(str)
        product_missing_like = tmp_df["Product"].str.strip().isin(["", "NULL", "null"])
        tmp_df.loc[product_missing_like, "Product"] = np.nan

        barcode_to_product = (
            tmp_df[~tmp_df["Product"].isna()]
            .groupby("Barcode")["Product"]
            .agg(lambda x: x.value_counts().index[0])
        )

    product_str = df["Product"].astype(str)
    missing_mask = df["Product"].isna() | product_str.str.strip().isin(["", "NULL", "null", ""])
    missing_indices = missing_mask[missing_mask].index.tolist()
    missing_count = len(missing_indices)

    if missing_count == 0:
        return messages, issues

    example_rows = missing_indices[:3]
    msg = (
        f"[Missing Product Names] ERROR: Column 'Product' has {missing_count} missing/blank values "
        f"(including '', 'NULL', whitespace). Example rows: {example_rows}. "
        f"Imputation suggested from 'Barcode' where possible."
    )
    messages.append(msg)

    lignes = {}
    for idx in missing_indices:
        row = df.iloc[idx]
        suggested = None

        if barcode_to_product is not None and "Barcode" in df.columns:
            barcode_val = row["Barcode"]
            if barcode_val in barcode_to_product.index:
                suggested = barcode_to_product.loc[barcode_val]

        lignes[str(idx)] = {
            "default": {"Product": None},
            "correction": {"Product": suggested}
        }

    issues.append({
        "type_erreur": "Missing Product Names",
        "texte_erreur": msg,
        "lignes": lignes
    })

    return messages, issues



# 2) EXACT DUPLICATE ROWS
def check_duplicates(df: pd.DataFrame) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Exact duplicates: all columns identical (including Sale ID and Sale Date).
    We do NOT drop them here, just mark them and suggest deletion (correction=None).
    """
    messages = []
    issues = []

    duplicated_mask = df.duplicated(keep=False)
    duplicate_indices = df[duplicated_mask].index.tolist()
    duplicate_count = len(duplicate_indices)

    if duplicate_count > 0:
        example_rows = duplicate_indices[:3]
        msg = (f"[Exact Duplicate Rows] ERROR: There are {duplicate_count} exact duplicate rows "
               f"(all columns identical). Example rows: {example_rows}. "
               f"Suggested fix: keep the first occurrence, drop the others.")
        messages.append(msg)

        lignes = {}
        for idx in duplicate_indices:
            row_dict = df.iloc[idx].to_dict()
            lignes[str(idx)] = {
                "default": row_dict,
                "correction": None  # implies: delete this row
            }

        issues.append({
            "type_erreur": "Exact Duplicate Rows",
            "texte_erreur": "Exact duplicate rows detected. Keep first occurrence and drop subsequent duplicates.",
            "lignes": lignes
        })

    return messages, issues



# 3) PRODUCT WHITESPACE ERRORS
def check_product_whitespace(df: pd.DataFrame) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Detect and Correct any whitespace issue in Product (leading, trailing, multiple internal spaces, etc.)
    """
    messages: List[str] = []
    issues: List[Dict[str, Any]] = []

    col_name = "Product"
    if col_name not in df.columns or df[col_name].dtype != "object":
        return messages, issues

    lignes: Dict[str, Dict[str, Any]] = {}
    error_count = 0
    example_indices: List[int] = []

    for idx, value in df[col_name].items():
        if pd.isna(value) or not isinstance(value, str):
            continue

        original = value
        # strip leading/trailing + collapse multiple internal spaces
        corrected = " ".join(original.split())

        if original != corrected:
            error_count += 1
            if len(example_indices) < 5:
                example_indices.append(idx)

            lignes[str(idx)] = {
                "default": {col_name: original},
                "correction": {col_name: corrected}
            }

    if error_count > 0:
        msg = (
            f"[Product Whitespace Errors] WARNING: Product contains whitespace errors "
            f"in {error_count} rows. Example rows: {example_indices}."
        )
        messages.append(msg)

        issues.append({
            "type_erreur": "Product Whitespace Errors",
            "texte_erreur": "Product contains whitespace errors.",
            "lignes": lignes
        })

    return messages, issues


# 4) SUPPLIER VARIATIONS (Pharmax drift)
def check_supplier_variations(df: pd.DataFrame) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Detects any supplier name that is a variant of 'Pharmax' and suggests 'Pharmax' as canonical.
    """
    messages = []
    issues = []

    if "OrderList" not in df.columns:
        return messages, issues

    lignes = {}
    variation_count = 0

    for idx, val in df["OrderList"].items():
        if pd.isna(val):
            continue
        original = str(val)
        normalized = re.sub(r"\s+", " ", original).strip()
        lower = normalized.lower()

        # anything that starts with 'pharmax' (case-insensitive) is considered a Pharmax variant
        if lower.startswith("pharmax") and normalized != "Pharmax":
            variation_count += 1
            lignes[str(idx)] = {
                "default": {"Supplier": original},
                "correction": {"Supplier": "Pharmax"}
            }

    if variation_count > 0:
        msg = (f"[Supplier Name Variations (Pharmax drift)] WARNING: Detected {variation_count} 'Pharmax' supplier "
               f"name variations (case/spacing/suffix/location). Suggested canonical name: 'Pharmax'.")
        messages.append(msg)

        issues.append({
            "type_erreur": "Supplier Name Variations (Pharmax drift)",
            "texte_erreur": "Supplier name variations detected for 'Pharmax' (normalize to 'Pharmax').",
            "lignes": lignes
        })

    return messages, issues


# 5) CATEGORY DRIFT (ExputexCoughSyrup200ml + general)
def check_category_drifts(df: pd.DataFrame) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    - Detect products that appear under multiple 'Dept Fullname' values.
    """
    messages: List[str] = []
    issues: List[Dict[str, Any]] = []

    if "Product" not in df.columns or "Dept Fullname" not in df.columns:
        return messages, issues

    product_groups = df.groupby("Product")

    for product, group in product_groups:
        if pd.isna(product):
            continue

        # Liste unique de tous les Dept Fullname non nuls pour ce produit
        unique_depts = group["Dept Fullname"].dropna().unique()
        if len(unique_depts) <= 1:
            # Pas de drift: un seul dept pour ce produit
            continue

        # On transforme en liste "classique" pour le JSON (et optionnellement triée)
        dept_list = sorted(map(str, unique_depts))

        dept_info = []
        lignes: Dict[str, Dict[str, Any]] = {}

        for dept in unique_depts:
            rows = group[group["Dept Fullname"] == dept].index.tolist()
            dept_info.append(f"'{dept}' (rows {rows[:3]})")

            # Toutes les lignes de ce dept reçoivent la même liste de corrections possibles
            for row_idx in rows:
                lignes[str(row_idx)] = {
                    "default": {"Dept Fullname": dept},
                    # Correction : on propose la LISTE complète, l'UI choisira
                    "correction": {"Dept Fullname": dept_list}
                }

        # Message plus neutre : pas de catégorie canonique imposée
        if product == "ExputexCoughSyrup200ml":
            msg_prefix = "[Category Drift] WARNING: Category drift detected for ExputexCoughSyrup200ml "
            temporal_note = "(e.g., 'OTC' in Q1 2024 vs 'OTC:Cold&Flu' from April 1, 2024). "
        else:
            msg_prefix = "[Category Drift] WARNING: Category drift detected for product "
            temporal_note = ""

        msg = (
            f"{msg_prefix}'{product}': {temporal_note}"
            f"categories found [{', '.join(dept_info)}]. "
            f"User should choose preferred 'Dept Fullname' among: {dept_list}."
        )
        messages.append(msg)

        issues.append({
            "type_erreur": "Category Drift",
            "texte_erreur": f"Category drift detected for product '{product}'. Product has multiple 'Dept Fullname' values.",
            "lignes": lignes
        })

    return messages, issues


# 6) NEAR-DUPLICATE ROWS (±1 second on Sale Date)
def check_near_duplicate_rows(df: pd.DataFrame) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Near-duplicate rows:
    - All columns identical except 'Sale Date', which differs by <= 1 second.
    Dataset is NOT changed; we just mark both rows and suggest that one be removed (correction=None).
    All rows participating in a near-duplicate pair appear in 'lignes'.
    """
    messages = []
    issues = []

    if 'Sale Date' not in df.columns:
        return messages, issues

    df_copy = df.copy()

    try:
        df_copy['Sale Date'] = pd.to_datetime(df_copy['Sale Date'])
    except Exception:
        return messages, issues

    cols_to_check = [col for col in df_copy.columns if col != 'Sale Date']

    near_dupe_pairs: List[Tuple[int, int]] = []
    lignes: Dict[str, Dict[str, Any]] = {}

    grouped = df_copy.groupby(cols_to_check, dropna=False)

    for _, group in grouped:
        if len(group) < 2:
            continue

        group_sorted = group.sort_values("Sale Date")
        times = group_sorted["Sale Date"]

        diffs = times.diff().dt.total_seconds().abs()

        candidate_indices = group_sorted.index[diffs <= 1]

        for idx in candidate_indices:
            sorted_indices = list(group_sorted.index)
            pos = sorted_indices.index(idx)
            if pos == 0:
                continue
            prev_idx = sorted_indices[pos - 1]

            near_dupe_pairs.append((prev_idx, idx))

            # We store the original rows, but set correction=None (means: candidate to drop)
            if str(prev_idx) not in lignes:
                lignes[str(prev_idx)] = {
                    "default": df.loc[prev_idx].to_dict(),
                    "correction": None
                }
            if str(idx) not in lignes:
                lignes[str(idx)] = {
                    "default": df.loc[idx].to_dict(),
                    "correction": None
                }

    if near_dupe_pairs:
        msg = (f"[Near-Duplicate Rows] WARNING: Detected {len(near_dupe_pairs)} near-duplicate row pairs "
               f"(identical on all columns except 'Sale Date', which differs by ≤ 1 second).")
        messages.append(msg)

        issues.append({
            "type_erreur": "Near-Duplicate Rows",
            "texte_erreur": "Near-duplicate rows detected (identical except for 'Sale Date' within ±1 second).",
            "lignes": lignes
        })

    return messages, issues


def compute_anomaly_stats(all_issues: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calcule le nombre de lignes concernées par chaque type d'erreur.
    Pour chaque bloc 'issue', on additionne la taille de 'lignes'.
    """
    stats = Counter()
    for issue in all_issues:
        err_type = issue.get("type_erreur", "UNKNOWN")
        nb_lignes = len(issue.get("lignes", {}))
        stats[err_type] += nb_lignes
    return dict(stats)


def main():
    if len(sys.argv) != 2:
        print("Usage: python detect_errors.py path/to/dataset.ext")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        df = load_dataset(file_path)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)

    all_messages = []
    all_issues = []

    messages, issues = check_missing_values(df)
    all_messages.extend(messages)
    all_issues.extend(issues)

    messages, issues = check_duplicates(df)
    all_messages.extend(messages)
    all_issues.extend(issues)

    messages, issues = check_product_whitespace(df)
    all_messages.extend(messages)
    all_issues.extend(issues)

    messages, issues = check_supplier_variations(df)
    all_messages.extend(messages)
    all_issues.extend(issues)

    messages, issues = check_category_drifts(df)
    all_messages.extend(messages)
    all_issues.extend(issues)

    messages, issues = check_near_duplicate_rows(df)
    all_messages.extend(messages)
    all_issues.extend(issues)

    # for msg in all_messages:
    #     print(f"- {msg}")

    if not all_messages:
        print("Aucune anomalie détectée.")

    print("\nANOMALY STATS (nb de lignes affectées)")
    print("======================================")

    stats = compute_anomaly_stats(all_issues)
    if stats:
        for err_type, count in stats.items():
            print(f"- {err_type}: {count} ligne(s) affectée(s)")
    else:
        print("Aucune anomalie.")

    output_json_path = file_path.rsplit(".", 1)[0] + "_anomalies.json"
    try:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(all_issues, f, ensure_ascii=False, indent=2)
        print(f"\nFichier JSON des anomalies sauvegardé dans : {output_json_path}")
    except Exception as e:
        print(f"\nErreur lors de l'écriture du fichier JSON : {e}")
        # print(json.dumps(all_issues, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

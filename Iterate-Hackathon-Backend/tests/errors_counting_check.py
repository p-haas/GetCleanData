import sys
import pandas as pd
import numpy as np
import re


def load_dataset(path: str) -> pd.DataFrame:
    if path.endswith(".xlsx") or path.endswith(".xls"):
        return pd.read_excel(path)
    return pd.read_csv(path, delimiter=",")


# 1. Missing Product Names
def count_missing_product_names(df: pd.DataFrame) -> int:
    """
    Missing Product Names:
    - Product is NULL, empty, whitespace, or 'NULL'/'null' (case-insensitive on value).
    """
    if "Product" not in df.columns:
        return 0

    prod_str = df["Product"].astype(str)
    mask = df["Product"].isna() | prod_str.str.strip().isin(["", "NULL", "null"])
    return int(mask.sum())


# 2. Exact Duplicate Rows
def count_exact_duplicates(df: pd.DataFrame) -> dict:
    """
    Exact Duplicate Rows:
    - All columns identical (including Sale ID, timestamp, etc.).
    Returns:
      {
        "rows_involved": number of rows that are part of duplicated groups,
        "duplicate_groups": number of duplicate groups (unique row patterns),
      }
    """
    # Mask of all rows that have at least one duplicate elsewhere
    dup_mask = df.duplicated(keep=False)
    rows_involved = int(dup_mask.sum())

    # Number of unique duplicate patterns (each group counted once)
    dup_groups = df[dup_mask].drop_duplicates().shape[0]

    return {
        "rows_involved": rows_involved,
        "duplicate_groups": dup_groups,
    }


# 3. Near Duplicate Rows (±1 second on Sale Date)
def count_near_duplicates(df: pd.DataFrame) -> dict:
    """
    Near Duplicate Rows:
    - All columns identical except 'Sale Date', which differs by <= 1 second.
    Returns:
      {
        "pairs": number of near-duplicate pairs,
        "rows_involved": number of distinct rows in those pairs
      }
    """
    if "Sale Date" not in df.columns:
        return {"pairs": 0, "rows_involved": 0}

    df_copy = df.copy()

    try:
        df_copy["Sale Date"] = pd.to_datetime(df_copy["Sale Date"])
    except Exception:
        return {"pairs": 0, "rows_involved": 0}

    cols_no_date = [c for c in df_copy.columns if c != "Sale Date"]

    near_dupe_pairs = []
    rows_set = set()

    grouped = df_copy.groupby(cols_no_date, dropna=False)

    for _, group in grouped:
        if len(group) < 2:
            continue

        group_sorted = group.sort_values("Sale Date")
        times = group_sorted["Sale Date"]
        diffs = times.diff().dt.total_seconds().abs()

        candidate_indices = group_sorted.index[diffs <= 1]

        for idx in candidate_indices:
            sorted_idx = list(group_sorted.index)
            pos = sorted_idx.index(idx)
            if pos == 0:
                continue
            prev_idx = sorted_idx[pos - 1]

            near_dupe_pairs.append((prev_idx, idx))
            rows_set.add(prev_idx)
            rows_set.add(idx)

    return {
        "pairs": len(near_dupe_pairs),
        "rows_involved": len(rows_set),
    }


# 4. Extra Whitespace in Product Names
def count_product_whitespace_errors(df: pd.DataFrame) -> int:
    """
    Extra Whitespace in Product Names:
    - Leading spaces
    - Trailing spaces
    - Multiple internal spaces
    """
    if "Product" not in df.columns:
        return 0

    col = df["Product"]

    def has_whitespace_issue(x: str) -> bool:
        if x is None or pd.isna(x):
            return False
        s = str(x)
        if s != s.strip():
            return True
        if "  " in s:  # double space
            return True
        return False

    mask = col.apply(has_whitespace_issue)
    return int(mask.sum())


# 5. Supplier Name Variations (Pharmax drift)
def count_pharmax_variations(df: pd.DataFrame) -> dict:
    """
    Supplier Name Variations:
    - Any supplier value that is a variant of 'Pharmax' (case/spacing/suffix/location).
    - Supplier column is `OrderList` in your dataset.
    Returns dict with:
      {
        "pharmax_total": total rows where normalized startswith 'pharmax',
        "canonical_pharmax": rows exactly 'Pharmax' (after strip),
        "variations": rows that startwith 'pharmax' but are not exactly 'Pharmax',
        "by_value": { value: count, ... }  # for pharmax-related only
      }
    """
    # adapter si un jour la colonne change, mais ici on sait que c'est 'OrderList'
    possible_cols = ["OrderList", "Supplier", "Supplier Name", "Supplier_Name",
                     "Manufacturer", "Manufacturer Name"]
    supplier_col = None
    for c in possible_cols:
        if c in df.columns:
            supplier_col = c
            break

    if supplier_col is None:
        return {
            "pharmax_total": 0,
            "canonical_pharmax": 0,
            "variations": 0,
            "by_value": {},
        }

    col = df[supplier_col]

    pharmax_mask = []
    canonical_mask = []

    norm_values = []

    for val in col:
        if pd.isna(val):
            norm_values.append(None)
            pharmax_mask.append(False)
            canonical_mask.append(False)
            continue

        original = str(val)
        normalized = re.sub(r"\s+", " ", original).strip()
        lower = normalized.lower()
        norm_values.append(normalized)

        is_pharmax_family = lower.startswith("pharmax")
        pharmax_mask.append(is_pharmax_family)
        canonical_mask.append(is_pharmax_family and normalized == "Pharmax")

    pharmax_mask = pd.Series(pharmax_mask, index=df.index)
    canonical_mask = pd.Series(canonical_mask, index=df.index)

    pharmax_total = int(pharmax_mask.sum())
    canonical_pharmax = int(canonical_mask.sum())
    variations = pharmax_total - canonical_pharmax

    # Count by actual supplier value for pharmax-family rows
    fam_values = pd.Series(norm_values)[pharmax_mask]
    by_value = fam_values.value_counts().to_dict()

    return {
        "pharmax_total": pharmax_total,
        "canonical_pharmax": canonical_pharmax,
        "variations": variations,
        "by_value": by_value,
    }


# 7. Category Drift (ExputexCoughSyrup200ml)
def count_category_drift(df: pd.DataFrame) -> dict:
    """
    Category Drift for product ExputexCoughSyrup200ml.
    We compute:
      - total rows for this product
      - count per Dept Fullname
      - (optionally) split before/after 2024-04-01
    """
    if "Product" not in df.columns or "Dept Fullname" not in df.columns:
        return {
            "total_rows": 0,
            "by_dept": {},
            "before_2024_04_01": {},
            "from_2024_04_01": {},
        }

    mask = df["Product"] == "ExputexCoughSyrup200ml"
    sub = df[mask]

    total_rows = int(sub.shape[0])

    by_dept = sub["Dept Fullname"].value_counts().to_dict()

    before = {}
    after = {}

    if "Sale Date" in df.columns:
        try:
            dates = pd.to_datetime(sub["Sale Date"])
            sub = sub.assign(_date=dates)
            cutoff = pd.Timestamp("2024-04-01")

            before_mask = sub["_date"] < cutoff
            after_mask = sub["_date"] >= cutoff

            before = sub[before_mask]["Dept Fullname"].value_counts().to_dict()
            after = sub[after_mask]["Dept Fullname"].value_counts().to_dict()
        except Exception:
            # si parsing date foire, on laisse before/after vides
            pass

    return {
        "total_rows": total_rows,
        "by_dept": by_dept,
        "before_2024_04_01": before,
        "from_2024_04_01": after,
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python confirm_error_counts.py path/to/dataset_with_all_errors_finals.csv")
        sys.exit(1)

    path = sys.argv[1]
    try:
        df = load_dataset(path)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)

    print("=== DATASET INFO ===")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    # 1) Missing Product Names
    missing_prod = count_missing_product_names(df)
    print("1) Missing Product Names")
    print(f"   → rows with missing/blank/NULL Product: {missing_prod} (doc says: 1133)")
    print()

    # 2) Exact Duplicate Rows
    dup_stats = count_exact_duplicates(df)
    print("2) Exact Duplicate Rows")
    print(f"   → rows involved in exact duplicates: {dup_stats['rows_involved']} (doc says: 14 rows)")
    print(f"   → number of duplicate groups (unique duplicated patterns): {dup_stats['duplicate_groups']} "
          f"(doc says: 6 exact duplicates)")
    print()

    # 3) Near Duplicate Rows
    near_stats = count_near_duplicates(df)
    print("3) Near Duplicate Rows")
    print(f"   → near-duplicate pairs (±1 second): {near_stats['pairs']} (doc says: 14 pairs)")
    print(f"   → distinct rows involved: {near_stats['rows_involved']} (doc says: 28 rows)")
    print()

    # 4) Extra Whitespace in Product Names
    ws_count = count_product_whitespace_errors(df)
    print("4) Extra Whitespace in Product Names")
    print(f"   → rows with Product whitespace issues: {ws_count} (doc says: 3338)")
    print()

    # 5) Supplier Name Variations (Pharmax drift)
    pharmax_stats = count_pharmax_variations(df)
    print("5) Supplier Name Variations (Pharmax drift)")
    print(f"   → total 'Pharmax' family rows (any variant): {pharmax_stats['pharmax_total']} "
          f"(doc says: 9,979 total Pharmax records)")
    print(f"   → canonical 'Pharmax': {pharmax_stats['canonical_pharmax']}")
    print(f"   → variations (non-exact 'Pharmax'): {pharmax_stats['variations']} "
          f"(doc says: 4,587 modified rows from April 1)")
    print("   → breakdown by supplier value for Pharmax-family:")
    for val, cnt in pharmax_stats["by_value"].items():
        print(f"      - {val!r}: {cnt}")
    print()

    # 7) Category Drift (ExputexCoughSyrup200ml)
    cat_stats = count_category_drift(df)
    print("7) Category Drift (ExputexCoughSyrup200ml)")
    print(f"   → total rows for ExputexCoughSyrup200ml: {cat_stats['total_rows']} "
          f"(doc suggests: 273 + 740 = 1013)")
    print("   → by Dept Fullname (all dates):")
    for dept, cnt in cat_stats["by_dept"].items():
        print(f"      - {dept!r}: {cnt}")

    if cat_stats["before_2024_04_01"] or cat_stats["from_2024_04_01"]:
        print("   → before 2024-04-01 (expected: OTC ~273):")
        for dept, cnt in cat_stats["before_2024_04_01"].items():
            print(f"      - {dept!r}: {cnt}")

        print("   → from 2024-04-01 (expected: OTC:Cold&Flu ~740):")
        for dept, cnt in cat_stats["from_2024_04_01"].items():
            print(f"      - {dept!r}: {cnt}")

    print("\n(Discount Context Loss intentionally ignored in this script.)")


if __name__ == "__main__":
    main()

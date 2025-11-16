import sys
from typing import List
import pandas as pd
import numpy as np

EXPECTED_COLUMNS = ['Product', 'Packsize', 'Headoffice ID', 'Barcode', 'OrderList', 'Branch Name', 'Dept Fullname', 'Group Fullname', 'Trade Price', 'RRP', 'Sale Date', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate', 'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 'Refund Qty', 'Refund Value']

def load_dataset(file_path: str) -> pd.DataFrame:
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path, delimiter=',')
    return df

def check_columns(df: pd.DataFrame) -> List[str]:
    errors = []
    actual_columns = list(df.columns)
    expected_set = set(EXPECTED_COLUMNS)
    actual_set = set(actual_columns)
    
    missing = expected_set - actual_set
    if missing:
        errors.append(f"ERROR: Missing columns: {sorted(list(missing))}.")
    
    extra = actual_set - expected_set
    if extra:
        errors.append(f"WARNING: Extra columns not in EXPECTED_COLUMNS: {sorted(list(extra))}.")
    
    return errors

def check_missing_values(df: pd.DataFrame) -> List[str]:
    errors = []
    for col in EXPECTED_COLUMNS:
        if col in df.columns:
            missing_mask = df[col].isna()
            missing_count = missing_mask.sum()
            if missing_count > 0:
                missing_indices = df[missing_mask].index.tolist()
                example_rows = missing_indices[:3]
                errors.append(f"ERROR: Column '{col}' has {missing_count} missing values. Example rows: {example_rows}.")
    return errors

def check_duplicates(df: pd.DataFrame) -> List[str]:
    errors = []
    duplicated_mask = df.duplicated(keep=False)
    duplicate_count = duplicated_mask.sum()
    if duplicate_count > 0:
        duplicate_indices = df[duplicated_mask].index.tolist()
        example_rows = duplicate_indices[:3]
        num_duplicate_sets = df[duplicated_mask].duplicated().sum()
        errors.append(f"ERROR: There are {num_duplicate_sets} duplicate rows. Example rows: {example_rows}.")
    return errors

def check_basic_types(df: pd.DataFrame) -> List[str]:
    errors = []
    numeric_candidates = ['Headoffice ID', 'Barcode', 'Trade Price', 'RRP', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate', 'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 'Refund Qty', 'Refund Value']
    
    for col in numeric_candidates:
        if col in df.columns:
            if df[col].dtype == 'object':
                non_numeric_mask = pd.to_numeric(df[col], errors='coerce').isna() & df[col].notna()
                if non_numeric_mask.any():
                    non_numeric_values = df.loc[non_numeric_mask, col].unique().tolist()[:5]
                    non_numeric_rows = df[non_numeric_mask].index.tolist()[:3]
                    errors.append(f"WARNING: Column '{col}' looks numeric but contains non-numeric values: {non_numeric_values} at rows {non_numeric_rows}.")
    
    return errors

def check_value_ranges(df: pd.DataFrame) -> List[str]:
    errors = []
    
    quantity_columns = ['Qty Sold', 'Refund Qty']
    for col in quantity_columns:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            negative_mask = (numeric_col < 0) & numeric_col.notna()
            if negative_mask.any():
                negative_values = numeric_col[negative_mask].tolist()[:5]
                negative_rows = df[negative_mask].index.tolist()[:3]
                errors.append(f"WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_rows}.")
    
    price_columns = ['Trade Price', 'RRP', 'Turnover', 'Turnover ex VAT', 'Profit']
    for col in price_columns:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            negative_mask = (numeric_col < 0) & numeric_col.notna()
            if negative_mask.any():
                negative_values = numeric_col[negative_mask].tolist()[:5]
                negative_rows = df[negative_mask].index.tolist()[:3]
                errors.append(f"WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_rows}.")
    
    vat_rate_col = 'Sale VAT Rate'
    if vat_rate_col in df.columns:
        numeric_col = pd.to_numeric(df[vat_rate_col], errors='coerce')
        invalid_mask = ((numeric_col < 0) | (numeric_col > 100)) & numeric_col.notna()
        if invalid_mask.any():
            invalid_values = numeric_col[invalid_mask].tolist()[:5]
            invalid_rows = df[invalid_mask].index.tolist()[:3]
            errors.append(f"ERROR: Column '{vat_rate_col}' has values outside [0, 100]. Values: {invalid_values} at rows {invalid_rows}.")
    
    return errors

def check_allowed_categories(df: pd.DataFrame) -> List[str]:
    errors = []
    categorical_columns = ['Branch Name', 'Dept Fullname', 'Group Fullname', 'OrderList']
    
    for col in categorical_columns:
        if col in df.columns:
            value_counts = df[col].value_counts()
            rare_categories = value_counts[value_counts == 1]
            if len(rare_categories) > 0:
                for category in rare_categories.index[:3]:
                    example_row = df[df[col] == category].index.tolist()[:1]
                    errors.append(f"WARNING: Column '{col}' has rare category '{category}' (1 occurrence). Example row: {example_row}.")
    
    return errors

def check_unique_constraints(df: pd.DataFrame) -> List[str]:
    errors = []
    unique_candidates = ['Sale ID', 'Barcode']
    
    for col in unique_candidates:
        if col in df.columns:
            duplicated_mask = df[col].duplicated(keep=False) & df[col].notna()
            if duplicated_mask.any():
                duplicate_values = df.loc[duplicated_mask, col].unique()[:3]
                for dup_val in duplicate_values:
                    dup_rows = df[df[col] == dup_val].index.tolist()[:5]
                    errors.append(f"ERROR: Column '{col}' contains duplicate value {dup_val} at rows {dup_rows}.")
    
    return errors

def check_id_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    id_columns = ['Headoffice ID', 'Barcode', 'Product']
    consistency_columns = ['Product', 'Packsize', 'Trade Price', 'RRP', 'OrderList', 'Dept Fullname', 'Group Fullname']
    
    for id_col in id_columns:
        if id_col not in df.columns:
            continue
        
        for check_col in consistency_columns:
            if check_col not in df.columns or check_col == id_col:
                continue
            
            grouped = df.groupby(id_col)[check_col].apply(lambda x: x.dropna().unique())
            inconsistent = grouped[grouped.apply(len) > 1]
            
            if len(inconsistent) > 0:
                for id_val in inconsistent.index[:3]:
                    unique_vals = inconsistent[id_val]
                    examples = []
                    for val in unique_vals[:3]:
                        example_row = df[(df[id_col] == id_val) & (df[check_col] == val)].index.tolist()[:1]
                        if example_row:
                            examples.append(f"{repr(val)} (row {example_row[0]})")
                    if examples:
                        errors.append(f"ERROR: rows with {id_col} '{id_val}' have inconsistent '{check_col}' values: [{', '.join(examples)}].")
    
    return errors

def check_date_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Sale Date' in df.columns:
        try:
            date_col = pd.to_datetime(df['Sale Date'], errors='coerce')
            invalid_mask = date_col.isna() & df['Sale Date'].notna()
            if invalid_mask.any():
                invalid_values = df.loc[invalid_mask, 'Sale Date'].tolist()[:5]
                invalid_rows = df[invalid_mask].index.tolist()[:3]
                errors.append(f"ERROR: Column 'Sale Date' has invalid date values: {invalid_values} at rows {invalid_rows}.")
            
            future_mask = date_col > pd.Timestamp.now()
            if future_mask.any():
                future_values = date_col[future_mask].tolist()[:5]
                future_rows = df[future_mask].index.tolist()[:3]
                errors.append(f"WARNING: Column 'Sale Date' has future dates: {future_values} at rows {future_rows}.")
            
            old_threshold = pd.Timestamp.now() - pd.Timedelta(days=365*10)
            old_mask = date_col < old_threshold
            if old_mask.any():
                old_values = date_col[old_mask].tolist()[:5]
                old_rows = df[old_mask].index.tolist()[:3]
                errors.append(f"WARNING: Column 'Sale Date' has dates older than 10 years: {old_values} at rows {old_rows}.")
        except Exception as e:
            errors.append(f"ERROR: Could not parse 'Sale Date' column: {str(e)}")
    
    return errors

def check_financial_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if all(col in df.columns for col in ['Turnover', 'Vat Amount', 'Turnover ex VAT']):
        turnover = pd.to_numeric(df['Turnover'], errors='coerce')
        vat_amount = pd.to_numeric(df['Vat Amount'], errors='coerce')
        turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
        
        expected_turnover = turnover_ex_vat + vat_amount
        diff = abs(turnover - expected_turnover)
        inconsistent_mask = (diff > 0.02) & turnover.notna() & vat_amount.notna() & turnover_ex_vat.notna()
        
        if inconsistent_mask.any():
            inconsistent_rows = df[inconsistent_mask].index.tolist()[:3]
            errors.append(f"ERROR: Financial inconsistency: Turnover != Turnover ex VAT + Vat Amount at rows {inconsistent_rows}.")
    
    if all(col in df.columns for col in ['RRP', 'Turnover', 'Qty Sold']):
        rrp = pd.to_numeric(df['RRP'], errors='coerce')
        turnover = pd.to_numeric(df['Turnover'], errors='coerce')
        qty_sold = pd.to_numeric(df['Qty Sold'], errors='coerce')
        
        expected_turnover = rrp * qty_sold
        diff_ratio = abs(turnover - expected_turnover) / (expected_turnover + 0.01)
        suspicious_mask = (diff_ratio > 0.5) & rrp.notna() & turnover.notna() & qty_sold.notna() & (qty_sold > 0)
        
        if suspicious_mask.any():
            suspicious_rows = df[suspicious_mask].index.tolist()[:3]
            errors.append(f"WARNING: Turnover significantly differs from RRP * Qty Sold at rows {suspicious_rows}.")
    
    if all(col in df.columns for col in ['Turnover ex VAT', 'Trade Price', 'Profit']):
        turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
        trade_price = pd.to_numeric(df['Trade Price'], errors='coerce')
        profit = pd.to_numeric(df['Profit'], errors='coerce')
        
        expected_profit = turnover_ex_vat - trade_price
        diff = abs(profit - expected_profit)
        inconsistent_mask = (diff > 0.02) & turnover_ex_vat.notna() & trade_price.notna() & profit.notna()
        
        if inconsistent_mask.any():
            inconsistent_rows = df[inconsistent_mask].index.tolist()[:3]
            errors.append(f"WARNING: Profit calculation inconsistency at rows {inconsistent_rows}.")
    
    return errors

def check_outliers(df: pd.DataFrame) -> List[str]:
    errors = []
    numeric_columns = ['Trade Price', 'RRP', 'Qty Sold', 'Turnover', 'Profit']
    
    for col in numeric_columns:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            if numeric_col.notna().sum() > 0:
                q1 = numeric_col.quantile(0.25)
                q3 = numeric_col.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 3 * iqr
                upper_bound = q3 + 3 * iqr
                
                outlier_mask = ((numeric_col < lower_bound) | (numeric_col > upper_bound)) & numeric_col.notna()
                if outlier_mask.any():
                    outlier_count = outlier_mask.sum()
                    outlier_values = numeric_col[outlier_mask].tolist()[:5]
                    outlier_rows = df[outlier_mask].index.tolist()[:3]
                    errors.append(f"WARNING: Column '{col}' has {outlier_count} potential outliers. Example values: {outlier_values} at rows {outlier_rows}.")
    
    return errors

def summarize_dataset(df: pd.DataFrame) -> List[str]:
    summary = []
    summary.append(f"INFO: Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns.")
    
    for col in df.columns:
        if col in EXPECTED_COLUMNS:
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                if numeric_col.notna().sum() > 0:
                    min_val = numeric_col.min()
                    max_val = numeric_col.max()
                    mean_val = numeric_col.mean()
                    summary.append(f"INFO: Column '{col}' (numeric) - min={min_val:.2f}, max={max_val:.2f}, mean={mean_val:.2f}.")
            else:
                distinct_count = df[col].nunique()
                summary.append(f"INFO: Column '{col}' (categorical) - {distinct_count} distinct values.")
    
    return summary

def main():
    if len(sys.argv) != 2:
        print("Usage: python detect_errors.py path/to/dataset.ext")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        df = load_dataset(file_path)
    except Exception as e:
        print(f"ERROR: Could not load dataset: {str(e)}")
        sys.exit(1)
    
    print("DATASET ERROR REPORT")
    print("=" * 50)
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print("=" * 50)
    print()
    
    all_errors = []
    
    all_errors.extend(check_columns(df))
    all_errors.extend(check_missing_values(df))
    all_errors.extend(check_duplicates(df))
    all_errors.extend(check_basic_types(df))
    all_errors.extend(check_value_ranges(df))
    all_errors.extend(check_allowed_categories(df))
    all_errors.extend(check_unique_constraints(df))
    all_errors.extend(check_id_consistency(df))
    all_errors.extend(check_date_consistency(df))
    all_errors.extend(check_financial_consistency(df))
    all_errors.extend(check_outliers(df))
    
    if all_errors:
        print("ERRORS AND WARNINGS:")
        print("-" * 50)
        for error in all_errors:
            print(f"  - {error}")
        print()
    else:
        print("No errors or warnings found.")
        print()
    
    print("DATASET SUMMARY:")
    print("-" * 50)
    summary = summarize_dataset(df)
    for line in summary:
        print(f"  {line}")
    
    print()
    print("=" * 50)
    print("END OF REPORT")

if __name__ == "__main__":
    main()
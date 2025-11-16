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
    actual_columns = set(df.columns)
    expected_columns = set(EXPECTED_COLUMNS)
    
    missing = expected_columns - actual_columns
    if missing:
        errors.append(f"ERROR: Missing columns: {sorted(list(missing))}.")
    
    extra = actual_columns - expected_columns
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
        num_duplicate_groups = df[duplicated_mask].duplicated().sum()
        errors.append(f"ERROR: There are {duplicate_count} duplicate rows. Example rows: {example_rows}.")
    return errors

def check_basic_types(df: pd.DataFrame) -> List[str]:
    errors = []
    numeric_like_columns = ['Headoffice ID', 'Barcode', 'Trade Price', 'RRP', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate', 'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 'Refund Qty', 'Refund Value']
    
    for col in numeric_like_columns:
        if col in df.columns:
            if df[col].dtype == 'object':
                non_numeric_mask = pd.to_numeric(df[col], errors='coerce').isna() & df[col].notna()
                if non_numeric_mask.any():
                    non_numeric_values = df.loc[non_numeric_mask, col].unique().tolist()[:5]
                    non_numeric_indices = df[non_numeric_mask].index.tolist()[:3]
                    errors.append(f"WARNING: Column '{col}' looks numeric but contains non-numeric values: {non_numeric_values} at rows {non_numeric_indices}.")
    
    return errors

def check_value_ranges(df: pd.DataFrame) -> List[str]:
    errors = []
    
    quantity_like_columns = ['Qty Sold', 'Refund Qty']
    for col in quantity_like_columns:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            negative_mask = numeric_col < 0
            if negative_mask.any():
                negative_values = numeric_col[negative_mask].tolist()[:5]
                negative_indices = df[negative_mask].index.tolist()[:3]
                errors.append(f"WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_indices}.")
    
    price_like_columns = ['Trade Price', 'RRP', 'Turnover', 'Turnover ex VAT', 'Profit']
    for col in price_like_columns:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            negative_mask = numeric_col < 0
            if negative_mask.any():
                negative_values = numeric_col[negative_mask].tolist()[:5]
                negative_indices = df[negative_mask].index.tolist()[:3]
                errors.append(f"WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_indices}.")
    
    if 'Sale VAT Rate' in df.columns:
        vat_col = pd.to_numeric(df['Sale VAT Rate'], errors='coerce')
        invalid_mask = (vat_col < 0) | (vat_col > 100)
        if invalid_mask.any():
            invalid_values = vat_col[invalid_mask].tolist()[:5]
            invalid_indices = df[invalid_mask].index.tolist()[:3]
            errors.append(f"ERROR: Column 'Sale VAT Rate' has values outside [0, 100]. Values: {invalid_values} at rows {invalid_indices}.")
    
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
                    example_row = df[df[col] == category].index.tolist()[0]
                    errors.append(f"WARNING: Column '{col}' has rare category '{category}' (1 occurrence). Example row: [{example_row}].")
    
    return errors

def check_unique_constraints(df: pd.DataFrame) -> List[str]:
    errors = []
    unique_like_columns = ['Sale ID', 'Barcode']
    
    for col in unique_like_columns:
        if col in df.columns:
            value_counts = df[col].value_counts()
            duplicates = value_counts[value_counts > 1]
            if len(duplicates) > 0:
                for value in duplicates.index[:3]:
                    duplicate_rows = df[df[col] == value].index.tolist()[:3]
                    errors.append(f"ERROR: Column '{col}' contains duplicate value {value} at rows {duplicate_rows}.")
    
    return errors

def check_id_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    id_columns = ['Headoffice ID', 'Barcode', 'Sale ID']
    consistency_columns = ['Product', 'Packsize', 'Trade Price', 'RRP', 'OrderList']
    
    if 'Barcode' in df.columns:
        barcode_groups = df.groupby('Barcode')
        for barcode, group in barcode_groups:
            if len(group) > 1:
                for check_col in consistency_columns:
                    if check_col in df.columns:
                        unique_values = group[check_col].dropna().unique()
                        if len(unique_values) > 1:
                            example_rows = group.index.tolist()[:3]
                            errors.append(f"ERROR: Inconsistent data for Barcode '{barcode}': multiple values in '{check_col}' found {unique_values.tolist()[:5]}. Example rows: {example_rows}.")
                            break
    
    if 'Headoffice ID' in df.columns:
        headoffice_groups = df.groupby('Headoffice ID')
        for hoid, group in headoffice_groups:
            if len(group) > 1:
                for check_col in ['Product', 'Packsize']:
                    if check_col in df.columns:
                        unique_values = group[check_col].dropna().unique()
                        if len(unique_values) > 1:
                            example_rows = group.index.tolist()[:3]
                            errors.append(f"ERROR: Inconsistent data for Headoffice ID '{hoid}': multiple values in '{check_col}' found {unique_values.tolist()[:5]}. Example rows: {example_rows}.")
                            break
    
    return errors

def check_date_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Sale Date' in df.columns:
        try:
            date_col = pd.to_datetime(df['Sale Date'], errors='coerce')
            invalid_dates_mask = date_col.isna() & df['Sale Date'].notna()
            if invalid_dates_mask.any():
                invalid_indices = df[invalid_dates_mask].index.tolist()[:3]
                invalid_values = df.loc[invalid_dates_mask, 'Sale Date'].tolist()[:3]
                errors.append(f"ERROR: Column 'Sale Date' has invalid date values: {invalid_values} at rows {invalid_indices}.")
            
            future_dates_mask = date_col > pd.Timestamp.now()
            if future_dates_mask.any():
                future_indices = df[future_dates_mask].index.tolist()[:3]
                future_values = date_col[future_dates_mask].tolist()[:3]
                errors.append(f"WARNING: Column 'Sale Date' has future dates: {future_values} at rows {future_indices}.")
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
        tolerance = 0.02
        inconsistent_mask = (abs(turnover - expected_turnover) > tolerance) & turnover.notna() & vat_amount.notna() & turnover_ex_vat.notna()
        
        if inconsistent_mask.any():
            inconsistent_indices = df[inconsistent_mask].index.tolist()[:3]
            errors.append(f"ERROR: Financial inconsistency: Turnover != Turnover ex VAT + Vat Amount at rows {inconsistent_indices}.")
    
    if all(col in df.columns for col in ['RRP', 'Turnover', 'Qty Sold']):
        rrp = pd.to_numeric(df['RRP'], errors='coerce')
        turnover = pd.to_numeric(df['Turnover'], errors='coerce')
        qty_sold = pd.to_numeric(df['Qty Sold'], errors='coerce')
        
        expected_turnover = rrp * qty_sold
        tolerance_pct = 0.5
        inconsistent_mask = (abs(turnover - expected_turnover) / expected_turnover > tolerance_pct) & turnover.notna() & rrp.notna() & qty_sold.notna() & (qty_sold > 0)
        
        if inconsistent_mask.any():
            inconsistent_indices = df[inconsistent_mask].index.tolist()[:3]
            errors.append(f"WARNING: Turnover significantly differs from RRP * Qty Sold (possible discounts) at rows {inconsistent_indices}.")
    
    return errors

def summarize_dataset(df: pd.DataFrame) -> List[str]:
    summary = []
    summary.append(f"INFO: Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns.")
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        if col in EXPECTED_COLUMNS:
            col_min = df[col].min()
            col_max = df[col].max()
            col_mean = df[col].mean()
            summary.append(f"INFO: Column '{col}' (numeric) - min={col_min:.2f}, max={col_max:.2f}, mean={col_mean:.2f}.")
    
    categorical_columns = df.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        if col in EXPECTED_COLUMNS:
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
        print(f"ERROR: Could not load dataset: {e}")
        sys.exit(1)
    
    print("DATASET ERROR REPORT")
    print("=" * 50)
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print("=" * 50)
    
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
    
    if all_errors:
        for error in all_errors:
            print(f"- {error}")
    else:
        print("No errors or warnings found.")
    
    print("\n" + "=" * 50)
    print("DATASET SUMMARY")
    print("=" * 50)
    summary = summarize_dataset(df)
    for line in summary:
        print(f"- {line}")

if __name__ == "__main__":
    main()
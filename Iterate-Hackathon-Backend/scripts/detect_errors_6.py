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
                    non_numeric_indices = df[non_numeric_mask].index.tolist()[:3]
                    errors.append(f"WARNING: Column '{col}' looks numeric but contains non-numeric values: {non_numeric_values} at rows {non_numeric_indices}.")
    
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
                negative_indices = df[negative_mask].index.tolist()[:3]
                errors.append(f"WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_indices}.")
    
    price_columns = ['Trade Price', 'RRP', 'Turnover', 'Turnover ex VAT', 'Profit']
    for col in price_columns:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            negative_mask = (numeric_col < 0) & numeric_col.notna()
            if negative_mask.any():
                negative_values = numeric_col[negative_mask].tolist()[:5]
                negative_indices = df[negative_mask].index.tolist()[:3]
                errors.append(f"WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_indices}.")
    
    if 'Sale VAT Rate' in df.columns:
        numeric_col = pd.to_numeric(df['Sale VAT Rate'], errors='coerce')
        invalid_mask = ((numeric_col < 0) | (numeric_col > 100)) & numeric_col.notna()
        if invalid_mask.any():
            invalid_values = numeric_col[invalid_mask].tolist()[:5]
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
                    example_row = df[df[col] == category].index.tolist()[:1]
                    errors.append(f"WARNING: Column '{col}' has rare category '{category}' (1 occurrence). Example row: {example_row}.")
    
    return errors

def check_unique_constraints(df: pd.DataFrame) -> List[str]:
    errors = []
    unique_candidates = ['Sale ID', 'Barcode']
    
    for col in unique_candidates:
        if col in df.columns:
            duplicated_values = df[df.duplicated(subset=[col], keep=False)][col]
            if len(duplicated_values) > 0:
                unique_duplicates = duplicated_values.unique()[:3]
                for dup_val in unique_duplicates:
                    dup_indices = df[df[col] == dup_val].index.tolist()[:3]
                    errors.append(f"ERROR: Column '{col}' contains duplicate value {dup_val} at rows {dup_indices}.")
    
    return errors

def check_id_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    id_columns = ['Headoffice ID', 'Barcode', 'Product']
    consistency_columns = ['Product', 'Packsize', 'Trade Price', 'RRP', 'OrderList']
    
    if 'Barcode' in df.columns:
        barcode_groups = df.groupby('Barcode')
        for barcode, group in barcode_groups:
            if len(group) > 1:
                for check_col in consistency_columns:
                    if check_col in df.columns and check_col != 'Barcode':
                        unique_values = group[check_col].dropna().unique()
                        if len(unique_values) > 1:
                            example_rows = group.index.tolist()[:3]
                            example_values = unique_values[:5].tolist()
                            errors.append(f"ERROR: Inconsistent data for Barcode '{barcode}': multiple {check_col} values found {example_values}. Example rows: {example_rows} with different {check_col} and same Barcode.")
                            break
    
    if 'Headoffice ID' in df.columns:
        id_groups = df.groupby('Headoffice ID')
        for hq_id, group in id_groups:
            if len(group) > 1:
                for check_col in ['Product', 'Packsize']:
                    if check_col in df.columns:
                        unique_values = group[check_col].dropna().unique()
                        if len(unique_values) > 1:
                            example_rows = group.index.tolist()[:3]
                            example_values = unique_values[:5].tolist()
                            errors.append(f"ERROR: Inconsistent data for Headoffice ID '{hq_id}': multiple {check_col} values found {example_values}. Example rows: {example_rows} with different {check_col} and same Headoffice ID.")
                            break
    
    return errors

def check_date_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Sale Date' in df.columns:
        try:
            date_col = pd.to_datetime(df['Sale Date'], errors='coerce')
            invalid_dates = date_col.isna() & df['Sale Date'].notna()
            if invalid_dates.any():
                invalid_indices = df[invalid_dates].index.tolist()[:3]
                invalid_values = df.loc[invalid_dates, 'Sale Date'].tolist()[:3]
                errors.append(f"ERROR: Column 'Sale Date' has invalid date values: {invalid_values} at rows {invalid_indices}.")
            
            future_dates = date_col > pd.Timestamp.now()
            if future_dates.any():
                future_indices = df[future_dates].index.tolist()[:3]
                future_values = date_col[future_dates].tolist()[:3]
                errors.append(f"WARNING: Column 'Sale Date' has future dates: {future_values} at rows {future_indices}.")
        except Exception as e:
            errors.append(f"WARNING: Could not parse 'Sale Date' column: {str(e)}")
    
    return errors

def check_financial_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if all(col in df.columns for col in ['Turnover', 'Vat Amount', 'Turnover ex VAT']):
        turnover_numeric = pd.to_numeric(df['Turnover'], errors='coerce')
        vat_numeric = pd.to_numeric(df['Vat Amount'], errors='coerce')
        turnover_ex_vat_numeric = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
        
        calculated_turnover = turnover_ex_vat_numeric + vat_numeric
        tolerance = 0.02
        inconsistent_mask = (abs(turnover_numeric - calculated_turnover) > tolerance) & turnover_numeric.notna() & calculated_turnover.notna()
        
        if inconsistent_mask.any():
            inconsistent_indices = df[inconsistent_mask].index.tolist()[:3]
            errors.append(f"ERROR: Financial inconsistency detected: Turnover != Turnover ex VAT + Vat Amount at rows {inconsistent_indices}.")
    
    if all(col in df.columns for col in ['RRP', 'Trade Price']):
        rrp_numeric = pd.to_numeric(df['RRP'], errors='coerce')
        trade_price_numeric = pd.to_numeric(df['Trade Price'], errors='coerce')
        
        invalid_pricing = (rrp_numeric < trade_price_numeric) & rrp_numeric.notna() & trade_price_numeric.notna()
        if invalid_pricing.any():
            invalid_indices = df[invalid_pricing].index.tolist()[:3]
            errors.append(f"WARNING: RRP is less than Trade Price at rows {invalid_indices}.")
    
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
                
                outliers_mask = ((numeric_col < lower_bound) | (numeric_col > upper_bound)) & numeric_col.notna()
                if outliers_mask.any():
                    outlier_count = outliers_mask.sum()
                    outlier_indices = df[outliers_mask].index.tolist()[:3]
                    outlier_values = numeric_col[outliers_mask].tolist()[:3]
                    errors.append(f"WARNING: Column '{col}' has {outlier_count} potential outliers. Example values: {outlier_values} at rows {outlier_indices}.")
    
    return errors

def summarize_dataset(df: pd.DataFrame) -> List[str]:
    summary = []
    summary.append(f"INFO: Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns.")
    
    for col in df.columns:
        if col in EXPECTED_COLUMNS:
            if pd.api.types.is_numeric_dtype(df[col]) or df[col].dtype == 'object':
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                if numeric_col.notna().sum() > 0:
                    min_val = numeric_col.min()
                    max_val = numeric_col.max()
                    mean_val = numeric_col.mean()
                    summary.append(f"INFO: Column '{col}' (numeric) - min={min_val:.2f}, max={max_val:.2f}, mean={mean_val:.2f}.")
                else:
                    distinct_count = df[col].nunique()
                    summary.append(f"INFO: Column '{col}' (categorical) - {distinct_count} distinct values.")
            else:
                distinct_count = df[col].nunique()
                summary.append(f"INFO: Column '{col}' - {distinct_count} distinct values.")
    
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
    all_errors.extend(check_outliers(df))
    
    if all_errors:
        for error in all_errors:
            print(f"- {error}")
    else:
        print("No errors or warnings detected.")
    
    print("\n" + "=" * 50)
    print("DATASET SUMMARY")
    print("=" * 50)
    
    summary = summarize_dataset(df)
    for line in summary:
        print(f"- {line}")
    
    print("\n" + "=" * 50)
    print("END OF REPORT")
    print("=" * 50)

if __name__ == "__main__":
    main()
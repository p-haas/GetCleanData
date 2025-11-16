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
                    non_numeric_rows = df[non_numeric_mask].index.tolist()[:3]
                    errors.append(f"WARNING: Column '{col}' looks numeric but contains non-numeric values: {non_numeric_values} at rows {non_numeric_rows}.")
    
    return errors

def check_value_ranges(df: pd.DataFrame) -> List[str]:
    errors = []
    
    quantity_like_columns = ['Qty Sold', 'Refund Qty']
    for col in quantity_like_columns:
        if col in df.columns:
            try:
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                negative_mask = (numeric_col < 0) & numeric_col.notna()
                if negative_mask.any():
                    negative_values = numeric_col[negative_mask].tolist()[:5]
                    negative_rows = df[negative_mask].index.tolist()[:3]
                    errors.append(f"WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_rows}.")
            except:
                pass
    
    price_like_columns = ['Trade Price', 'RRP', 'Turnover', 'Turnover ex VAT', 'Profit']
    for col in price_like_columns:
        if col in df.columns:
            try:
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                negative_mask = (numeric_col < 0) & numeric_col.notna()
                if negative_mask.any():
                    negative_values = numeric_col[negative_mask].tolist()[:5]
                    negative_rows = df[negative_mask].index.tolist()[:3]
                    errors.append(f"WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_rows}.")
            except:
                pass
    
    vat_rate_col = 'Sale VAT Rate'
    if vat_rate_col in df.columns:
        try:
            numeric_col = pd.to_numeric(df[vat_rate_col], errors='coerce')
            invalid_mask = ((numeric_col < 0) | (numeric_col > 100)) & numeric_col.notna()
            if invalid_mask.any():
                invalid_values = numeric_col[invalid_mask].tolist()[:5]
                invalid_rows = df[invalid_mask].index.tolist()[:3]
                errors.append(f"ERROR: Column '{vat_rate_col}' has values outside [0, 100]. Values: {invalid_values} at rows {invalid_rows}.")
        except:
            pass
    
    return errors

def check_allowed_categories(df: pd.DataFrame) -> List[str]:
    errors = []
    categorical_columns = ['Branch Name', 'Dept Fullname', 'Group Fullname', 'OrderList']
    
    for col in categorical_columns:
        if col in df.columns:
            value_counts = df[col].value_counts()
            rare_categories = value_counts[value_counts == 1]
            if len(rare_categories) > 0:
                for category, count in rare_categories.head(3).items():
                    example_row = df[df[col] == category].index.tolist()[:1]
                    errors.append(f"WARNING: Column '{col}' has rare category '{category}' ({count} occurrence). Example row: {example_row}.")
    
    return errors

def check_unique_constraints(df: pd.DataFrame) -> List[str]:
    errors = []
    unique_columns = ['Sale ID', 'Barcode']
    
    for col in unique_columns:
        if col in df.columns:
            duplicated_values = df[df.duplicated(subset=[col], keep=False)][col]
            if len(duplicated_values) > 0:
                unique_duplicates = duplicated_values.unique()[:3]
                for dup_val in unique_duplicates:
                    dup_rows = df[df[col] == dup_val].index.tolist()[:5]
                    errors.append(f"ERROR: Column '{col}' contains duplicate value {dup_val} at rows {dup_rows}.")
    
    return errors

def check_id_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    identifier_columns = ['Headoffice ID', 'Barcode', 'Product']
    consistency_check_columns = {
        'Headoffice ID': ['Product', 'Packsize'],
        'Barcode': ['Product', 'Packsize', 'Headoffice ID'],
        'Product': ['Packsize', 'Dept Fullname', 'Group Fullname']
    }
    
    for id_col in identifier_columns:
        if id_col not in df.columns:
            continue
        
        check_cols = consistency_check_columns.get(id_col, [])
        check_cols = [c for c in check_cols if c in df.columns]
        
        if not check_cols:
            continue
        
        grouped = df.groupby(id_col)
        
        for check_col in check_cols:
            inconsistent_ids = []
            
            for id_val, group in grouped:
                if pd.isna(id_val):
                    continue
                
                unique_values = group[check_col].dropna().unique()
                
                if len(unique_values) > 1:
                    value_examples = []
                    for val in unique_values[:3]:
                        example_row = group[group[check_col] == val].index[0]
                        value_examples.append(f"'{val}' (row {example_row})")
                    
                    errors.append(f"ERROR: rows with {id_col} '{id_val}' have inconsistent '{check_col}' values: [{', '.join(value_examples)}].")
                    inconsistent_ids.append(id_val)
                    
                    if len(inconsistent_ids) >= 5:
                        break
            
            if len(inconsistent_ids) >= 5:
                break
    
    return errors

def check_date_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    date_col = 'Sale Date'
    
    if date_col in df.columns:
        try:
            date_series = pd.to_datetime(df[date_col], errors='coerce')
            invalid_dates_mask = date_series.isna() & df[date_col].notna()
            
            if invalid_dates_mask.any():
                invalid_rows = df[invalid_dates_mask].index.tolist()[:3]
                invalid_values = df.loc[invalid_dates_mask, date_col].tolist()[:3]
                errors.append(f"ERROR: Column '{date_col}' has invalid date values: {invalid_values} at rows {invalid_rows}.")
            
            valid_dates = date_series.dropna()
            if len(valid_dates) > 0:
                future_mask = date_series > pd.Timestamp.now()
                if future_mask.any():
                    future_rows = df[future_mask].index.tolist()[:3]
                    future_values = date_series[future_mask].tolist()[:3]
                    errors.append(f"WARNING: Column '{date_col}' has future dates: {future_values} at rows {future_rows}.")
                
                very_old_mask = date_series < pd.Timestamp('2000-01-01')
                if very_old_mask.any():
                    old_rows = df[very_old_mask].index.tolist()[:3]
                    old_values = date_series[very_old_mask].tolist()[:3]
                    errors.append(f"WARNING: Column '{date_col}' has very old dates (before 2000): {old_values} at rows {old_rows}.")
        except:
            pass
    
    return errors

def check_financial_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Turnover' in df.columns and 'Turnover ex VAT' in df.columns and 'Vat Amount' in df.columns:
        try:
            turnover = pd.to_numeric(df['Turnover'], errors='coerce')
            turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
            vat_amount = pd.to_numeric(df['Vat Amount'], errors='coerce')
            
            calculated_turnover = turnover_ex_vat + vat_amount
            diff = abs(turnover - calculated_turnover)
            
            inconsistent_mask = (diff > 0.02) & turnover.notna() & turnover_ex_vat.notna() & vat_amount.notna()
            
            if inconsistent_mask.any():
                inconsistent_rows = df[inconsistent_mask].index.tolist()[:3]
                errors.append(f"ERROR: Turnover != Turnover ex VAT + Vat Amount in {inconsistent_mask.sum()} rows. Example rows: {inconsistent_rows}.")
        except:
            pass
    
    if 'Trade Price' in df.columns and 'RRP' in df.columns:
        try:
            trade_price = pd.to_numeric(df['Trade Price'], errors='coerce')
            rrp = pd.to_numeric(df['RRP'], errors='coerce')
            
            invalid_mask = (trade_price > rrp) & trade_price.notna() & rrp.notna()
            
            if invalid_mask.any():
                invalid_rows = df[invalid_mask].index.tolist()[:3]
                errors.append(f"WARNING: Trade Price > RRP in {invalid_mask.sum()} rows. Example rows: {invalid_rows}.")
        except:
            pass
    
    return errors

def summarize_dataset(df: pd.DataFrame) -> List[str]:
    summary = []
    summary.append(f"INFO: Dataset shape - {df.shape[0]} rows x {df.shape[1]} columns.")
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        if col in EXPECTED_COLUMNS:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                min_val = col_data.min()
                max_val = col_data.max()
                mean_val = col_data.mean()
                summary.append(f"INFO: Column '{col}' (numeric) - min={min_val:.2f}, max={max_val:.2f}, mean={mean_val:.2f}.")
    
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
        print(f"ERROR: Failed to load dataset: {e}")
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
import sys
from typing import List
import pandas as pd
import numpy as np
import re

EXPECTED_COLUMNS = ['Unnamed: 0', 'Product', 'Packsize', 'Headoffice ID', 'Barcode', 'OrderList', 'Branch Name', 'Dept Fullname', 'Group Fullname', 'Trade Price', 'RRP', 'Sale Date', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate', 'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 'Refund Qty', 'Refund Value']

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
        num_duplicate_sets = df.duplicated().sum()
        errors.append(f"ERROR: There are {num_duplicate_sets} duplicate rows. Example rows: {example_rows}.")
    return errors

def check_basic_types(df: pd.DataFrame) -> List[str]:
    errors = []
    
    numeric_columns = ['Unnamed: 0', 'Headoffice ID', 'Barcode', 'Trade Price', 'RRP', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate', 'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 'Refund Qty', 'Refund Value']
    
    for col in numeric_columns:
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
    
    vat_rate_col = 'Sale VAT Rate'
    if vat_rate_col in df.columns:
        numeric_col = pd.to_numeric(df[vat_rate_col], errors='coerce')
        invalid_mask = ((numeric_col < 0) | (numeric_col > 100)) & numeric_col.notna()
        if invalid_mask.any():
            invalid_values = numeric_col[invalid_mask].tolist()[:5]
            invalid_indices = df[invalid_mask].index.tolist()[:3]
            errors.append(f"ERROR: Column '{vat_rate_col}' has values outside [0, 100]. Values: {invalid_values} at rows {invalid_indices}.")
    
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
                    example_row = df[df[col] == category].index.tolist()[0]
                    errors.append(f"WARNING: Column '{col}' has rare category '{category}' ({count} occurrence). Example row: [{example_row}].")
    
    return errors

def check_id_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    id_columns = ['Headoffice ID', 'Barcode', 'Product']
    consistency_columns = {
        'Headoffice ID': ['Product', 'Packsize'],
        'Barcode': ['Product', 'Packsize', 'Headoffice ID'],
        'Product': ['Packsize']
    }
    
    for id_col in id_columns:
        if id_col not in df.columns:
            continue
        
        check_cols = consistency_columns.get(id_col, [])
        check_cols = [c for c in check_cols if c in df.columns]
        
        for check_col in check_cols:
            grouped = df.groupby(id_col)[check_col].apply(lambda x: x.dropna().unique())
            inconsistent = grouped[grouped.apply(len) > 1]
            
            if len(inconsistent) > 0:
                for id_value, values in inconsistent.head(3).items():
                    rows_with_id = df[df[id_col] == id_value]
                    examples = []
                    for val in values[:3]:
                        row_idx = rows_with_id[rows_with_id[check_col] == val].index[0]
                        examples.append(f"{val} (row {row_idx})")
                    errors.append(f"ERROR: rows with {id_col} '{id_value}' have inconsistent '{check_col}' values: [{', '.join(examples)}].")
    
    return errors

def check_product_whitespace(df: pd.DataFrame) -> List[str]:
    errors = []
    
    text_columns = ['Product', 'Packsize', 'OrderList', 'Branch Name', 'Dept Fullname', 'Group Fullname']
    
    for col in text_columns:
        if col not in df.columns:
            continue
        
        string_mask = df[col].notna() & (df[col].astype(str) != '')
        
        leading_space_mask = string_mask & df[col].astype(str).str.match(r'^\s+')
        if leading_space_mask.any():
            for idx in df[leading_space_mask].head(3).index:
                value = df.loc[idx, col]
                errors.append(f"WARNING: Column '{col}' contains leading spaces: '{value}' at row {idx}.")
        
        trailing_space_mask = string_mask & df[col].astype(str).str.match(r'.*\s+$')
        if trailing_space_mask.any():
            for idx in df[trailing_space_mask].head(3).index:
                value = df.loc[idx, col]
                errors.append(f"WARNING: Column '{col}' contains trailing spaces: '{value}' at row {idx}.")
        
        multiple_space_mask = string_mask & df[col].astype(str).str.contains(r'\s{2,}', regex=True)
        if multiple_space_mask.any():
            for idx in df[multiple_space_mask].head(3).index:
                value = df.loc[idx, col]
                errors.append(f"WARNING: Column '{col}' contains multiple internal spaces: '{value}' at row {idx}.")
    
    return errors

def check_date_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    date_col = 'Sale Date'
    if date_col in df.columns:
        try:
            date_series = pd.to_datetime(df[date_col], errors='coerce')
            invalid_mask = date_series.isna() & df[date_col].notna()
            if invalid_mask.any():
                invalid_values = df.loc[invalid_mask, date_col].tolist()[:5]
                invalid_indices = df[invalid_mask].index.tolist()[:3]
                errors.append(f"ERROR: Column '{date_col}' has invalid date values: {invalid_values} at rows {invalid_indices}.")
            
            future_mask = date_series > pd.Timestamp.now()
            if future_mask.any():
                future_values = date_series[future_mask].tolist()[:5]
                future_indices = df[future_mask].index.tolist()[:3]
                errors.append(f"WARNING: Column '{date_col}' has future dates: {future_values} at rows {future_indices}.")
        except Exception as e:
            errors.append(f"ERROR: Could not parse '{date_col}' as dates: {str(e)}")
    
    return errors

def check_financial_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Turnover' in df.columns and 'Vat Amount' in df.columns and 'Turnover ex VAT' in df.columns:
        turnover = pd.to_numeric(df['Turnover'], errors='coerce')
        vat_amount = pd.to_numeric(df['Vat Amount'], errors='coerce')
        turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
        
        calculated_turnover = turnover_ex_vat + vat_amount
        diff = abs(turnover - calculated_turnover)
        inconsistent_mask = (diff > 0.02) & turnover.notna() & vat_amount.notna() & turnover_ex_vat.notna()
        
        if inconsistent_mask.any():
            inconsistent_indices = df[inconsistent_mask].index.tolist()[:3]
            errors.append(f"WARNING: Turnover calculation inconsistency detected (Turnover != Turnover ex VAT + Vat Amount). Example rows: {inconsistent_indices}.")
    
    if 'Turnover ex VAT' in df.columns and 'Trade Price' in df.columns and 'Qty Sold' in df.columns and 'Profit' in df.columns:
        turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
        trade_price = pd.to_numeric(df['Trade Price'], errors='coerce')
        qty_sold = pd.to_numeric(df['Qty Sold'], errors='coerce')
        profit = pd.to_numeric(df['Profit'], errors='coerce')
        
        calculated_profit = turnover_ex_vat - (trade_price * qty_sold)
        diff = abs(profit - calculated_profit)
        inconsistent_mask = (diff > 0.02) & profit.notna() & turnover_ex_vat.notna() & trade_price.notna() & qty_sold.notna()
        
        if inconsistent_mask.any():
            inconsistent_indices = df[inconsistent_mask].index.tolist()[:3]
            errors.append(f"WARNING: Profit calculation inconsistency detected. Example rows: {inconsistent_indices}.")
    
    return errors

def check_price_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Trade Price' in df.columns and 'RRP' in df.columns:
        trade_price = pd.to_numeric(df['Trade Price'], errors='coerce')
        rrp = pd.to_numeric(df['RRP'], errors='coerce')
        
        invalid_mask = (trade_price > rrp) & trade_price.notna() & rrp.notna()
        if invalid_mask.any():
            invalid_indices = df[invalid_mask].index.tolist()[:3]
            errors.append(f"WARNING: Trade Price exceeds RRP in some rows. Example rows: {invalid_indices}.")
    
    return errors

def summarize_dataset(df: pd.DataFrame) -> List[str]:
    summary = []
    summary.append(f"INFO: Dataset shape - {df.shape[0]} rows x {df.shape[1]} columns.")
    
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
    print()
    
    all_errors = []
    
    all_errors.extend(check_columns(df))
    all_errors.extend(check_missing_values(df))
    all_errors.extend(check_duplicates(df))
    all_errors.extend(check_basic_types(df))
    all_errors.extend(check_value_ranges(df))
    all_errors.extend(check_allowed_categories(df))
    all_errors.extend(check_id_consistency(df))
    all_errors.extend(check_product_whitespace(df))
    all_errors.extend(check_date_consistency(df))
    all_errors.extend(check_financial_consistency(df))
    all_errors.extend(check_price_consistency(df))
    
    if all_errors:
        print("ERRORS AND WARNINGS:")
        print("-" * 50)
        for error in all_errors:
            print(f"  - {error}")
        print()
    else:
        print("No errors or warnings detected.")
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
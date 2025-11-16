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
        errors.append(f"ERROR: Missing columns: {sorted(missing)}")
    
    extra = actual_columns - expected_columns
    if extra:
        errors.append(f"WARNING: Extra columns found: {sorted(extra)}")
    
    return errors

def check_missing_values(df: pd.DataFrame) -> List[str]:
    errors = []
    for col in EXPECTED_COLUMNS:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                errors.append(f"WARNING: Column '{col}' has {missing_count} missing values.")
    return errors

def check_duplicates(df: pd.DataFrame) -> List[str]:
    errors = []
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        errors.append(f"WARNING: There are {duplicate_count} duplicate rows.")
    return errors

def check_basic_types(df: pd.DataFrame) -> List[str]:
    errors = []
    numeric_columns = ['Headoffice ID', 'Barcode', 'Trade Price', 'RRP', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate', 'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 'Refund Qty', 'Refund Value']
    
    for col in numeric_columns:
        if col in df.columns:
            if df[col].dtype == 'object':
                non_numeric = []
                for val in df[col].dropna().unique():
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        non_numeric.append(str(val))
                        if len(non_numeric) >= 5:
                            break
                if non_numeric:
                    errors.append(f"WARNING: Column '{col}' looks numeric but contains non-numeric values: {non_numeric}")
    
    return errors

def check_value_ranges(df: pd.DataFrame) -> List[str]:
    errors = []
    
    numeric_positive_columns = ['Trade Price', 'RRP', 'Qty Sold', 'Turnover', 'Vat Amount', 'Turnover ex VAT', 'Profit']
    
    for col in numeric_positive_columns:
        if col in df.columns:
            try:
                numeric_vals = pd.to_numeric(df[col], errors='coerce')
                negative_vals = numeric_vals[numeric_vals < 0].dropna()
                if len(negative_vals) > 0:
                    examples = negative_vals.head(3).tolist()
                    errors.append(f"WARNING: Column '{col}' has {len(negative_vals)} negative values. Examples: {examples}")
            except:
                pass
    
    if 'Sale VAT Rate' in df.columns:
        try:
            vat_vals = pd.to_numeric(df['Sale VAT Rate'], errors='coerce')
            invalid_vat = vat_vals[(vat_vals < 0) | (vat_vals > 100)].dropna()
            if len(invalid_vat) > 0:
                examples = invalid_vat.head(3).tolist()
                errors.append(f"WARNING: Column 'Sale VAT Rate' has values outside [0, 100]. Examples: {examples}")
        except:
            pass
    
    if 'Refund Qty' in df.columns:
        try:
            refund_qty = pd.to_numeric(df['Refund Qty'], errors='coerce')
            negative_refunds = refund_qty[refund_qty < 0].dropna()
            if len(negative_refunds) > 0:
                examples = negative_refunds.head(3).tolist()
                errors.append(f"WARNING: Column 'Refund Qty' has {len(negative_refunds)} negative values. Examples: {examples}")
        except:
            pass
    
    return errors

def check_allowed_categories(df: pd.DataFrame) -> List[str]:
    errors = []
    categorical_columns = ['Branch Name', 'Dept Fullname', 'Group Fullname', 'OrderList']
    
    for col in categorical_columns:
        if col in df.columns:
            value_counts = df[col].value_counts()
            total_count = len(df[col].dropna())
            if total_count > 0:
                rare_categories = value_counts[value_counts <= max(1, total_count * 0.001)]
                if len(rare_categories) > 0 and len(rare_categories) <= 10:
                    for cat, count in rare_categories.items():
                        errors.append(f"WARNING: Column '{col}' has rare category '{cat}' ({count} occurrence(s)).")
    
    return errors

def check_unique_constraints(df: pd.DataFrame) -> List[str]:
    errors = []
    id_columns = ['Sale ID', 'Barcode', 'Headoffice ID']
    
    for col in id_columns:
        if col in df.columns:
            duplicates = df[col].dropna()[df[col].dropna().duplicated()]
            if len(duplicates) > 0:
                unique_dupes = duplicates.unique()[:3].tolist()
                errors.append(f"WARNING: Column '{col}' contains {len(duplicates)} duplicate values. Example duplicates: {unique_dupes}")
    
    return errors

def check_id_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Barcode' in df.columns:
        barcode_groups = df.groupby('Barcode')
        
        for attr in ['Product', 'Packsize', 'Trade Price', 'RRP', 'Headoffice ID']:
            if attr in df.columns:
                inconsistent_barcodes = []
                for barcode, group in barcode_groups:
                    if pd.isna(barcode):
                        continue
                    unique_vals = group[attr].dropna().unique()
                    if len(unique_vals) > 1:
                        inconsistent_barcodes.append((barcode, unique_vals[:5].tolist()))
                        if len(inconsistent_barcodes) >= 5:
                            break
                
                if inconsistent_barcodes:
                    for barcode, vals in inconsistent_barcodes[:3]:
                        errors.append(f"ERROR: Inconsistent data for Barcode '{barcode}': multiple values for '{attr}' found {vals}.")
    
    if 'Headoffice ID' in df.columns:
        hoid_groups = df.groupby('Headoffice ID')
        
        for attr in ['Product', 'Packsize']:
            if attr in df.columns:
                inconsistent_ids = []
                for hoid, group in hoid_groups:
                    if pd.isna(hoid):
                        continue
                    unique_vals = group[attr].dropna().unique()
                    if len(unique_vals) > 1:
                        inconsistent_ids.append((hoid, unique_vals[:5].tolist()))
                        if len(inconsistent_ids) >= 5:
                            break
                
                if inconsistent_ids:
                    for hoid, vals in inconsistent_ids[:3]:
                        errors.append(f"ERROR: Inconsistent data for Headoffice ID '{hoid}': multiple values for '{attr}' found {vals}.")
    
    return errors

def check_date_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Sale Date' in df.columns:
        try:
            dates = pd.to_datetime(df['Sale Date'], errors='coerce')
            invalid_dates = df['Sale Date'][dates.isna() & df['Sale Date'].notna()]
            if len(invalid_dates) > 0:
                examples = invalid_dates.head(3).tolist()
                errors.append(f"ERROR: Column 'Sale Date' has {len(invalid_dates)} invalid date values. Examples: {examples}")
            
            valid_dates = dates.dropna()
            if len(valid_dates) > 0:
                min_date = valid_dates.min()
                max_date = valid_dates.max()
                current_year = pd.Timestamp.now().year
                if min_date.year < 1900:
                    errors.append(f"WARNING: Column 'Sale Date' has dates before 1900. Earliest: {min_date}")
                if max_date.year > current_year + 1:
                    errors.append(f"WARNING: Column 'Sale Date' has future dates beyond next year. Latest: {max_date}")
        except:
            errors.append(f"ERROR: Column 'Sale Date' could not be parsed as dates.")
    
    return errors

def check_business_rules(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Trade Price' in df.columns and 'RRP' in df.columns:
        try:
            trade_price = pd.to_numeric(df['Trade Price'], errors='coerce')
            rrp = pd.to_numeric(df['RRP'], errors='coerce')
            invalid_pricing = df[(trade_price > rrp) & trade_price.notna() & rrp.notna()]
            if len(invalid_pricing) > 0:
                errors.append(f"WARNING: {len(invalid_pricing)} rows have Trade Price > RRP (unusual pricing).")
        except:
            pass
    
    if 'Turnover' in df.columns and 'Turnover ex VAT' in df.columns:
        try:
            turnover = pd.to_numeric(df['Turnover'], errors='coerce')
            turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
            invalid_turnover = df[(turnover < turnover_ex_vat) & turnover.notna() & turnover_ex_vat.notna()]
            if len(invalid_turnover) > 0:
                errors.append(f"ERROR: {len(invalid_turnover)} rows have Turnover < Turnover ex VAT (impossible).")
        except:
            pass
    
    if 'Qty Sold' in df.columns and 'Turnover' in df.columns:
        try:
            qty_sold = pd.to_numeric(df['Qty Sold'], errors='coerce')
            turnover = pd.to_numeric(df['Turnover'], errors='coerce')
            zero_qty_nonzero_turnover = df[(qty_sold == 0) & (turnover != 0) & qty_sold.notna() & turnover.notna()]
            if len(zero_qty_nonzero_turnover) > 0:
                errors.append(f"WARNING: {len(zero_qty_nonzero_turnover)} rows have Qty Sold = 0 but Turnover != 0.")
        except:
            pass
    
    if 'Profit' in df.columns and 'Turnover ex VAT' in df.columns and 'Trade Price' in df.columns:
        try:
            profit = pd.to_numeric(df['Profit'], errors='coerce')
            turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
            extreme_profit = df[(profit > turnover_ex_vat) & profit.notna() & turnover_ex_vat.notna()]
            if len(extreme_profit) > 0:
                errors.append(f"WARNING: {len(extreme_profit)} rows have Profit > Turnover ex VAT (unusual).")
        except:
            pass
    
    return errors

def check_outliers(df: pd.DataFrame) -> List[str]:
    errors = []
    numeric_columns = ['Trade Price', 'RRP', 'Qty Sold', 'Turnover', 'Profit']
    
    for col in numeric_columns:
        if col in df.columns:
            try:
                numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(numeric_vals) > 10:
                    q1 = numeric_vals.quantile(0.25)
                    q3 = numeric_vals.quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 3 * iqr
                    upper_bound = q3 + 3 * iqr
                    outliers = numeric_vals[(numeric_vals < lower_bound) | (numeric_vals > upper_bound)]
                    if len(outliers) > 0:
                        outlier_pct = (len(outliers) / len(numeric_vals)) * 100
                        if outlier_pct > 5:
                            errors.append(f"WARNING: Column '{col}' has {len(outliers)} extreme outliers ({outlier_pct:.1f}% of data).")
            except:
                pass
    
    return errors

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
    all_errors.extend(check_business_rules(df))
    all_errors.extend(check_outliers(df))
    
    if all_errors:
        for error in all_errors:
            print(f"- {error}")
    else:
        print("No errors or warnings detected.")
    
    print()
    print("=" * 50)
    print(f"Total issues found: {len(all_errors)}")

if __name__ == "__main__":
    main()
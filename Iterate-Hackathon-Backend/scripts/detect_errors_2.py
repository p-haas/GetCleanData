import sys
from typing import List, Tuple, Dict, Any
import pandas as pd
import numpy as np
from collections import Counter

EXPECTED_COLUMNS = [
    'Product', 'Packsize', 'Headoffice ID', 'Barcode', 'OrderList', 
    'Branch Name', 'Dept Fullname', 'Group Fullname', 'Trade Price', 
    'RRP', 'Sale Date', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 
    'Sale VAT Rate', 'Turnover ex VAT', 'Disc Amount', 'Discount Band', 
    'Profit', 'Refund Qty', 'Refund Value'
]

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
        errors.append(f"ERROR: Missing columns: {sorted(list(missing))}")
    
    extra = actual_columns - expected_columns
    if extra:
        errors.append(f"WARNING: Extra columns not in specification: {sorted(list(extra))}")
    
    return errors

def check_missing_values(df: pd.DataFrame) -> List[str]:
    errors = []
    for col in EXPECTED_COLUMNS:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                pct = (missing_count / len(df)) * 100
                errors.append(f"WARNING: Column '{col}' has {missing_count} missing values ({pct:.2f}%)")
    return errors

def check_duplicates(df: pd.DataFrame) -> List[str]:
    errors = []
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        pct = (dup_count / len(df)) * 100
        errors.append(f"WARNING: Found {dup_count} duplicate rows ({pct:.2f}%)")
    return errors

def check_basic_types(df: pd.DataFrame) -> List[str]:
    errors = []
    numeric_cols = ['Headoffice ID', 'Barcode', 'Trade Price', 'RRP', 'Sale ID', 
                    'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate', 
                    'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 
                    'Refund Qty', 'Refund Value']
    
    for col in numeric_cols:
        if col in df.columns:
            if df[col].dtype == 'object':
                non_numeric = df[col].dropna()
                non_numeric_vals = []
                for val in non_numeric:
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        non_numeric_vals.append(val)
                
                if non_numeric_vals:
                    sample = list(set(non_numeric_vals))[:5]
                    errors.append(f"WARNING: Column '{col}' should be numeric but contains non-numeric values: {sample}")
    
    return errors

def check_value_ranges(df: pd.DataFrame) -> List[str]:
    errors = []
    
    numeric_cols = {
        'Trade Price': (0, None),
        'RRP': (0, None),
        'Qty Sold': (0, None),
        'Turnover': (0, None),
        'Vat Amount': (0, None),
        'Sale VAT Rate': (0, 100),
        'Turnover ex VAT': (0, None),
        'Disc Amount': (0, None),
        'Profit': (None, None),
        'Refund Qty': (0, None),
        'Refund Value': (0, None)
    }
    
    for col, (min_val, max_val) in numeric_cols.items():
        if col in df.columns:
            try:
                numeric_data = pd.to_numeric(df[col], errors='coerce')
                
                if min_val is not None:
                    below_min = numeric_data[numeric_data < min_val].dropna()
                    if len(below_min) > 0:
                        examples = below_min.head(3).tolist()
                        errors.append(f"ERROR: Column '{col}' has values below {min_val}. Examples: {examples}")
                
                if max_val is not None:
                    above_max = numeric_data[numeric_data > max_val].dropna()
                    if len(above_max) > 0:
                        examples = above_max.head(3).tolist()
                        errors.append(f"ERROR: Column '{col}' has values above {max_val}. Examples: {examples}")
            except Exception:
                pass
    
    return errors

def check_allowed_categories(df: pd.DataFrame) -> List[str]:
    errors = []
    categorical_cols = ['Branch Name', 'Dept Fullname', 'Group Fullname', 'OrderList']
    
    for col in categorical_cols:
        if col in df.columns:
            value_counts = df[col].value_counts()
            total = len(df[col].dropna())
            
            if total > 0:
                for category, count in value_counts.items():
                    pct = (count / total) * 100
                    if pct < 0.1 and count < 3:
                        errors.append(f"WARNING: Column '{col}' has rare category '{category}' ({count} occurrence(s), {pct:.3f}%)")
    
    return errors

def check_unique_constraints(df: pd.DataFrame) -> List[str]:
    errors = []
    unique_cols = ['Sale ID', 'Barcode']
    
    for col in unique_cols:
        if col in df.columns:
            dup_mask = df[col].duplicated(keep=False)
            if dup_mask.any():
                dup_values = df.loc[dup_mask, col].value_counts()
                examples = dup_values.head(3).index.tolist()
                total_dups = dup_mask.sum()
                
                if col == 'Sale ID':
                    errors.append(f"ERROR: Column '{col}' contains {total_dups} duplicate values. This should be unique. Examples: {examples}")
                else:
                    errors.append(f"INFO: Column '{col}' contains {total_dups} duplicate values. Examples: {examples}")
    
    return errors

def check_barcode_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Barcode' in df.columns and 'Product' in df.columns:
        barcode_product = df.groupby('Barcode')['Product'].nunique()
        inconsistent = barcode_product[barcode_product > 1]
        
        if len(inconsistent) > 0:
            for barcode in inconsistent.head(5).index:
                products = df[df['Barcode'] == barcode]['Product'].unique().tolist()
                errors.append(f"ERROR: Barcode '{barcode}' is associated with multiple products: {products}")
    
    if 'Barcode' in df.columns and 'Trade Price' in df.columns:
        try:
            barcode_price = df.groupby('Barcode')['Trade Price'].nunique()
            inconsistent_price = barcode_price[barcode_price > 1]
            
            if len(inconsistent_price) > 0:
                for barcode in inconsistent_price.head(5).index:
                    prices = df[df['Barcode'] == barcode]['Trade Price'].unique().tolist()
                    errors.append(f"WARNING: Barcode '{barcode}' has multiple Trade Prices: {prices}")
        except Exception:
            pass
    
    if 'Barcode' in df.columns and 'RRP' in df.columns:
        try:
            barcode_rrp = df.groupby('Barcode')['RRP'].nunique()
            inconsistent_rrp = barcode_rrp[barcode_rrp > 1]
            
            if len(inconsistent_rrp) > 0:
                for barcode in inconsistent_rrp.head(5).index:
                    rrps = df[df['Barcode'] == barcode]['RRP'].unique().tolist()
                    errors.append(f"WARNING: Barcode '{barcode}' has multiple RRP values: {rrps}")
        except Exception:
            pass
    
    return errors

def check_date_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Sale Date' in df.columns:
        try:
            dates = pd.to_datetime(df['Sale Date'], errors='coerce')
            invalid_dates = dates.isna().sum() - df['Sale Date'].isna().sum()
            
            if invalid_dates > 0:
                errors.append(f"ERROR: Column 'Sale Date' has {invalid_dates} invalid date formats")
            
            valid_dates = dates.dropna()
            if len(valid_dates) > 0:
                min_date = valid_dates.min()
                max_date = valid_dates.max()
                
                current_year = pd.Timestamp.now().year
                if min_date.year < 1900:
                    errors.append(f"WARNING: 'Sale Date' has suspiciously old dates. Minimum: {min_date}")
                
                if max_date.year > current_year + 1:
                    errors.append(f"WARNING: 'Sale Date' has future dates beyond reasonable range. Maximum: {max_date}")
        except Exception as e:
            errors.append(f"ERROR: Could not parse 'Sale Date' column: {str(e)}")
    
    return errors

def check_business_rules(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Trade Price' in df.columns and 'RRP' in df.columns:
        try:
            trade_price = pd.to_numeric(df['Trade Price'], errors='coerce')
            rrp = pd.to_numeric(df['RRP'], errors='coerce')
            
            invalid = (trade_price > rrp) & trade_price.notna() & rrp.notna()
            if invalid.any():
                count = invalid.sum()
                errors.append(f"ERROR: {count} rows where Trade Price > RRP (retail price)")
        except Exception:
            pass
    
    if 'Turnover' in df.columns and 'Turnover ex VAT' in df.columns and 'Vat Amount' in df.columns:
        try:
            turnover = pd.to_numeric(df['Turnover'], errors='coerce')
            turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
            vat_amount = pd.to_numeric(df['Vat Amount'], errors='coerce')
            
            calculated = turnover_ex_vat + vat_amount
            diff = abs(turnover - calculated)
            
            inconsistent = (diff > 0.02) & turnover.notna() & calculated.notna()
            if inconsistent.any():
                count = inconsistent.sum()
                errors.append(f"WARNING: {count} rows where Turnover != Turnover ex VAT + Vat Amount (tolerance: 0.02)")
        except Exception:
            pass
    
    if 'Qty Sold' in df.columns and 'Turnover' in df.columns:
        try:
            qty = pd.to_numeric(df['Qty Sold'], errors='coerce')
            turnover = pd.to_numeric(df['Turnover'], errors='coerce')
            
            zero_qty_nonzero_turnover = (qty == 0) & (turnover != 0) & qty.notna() & turnover.notna()
            if zero_qty_nonzero_turnover.any():
                count = zero_qty_nonzero_turnover.sum()
                errors.append(f"WARNING: {count} rows with Qty Sold = 0 but Turnover != 0")
        except Exception:
            pass
    
    if 'Profit' in df.columns and 'Turnover ex VAT' in df.columns and 'Trade Price' in df.columns and 'Qty Sold' in df.columns:
        try:
            profit = pd.to_numeric(df['Profit'], errors='coerce')
            turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
            trade_price = pd.to_numeric(df['Trade Price'], errors='coerce')
            qty_sold = pd.to_numeric(df['Qty Sold'], errors='coerce')
            
            expected_profit = turnover_ex_vat - (trade_price * qty_sold)
            diff = abs(profit - expected_profit)
            
            inconsistent = (diff > 0.02) & profit.notna() & expected_profit.notna()
            if inconsistent.any():
                count = inconsistent.sum()
                errors.append(f"WARNING: {count} rows where Profit calculation seems inconsistent (tolerance: 0.02)")
        except Exception:
            pass
    
    return errors

def check_outliers(df: pd.DataFrame) -> List[str]:
    errors = []
    numeric_cols = ['Trade Price', 'RRP', 'Qty Sold', 'Turnover', 'Profit']
    
    for col in numeric_cols:
        if col in df.columns:
            try:
                data = pd.to_numeric(df[col], errors='coerce').dropna()
                
                if len(data) > 0:
                    q1 = data.quantile(0.25)
                    q3 = data.quantile(0.75)
                    iqr = q3 - q1
                    
                    lower_bound = q1 - 3 * iqr
                    upper_bound = q3 + 3 * iqr
                    
                    outliers = data[(data < lower_bound) | (data > upper_bound)]
                    
                    if len(outliers) > 0:
                        pct = (len(outliers) / len(data)) * 100
                        if pct > 1:
                            errors.append(f"INFO: Column '{col}' has {len(outliers)} potential outliers ({pct:.2f}%). Range: [{data.min()}, {data.max()}]")
            except Exception:
                pass
    
    return errors

def summarize_dataset(df: pd.DataFrame) -> List[str]:
    info = []
    info.append(f"INFO: Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in EXPECTED_COLUMNS:
            data = df[col].dropna()
            if len(data) > 0:
                info.append(f"INFO: Column '{col}' (numeric) - min={data.min():.2f}, max={data.max():.2f}, mean={data.mean():.2f}, median={data.median():.2f}")
    
    categorical_cols = ['Product', 'Branch Name', 'Dept Fullname', 'Group Fullname', 'OrderList']
    for col in categorical_cols:
        if col in df.columns:
            distinct = df[col].nunique()
            info.append(f"INFO: Column '{col}' (categorical) - {distinct} distinct values")
    
    return info

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
    
    print("=" * 80)
    print("DATASET ERROR REPORT")
    print("=" * 80)
    print()
    
    all_errors = []
    
    all_errors.extend(summarize_dataset(df))
    print("\n--- DATASET SUMMARY ---")
    for msg in summarize_dataset(df):
        print(msg)
    
    print("\n--- COLUMN STRUCTURE CHECKS ---")
    col_errors = check_columns(df)
    all_errors.extend(col_errors)
    if col_errors:
        for msg in col_errors:
            print(msg)
    else:
        print("OK: All expected columns present, no extra columns")
    
    print("\n--- MISSING VALUES CHECKS ---")
    missing_errors = check_missing_values(df)
    all_errors.extend(missing_errors)
    if missing_errors:
        for msg in missing_errors:
            print(msg)
    else:
        print("OK: No missing values detected")
    
    print("\n--- DUPLICATE ROWS CHECKS ---")
    dup_errors = check_duplicates(df)
    all_errors.extend(dup_errors)
    if dup_errors:
        for msg in dup_errors:
            print(msg)
    else:
        print("OK: No duplicate rows detected")
    
    print("\n--- DATA TYPE CHECKS ---")
    type_errors = check_basic_types(df)
    all_errors.extend(type_errors)
    if type_errors:
        for msg in type_errors:
            print(msg)
    else:
        print("OK: All columns have appropriate data types")
    
    print("\n--- VALUE RANGE CHECKS ---")
    range_errors = check_value_ranges(df)
    all_errors.extend(range_errors)
    if range_errors:
        for msg in range_errors:
            print(msg)
    else:
        print("OK: All numeric values within expected ranges")
    
    print("\n--- CATEGORICAL VALUE CHECKS ---")
    cat_errors = check_allowed_categories(df)
    all_errors.extend(cat_errors)
    if cat_errors:
        for msg in cat_errors:
            print(msg)
    else:
        print("OK: No rare or suspicious categories detected")
    
    print("\n--- UNIQUE CONSTRAINT CHECKS ---")
    unique_errors = check_unique_constraints(df)
    all_errors.extend(unique_errors)
    if unique_errors:
        for msg in unique_errors:
            print(msg)
    else:
        print("OK: Unique constraints satisfied")
    
    print("\n--- BARCODE CONSISTENCY CHECKS ---")
    barcode_errors = check_barcode_consistency(df)
    all_errors.extend(barcode_errors)
    if barcode_errors:
        for msg in barcode_errors:
            print(msg)
    else:
        print("OK: Barcode consistency verified")
    
    print("\n--- DATE CONSISTENCY CHECKS ---")
    date_errors = check_date_consistency(df)
    all_errors.extend(date_errors)
    if date_errors:
        for msg in date_errors:
            print(msg)
    else:
        print("OK: Date values are consistent")
    
    print("\n--- BUSINESS RULES CHECKS ---")
    business_errors = check_business_rules(df)
    all_errors.extend(business_errors)
    if business_errors:
        for msg in business_errors:
            print(msg)
    else:
        print("OK: Business rules validated")
    
    print("\n--- OUTLIER DETECTION ---")
    outlier_errors = check_outliers(df)
    all_errors.extend(outlier_errors)
    if outlier_errors:
        for msg in outlier_errors:
            print(msg)
    else:
        print("OK: No significant outliers detected")
    
    print("\n" + "=" * 80)
    error_count = sum(1 for msg in all_errors if msg.startswith("ERROR"))
    warning_count = sum(1 for msg in all_errors if msg.startswith("WARNING"))
    print(f"SUMMARY: {error_count} errors, {warning_count} warnings detected")
    print("=" * 80)

if __name__ == "__main__":
    main()
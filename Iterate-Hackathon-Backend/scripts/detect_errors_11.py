import sys
from typing import List
import pandas as pd
import numpy as np
from datetime import timedelta

EXPECTED_COLUMNS = ['Unnamed: 0', 'Product', 'Packsize', 'Headoffice ID', 'Barcode', 'OrderList', 'Branch Name', 'Dept Fullname', 'Group Fullname', 'Trade Price', 'RRP', 'Sale Date', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate', 'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 'Refund Qty', 'Refund Value']

def load_dataset(file_path: str) -> pd.DataFrame:
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path, delimiter=',')
    return df

def check_missing_values(df: pd.DataFrame) -> List[str]:
    errors = []
    for col in EXPECTED_COLUMNS:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                missing_indices = df[df[col].isna()].index.tolist()
                example_rows = missing_indices[:5]
                errors.append(f"[MISSING_VALUES] ERROR: Column '{col}' has {missing_count} missing values. Example rows: {example_rows}.")
    return errors

def check_duplicates(df: pd.DataFrame) -> List[str]:
    errors = []
    duplicated_mask = df.duplicated(keep=False)
    duplicate_count = duplicated_mask.sum()
    if duplicate_count > 0:
        duplicate_indices = df[duplicated_mask].index.tolist()
        example_rows = duplicate_indices[:5]
        errors.append(f"[DUPLICATE_ROWS] ERROR: There are {duplicate_count} duplicate rows. Example rows: {example_rows}.")
    return errors

def check_basic_types(df: pd.DataFrame) -> List[str]:
    warnings = []
    numeric_like_columns = ['Headoffice ID', 'Barcode', 'Trade Price', 'RRP', 'Sale ID', 'Qty Sold', 'Turnover', 'Vat Amount', 'Sale VAT Rate', 'Turnover ex VAT', 'Disc Amount', 'Discount Band', 'Profit', 'Refund Qty', 'Refund Value']
    
    for col in numeric_like_columns:
        if col in df.columns:
            if df[col].dtype == 'object':
                non_numeric_mask = pd.to_numeric(df[col], errors='coerce').isna() & df[col].notna()
                if non_numeric_mask.any():
                    non_numeric_values = df.loc[non_numeric_mask, col].unique().tolist()[:5]
                    non_numeric_rows = df[non_numeric_mask].index.tolist()[:5]
                    warnings.append(f"[TYPE_INCONSISTENCY] WARNING: Column '{col}' looks numeric but contains non-numeric values: {non_numeric_values} at rows {non_numeric_rows}.")
    return warnings

def check_value_ranges(df: pd.DataFrame) -> List[str]:
    errors = []
    
    quantity_like_columns = ['Qty Sold', 'Refund Qty']
    for col in quantity_like_columns:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            negative_mask = (numeric_col < 0) & numeric_col.notna()
            if negative_mask.any():
                negative_values = numeric_col[negative_mask].tolist()[:5]
                negative_rows = df[negative_mask].index.tolist()[:5]
                errors.append(f"[NEGATIVE_QUANTITY] WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_rows}.")
    
    price_like_columns = ['Trade Price', 'RRP', 'Turnover', 'Turnover ex VAT', 'Profit']
    for col in price_like_columns:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            negative_mask = (numeric_col < 0) & numeric_col.notna()
            if negative_mask.any():
                negative_values = numeric_col[negative_mask].tolist()[:5]
                negative_rows = df[negative_mask].index.tolist()[:5]
                errors.append(f"[NEGATIVE_VALUE] WARNING: Column '{col}' has negative values. Values: {negative_values} at rows {negative_rows}.")
    
    if 'Sale VAT Rate' in df.columns:
        vat_col = pd.to_numeric(df['Sale VAT Rate'], errors='coerce')
        invalid_vat_mask = ((vat_col < 0) | (vat_col > 100)) & vat_col.notna()
        if invalid_vat_mask.any():
            invalid_values = vat_col[invalid_vat_mask].tolist()[:5]
            invalid_rows = df[invalid_vat_mask].index.tolist()[:5]
            errors.append(f"[VALUE_RANGE] ERROR: Column 'Sale VAT Rate' has values outside [0, 100]. Values: {invalid_values} at rows {invalid_rows}.")
    
    return errors

def check_allowed_categories(df: pd.DataFrame) -> List[str]:
    warnings = []
    categorical_columns = ['OrderList', 'Branch Name', 'Dept Fullname', 'Group Fullname']
    
    for col in categorical_columns:
        if col in df.columns:
            value_counts = df[col].value_counts()
            rare_categories = value_counts[value_counts == 1]
            if len(rare_categories) > 0:
                for category in rare_categories.index[:5]:
                    example_row = df[df[col] == category].index.tolist()[0]
                    warnings.append(f"[RARE_CATEGORY] WARNING: Column '{col}' has rare category '{category}' (1 occurrence). Example row: [{example_row}].")
    
    return warnings

def check_id_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Product' in df.columns:
        product_groups = df.groupby('Product')
        
        consistency_columns = ['Packsize', 'Headoffice ID', 'Barcode', 'OrderList', 'Trade Price', 'RRP']
        
        for col in consistency_columns:
            if col in df.columns:
                for product, group in product_groups:
                    unique_values = group[col].dropna().unique()
                    if len(unique_values) > 1:
                        examples = []
                        for val in unique_values[:3]:
                            row_idx = group[group[col] == val].index[0]
                            examples.append(f"{val} (row {row_idx})")
                        errors.append(f"[ID_INCONSISTENCY] ERROR: rows with Product '{product}' have inconsistent '{col}' values: [{', '.join(examples)}].")
    
    if 'Sale ID' in df.columns:
        sale_id_groups = df.groupby('Sale ID')
        
        consistency_columns = ['Branch Name', 'Sale Date']
        
        for col in consistency_columns:
            if col in df.columns:
                for sale_id, group in sale_id_groups:
                    if len(group) > 1:
                        unique_values = group[col].dropna().unique()
                        if len(unique_values) > 1:
                            examples = []
                            for val in unique_values[:3]:
                                row_idx = group[group[col] == val].index[0]
                                examples.append(f"{val} (row {row_idx})")
                            errors.append(f"[ID_INCONSISTENCY] ERROR: rows with Sale ID '{sale_id}' have inconsistent '{col}' values: [{', '.join(examples)}].")
    
    return errors

def check_product_whitespace(df: pd.DataFrame) -> List[str]:
    warnings = []
    
    text_columns = ['Product', 'Packsize', 'OrderList', 'Branch Name', 'Dept Fullname', 'Group Fullname']
    
    for col in text_columns:
        if col in df.columns:
            string_col = df[col].astype(str)
            
            leading_spaces_mask = string_col.str.match(r'^\s+.*')
            if leading_spaces_mask.any():
                for idx in df[leading_spaces_mask].index[:3]:
                    value = df.loc[idx, col]
                    warnings.append(f"[WHITESPACE] WARNING: Column '{col}' contains whitespace errors: '{value}' at row {idx} (leading spaces).")
            
            trailing_spaces_mask = string_col.str.match(r'.*\s+$')
            if trailing_spaces_mask.any():
                for idx in df[trailing_spaces_mask].index[:3]:
                    value = df.loc[idx, col]
                    warnings.append(f"[WHITESPACE] WARNING: Column '{col}' contains trailing spaces: '{value}' at row {idx}.")
            
            multiple_spaces_mask = string_col.str.contains(r'\s{2,}', regex=True, na=False)
            if multiple_spaces_mask.any():
                for idx in df[multiple_spaces_mask].index[:3]:
                    value = df.loc[idx, col]
                    warnings.append(f"[WHITESPACE] WARNING: Column '{col}' contains multiple internal spaces: '{value}' at row {idx}.")
    
    return warnings

def check_category_drifts(df: pd.DataFrame) -> List[str]:
    warnings = []
    
    if 'Product' in df.columns and 'Dept Fullname' in df.columns:
        product_groups = df.groupby('Product')
        
        for product, group in product_groups:
            unique_depts = group['Dept Fullname'].dropna().unique()
            if len(unique_depts) > 1:
                dept_examples = []
                for dept in unique_depts[:3]:
                    rows = group[group['Dept Fullname'] == dept].index.tolist()[:3]
                    dept_examples.append(f"'{dept}' (rows {rows})")
                warnings.append(f"[CATEGORY_DRIFT] WARNING: Category drift detected for product '{product}': categories found [{', '.join(dept_examples)}].")
    
    if 'Product' in df.columns and 'Group Fullname' in df.columns:
        product_groups = df.groupby('Product')
        
        for product, group in product_groups:
            unique_groups = group['Group Fullname'].dropna().unique()
            if len(unique_groups) > 1:
                group_examples = []
                for grp in unique_groups[:3]:
                    rows = group[group['Group Fullname'] == grp].index.tolist()[:3]
                    group_examples.append(f"'{grp}' (rows {rows})")
                warnings.append(f"[CATEGORY_DRIFT] WARNING: Group drift detected for product '{product}': groups found [{', '.join(group_examples)}].")
    
    return warnings

def check_near_duplicate_rows(df: pd.DataFrame) -> List[str]:
    warnings = []
    
    if 'Sale Date' not in df.columns:
        return warnings
    
    df_copy = df.copy()
    
    try:
        df_copy['Sale Date'] = pd.to_datetime(df_copy['Sale Date'], errors='coerce')
    except:
        return warnings
    
    non_date_columns = [col for col in df.columns if col != 'Sale Date']
    
    grouped = df_copy.groupby(non_date_columns, dropna=False)
    
    for name, group in grouped:
        if len(group) > 1:
            sorted_group = group.sort_values('Sale Date')
            dates = sorted_group['Sale Date'].dropna()
            
            if len(dates) > 1:
                for i in range(len(dates) - 1):
                    date1 = dates.iloc[i]
                    date2 = dates.iloc[i + 1]
                    
                    if pd.notna(date1) and pd.notna(date2):
                        time_diff = abs((date2 - date1).total_seconds())
                        
                        if time_diff <= 1:
                            row1 = sorted_group.iloc[i].name
                            row2 = sorted_group.iloc[i + 1].name
                            warnings.append(f"[NEAR_DUPLICATE] WARNING: Near-duplicate rows detected: rows [{row1}, {row2}] differ only by Sale Date ({date1} vs {date2}).")
    
    return warnings

def check_date_consistency(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Sale Date' in df.columns:
        try:
            date_col = pd.to_datetime(df['Sale Date'], errors='coerce')
            
            invalid_dates_mask = date_col.isna() & df['Sale Date'].notna()
            if invalid_dates_mask.any():
                invalid_values = df.loc[invalid_dates_mask, 'Sale Date'].tolist()[:5]
                invalid_rows = df[invalid_dates_mask].index.tolist()[:5]
                errors.append(f"[DATE_FORMAT] ERROR: Column 'Sale Date' has invalid date values: {invalid_values} at rows {invalid_rows}.")
            
            future_dates_mask = date_col > pd.Timestamp.now()
            if future_dates_mask.any():
                future_values = date_col[future_dates_mask].tolist()[:5]
                future_rows = df[future_dates_mask].index.tolist()[:5]
                errors.append(f"[DATE_RANGE] WARNING: Column 'Sale Date' has future dates: {future_values} at rows {future_rows}.")
            
            very_old_dates_mask = date_col < pd.Timestamp('2000-01-01')
            if very_old_dates_mask.any():
                old_values = date_col[very_old_dates_mask].tolist()[:5]
                old_rows = df[very_old_dates_mask].index.tolist()[:5]
                errors.append(f"[DATE_RANGE] WARNING: Column 'Sale Date' has very old dates: {old_values} at rows {old_rows}.")
        except:
            pass
    
    return errors

def check_outliers(df: pd.DataFrame) -> List[str]:
    warnings = []
    
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
                    outlier_values = numeric_col[outlier_mask].tolist()[:5]
                    outlier_rows = df[outlier_mask].index.tolist()[:5]
                    warnings.append(f"[OUTLIER] WARNING: Column '{col}' has extreme values {outlier_values} at rows {outlier_rows}.")
    
    return warnings

def check_business_logic(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'Trade Price' in df.columns and 'RRP' in df.columns:
        trade_price = pd.to_numeric(df['Trade Price'], errors='coerce')
        rrp = pd.to_numeric(df['RRP'], errors='coerce')
        
        invalid_mask = (trade_price > rrp) & trade_price.notna() & rrp.notna()
        if invalid_mask.any():
            invalid_rows = df[invalid_mask].index.tolist()[:5]
            examples = []
            for idx in invalid_rows[:3]:
                tp = df.loc[idx, 'Trade Price']
                r = df.loc[idx, 'RRP']
                examples.append(f"row {idx}: Trade Price={tp}, RRP={r}")
            errors.append(f"[BUSINESS_LOGIC] ERROR: Trade Price exceeds RRP in some rows. Examples: [{', '.join(examples)}].")
    
    if 'Turnover' in df.columns and 'Vat Amount' in df.columns and 'Turnover ex VAT' in df.columns:
        turnover = pd.to_numeric(df['Turnover'], errors='coerce')
        vat_amount = pd.to_numeric(df['Vat Amount'], errors='coerce')
        turnover_ex_vat = pd.to_numeric(df['Turnover ex VAT'], errors='coerce')
        
        calculated_turnover = turnover_ex_vat + vat_amount
        diff = abs(turnover - calculated_turnover)
        
        inconsistent_mask = (diff > 0.02) & turnover.notna() & vat_amount.notna() & turnover_ex_vat.notna()
        if inconsistent_mask.any():
            inconsistent_rows = df[inconsistent_mask].index.tolist()[:5]
            examples = []
            for idx in inconsistent_rows[:3]:
                t = df.loc[idx, 'Turnover']
                v = df.loc[idx, 'Vat Amount']
                te = df.loc[idx, 'Turnover ex VAT']
                examples.append(f"row {idx}: Turnover={t}, VAT={v}, Turnover ex VAT={te}")
            errors.append(f"[BUSINESS_LOGIC] ERROR: Turnover != Turnover ex VAT + VAT Amount. Examples: [{', '.join(examples)}].")
    
    if 'Qty Sold' in df.columns and 'Refund Qty' in df.columns:
        qty_sold = pd.to_numeric(df['Qty Sold'], errors='coerce')
        refund_qty = pd.to_numeric(df['Refund Qty'], errors='coerce')
        
        invalid_mask = (refund_qty > qty_sold) & qty_sold.notna() & refund_qty.notna()
        if invalid_mask.any():
            invalid_rows = df[invalid_mask].index.tolist()[:5]
            examples = []
            for idx in invalid_rows[:3]:
                qs = df.loc[idx, 'Qty Sold']
                rq = df.loc[idx, 'Refund Qty']
                examples.append(f"row {idx}: Qty Sold={qs}, Refund Qty={rq}")
            errors.append(f"[BUSINESS_LOGIC] ERROR: Refund Qty exceeds Qty Sold. Examples: [{', '.join(examples)}].")
    
    return errors

def summarize_dataset(df: pd.DataFrame) -> List[str]:
    summary = []
    
    summary.append(f"[SUMMARY] INFO: Dataset has {len(df)} rows and {len(df.columns)} columns.")
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        if col in EXPECTED_COLUMNS:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                min_val = col_data.min()
                max_val = col_data.max()
                mean_val = col_data.mean()
                summary.append(f"[SUMMARY] INFO: Column '{col}' (numeric) - min={min_val:.2f}, max={max_val:.2f}, mean={mean_val:.2f}.")
    
    categorical_columns = df.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        if col in EXPECTED_COLUMNS:
            distinct_count = df[col].nunique()
            summary.append(f"[SUMMARY] INFO: Column '{col}' (categorical) - {distinct_count} distinct values.")
    
    return summary

def main():
    if len(sys.argv) != 2:
        print("Usage: python detect_errors.py path/to/dataset.ext")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        df = load_dataset(file_path)
    except Exception as e:
        print(f"[ERROR] Failed to load dataset: {e}")
        sys.exit(1)
    
    print("DATASET ERROR REPORT")
    print("=" * 50)
    print(f"Shape: {len(df)} rows x {len(df.columns)} columns")
    print()
    
    all_messages = []
    
    all_messages.extend(summarize_dataset(df))
    all_messages.extend(check_missing_values(df))
    all_messages.extend(check_duplicates(df))
    all_messages.extend(check_basic_types(df))
    all_messages.extend(check_value_ranges(df))
    all_messages.extend(check_allowed_categories(df))
    all_messages.extend(check_id_consistency(df))
    all_messages.extend(check_product_whitespace(df))
    all_messages.extend(check_category_drifts(df))
    all_messages.extend(check_near_duplicate_rows(df))
    all_messages.extend(check_date_consistency(df))
    all_messages.extend(check_outliers(df))
    all_messages.extend(check_business_logic(df))
    
    if all_messages:
        for msg in all_messages:
            print(f"- {msg}")
    else:
        print("No errors or warnings detected.")
    
    print()
    print("=" * 50)
    print("END OF REPORT")

if __name__ == "__main__":
    main()
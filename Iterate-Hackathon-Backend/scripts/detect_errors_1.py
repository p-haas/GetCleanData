import sys
from typing import List
import pandas as pd
import numpy as np

EXPECTED_COLUMNS = ['id', 'name', 'age']

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
        errors.append(f"WARNING: Extra columns found: {sorted(list(extra))}")
    
    return errors

def check_missing_values(df: pd.DataFrame) -> List[str]:
    errors = []
    for col in EXPECTED_COLUMNS:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                errors.append(f"ERROR: Column '{col}' has {missing_count} missing values.")
    return errors

def check_duplicates(df: pd.DataFrame) -> List[str]:
    errors = []
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        errors.append(f"ERROR: There are {duplicate_count} duplicate rows.")
    return errors

def check_basic_types(df: pd.DataFrame) -> List[str]:
    errors = []
    for col in df.columns:
        if df[col].dtype == 'object':
            non_null = df[col].dropna()
            if len(non_null) > 0:
                numeric_count = 0
                non_numeric_values = []
                for val in non_null:
                    try:
                        float(val)
                        numeric_count += 1
                    except (ValueError, TypeError):
                        if len(non_numeric_values) < 5:
                            non_numeric_values.append(str(val))
                
                if numeric_count > len(non_null) * 0.8 and non_numeric_values:
                    errors.append(f"WARNING: Column '{col}' looks numeric but contains non-numeric values: {non_numeric_values}")
    return errors

def check_value_ranges(df: pd.DataFrame) -> List[str]:
    errors = []
    
    if 'age' in df.columns:
        age_col = df['age'].dropna()
        if len(age_col) > 0:
            try:
                age_numeric = pd.to_numeric(age_col, errors='coerce')
                invalid_ages = age_numeric[(age_numeric < 0) | (age_numeric > 120)]
                if len(invalid_ages) > 0:
                    examples = invalid_ages.head(3).tolist()
                    errors.append(f"ERROR: Column 'age' has values outside [0, 120]. Examples: {examples}")
            except:
                pass
    
    quantity_like_cols = ['quantity', 'amount', 'price', 'total', 'count', 'stock']
    for col in df.columns:
        if any(keyword in col.lower() for keyword in quantity_like_cols):
            if pd.api.types.is_numeric_dtype(df[col]):
                negative_values = df[col][df[col] < 0].dropna()
                if len(negative_values) > 0:
                    examples = negative_values.head(3).tolist()
                    errors.append(f"WARNING: Column '{col}' has negative values. Examples: {examples}")
    
    return errors

def check_allowed_categories(df: pd.DataFrame) -> List[str]:
    errors = []
    for col in df.columns:
        if df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col]):
            value_counts = df[col].value_counts()
            if len(value_counts) > 1:
                total_count = len(df[col].dropna())
                for category, count in value_counts.items():
                    if count == 1 and total_count > 10:
                        errors.append(f"WARNING: Column '{col}' has rare category '{category}' (1 occurrence).")
                    elif count / total_count < 0.01 and total_count > 100:
                        errors.append(f"WARNING: Column '{col}' has rare category '{category}' ({count} occurrences, {count/total_count*100:.2f}%).")
    return errors

def check_unique_constraints(df: pd.DataFrame) -> List[str]:
    errors = []
    unique_like_cols = ['id', 'email', 'identifier', 'uuid', 'key']
    
    for col in df.columns:
        if any(keyword in col.lower() for keyword in unique_like_cols):
            duplicates = df[col].dropna()
            duplicate_values = duplicates[duplicates.duplicated()].unique()
            if len(duplicate_values) > 0:
                examples = duplicate_values[:3].tolist()
                errors.append(f"ERROR: Column '{col}' contains duplicate values. Example duplicates: {examples}")
    
    return errors

def check_outliers(df: pd.DataFrame) -> List[str]:
    errors = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            col_data = df[col].dropna()
            if len(col_data) > 10:
                q1 = col_data.quantile(0.25)
                q3 = col_data.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower_bound = q1 - 3 * iqr
                    upper_bound = q3 + 3 * iqr
                    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                    if len(outliers) > 0:
                        examples = outliers.head(3).tolist()
                        errors.append(f"WARNING: Column '{col}' has {len(outliers)} potential outliers. Examples: {examples}")
    return errors

def check_pattern_columns(df: pd.DataFrame) -> List[str]:
    errors = []
    
    email_like_cols = ['email', 'mail', 'e-mail']
    for col in df.columns:
        if any(keyword in col.lower() for keyword in email_like_cols):
            if col in df.columns and df[col].dtype == 'object':
                non_null = df[col].dropna()
                invalid_emails = []
                for val in non_null:
                    if '@' not in str(val) or '.' not in str(val):
                        if len(invalid_emails) < 3:
                            invalid_emails.append(str(val))
                if invalid_emails:
                    errors.append(f"WARNING: Column '{col}' contains invalid email patterns. Examples: {invalid_emails}")
    
    return errors

def summarize_dataset(df: pd.DataFrame) -> List[str]:
    info = []
    info.append(f"INFO: Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns")
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            col_data = df[col].dropna()
            if len(col_data) > 0:
                min_val = col_data.min()
                max_val = col_data.max()
                mean_val = col_data.mean()
                info.append(f"INFO: Column '{col}' (numeric) - min={min_val}, max={max_val}, mean={mean_val:.2f}")
        elif df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col]):
            distinct_count = df[col].nunique()
            info.append(f"INFO: Column '{col}' (categorical) - {distinct_count} distinct values")
    
    return info

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
    print()
    
    summary = summarize_dataset(df)
    for line in summary:
        print(line)
    print()
    
    all_errors = []
    
    all_errors.extend(check_columns(df))
    all_errors.extend(check_missing_values(df))
    all_errors.extend(check_duplicates(df))
    all_errors.extend(check_basic_types(df))
    all_errors.extend(check_value_ranges(df))
    all_errors.extend(check_allowed_categories(df))
    all_errors.extend(check_unique_constraints(df))
    all_errors.extend(check_outliers(df))
    all_errors.extend(check_pattern_columns(df))
    
    if all_errors:
        print("ERRORS AND WARNINGS:")
        print("-" * 50)
        for error in all_errors:
            print(f"  {error}")
    else:
        print("No errors or warnings detected.")
    
    print()
    print("=" * 50)
    print("END OF REPORT")

if __name__ == "__main__":
    main()
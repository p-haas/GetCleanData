# app/sampling.py
"""
Intelligent dataset sampling for agent analysis.
Samples datasets efficiently to minimize token usage while maximizing insight.
"""
from typing import Dict, List, Any
import pandas as pd


def smart_sample_dataframe(
    df: pd.DataFrame,
    max_sample_rows: int = 300,
) -> pd.DataFrame:
    """
    Intelligently sample a dataframe for agent analysis.
    
    Strategy:
    - Small datasets (<= max_sample_rows): Use entire dataset
    - Large datasets: Sample from beginning, middle, and end
        - First 100 rows: Headers and initial patterns
        - Random 100 from middle: Variety and distribution
        - Last 100 rows: Detect data evolution over time
    
    Args:
        df: Input dataframe
        max_sample_rows: Maximum number of rows to sample
    
    Returns:
        Sampled dataframe
    """
    total_rows = len(df)
    
    # Small dataset: use everything
    if total_rows <= max_sample_rows:
        return df.copy()
    
    # Large dataset: smart sampling
    sample_size_per_section = max_sample_rows // 3
    
    # First section (beginning)
    first_section = df.head(sample_size_per_section)
    
    # Middle section (random sample excluding first and last)
    middle_start = sample_size_per_section
    middle_end = total_rows - sample_size_per_section
    if middle_end > middle_start:
        middle_indices = df.iloc[middle_start:middle_end].sample(
            n=min(sample_size_per_section, middle_end - middle_start),
            random_state=42
        ).index
        middle_section = df.loc[middle_indices]
    else:
        middle_section = pd.DataFrame()
    
    # Last section (end)
    last_section = df.tail(sample_size_per_section)
    
    # Combine sections
    sampled = pd.concat([first_section, middle_section, last_section])
    return sampled.sort_index()


def prepare_sample_rows(
    df: pd.DataFrame,
    max_rows: int = 5,
) -> List[Dict[str, Any]]:
    """
    Prepare sample rows for agent input.
    
    Args:
        df: Input dataframe
        max_rows: Maximum number of sample rows to return
    
    Returns:
        List of row dictionaries
    """
    sample_df = df.head(max_rows)
    
    # Convert to dict, handling NaN values
    rows = []
    for _, row in sample_df.iterrows():
        row_dict = {}
        for col in df.columns:
            val = row[col]
            # Convert NaN to None for JSON serialization
            if pd.isna(val):
                row_dict[col] = None
            else:
                row_dict[col] = val
        rows.append(row_dict)
    
    return rows


def prepare_column_summaries(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Prepare column summaries for agent input.
    
    Args:
        df: Input dataframe
    
    Returns:
        List of column summary dictionaries
    """
    summaries = []
    
    for col in df.columns:
        series = df[col]
        
        # Infer type
        if pd.api.types.is_bool_dtype(series):
            inferred_type = "boolean"
        elif pd.api.types.is_numeric_dtype(series):
            inferred_type = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            inferred_type = "date"
        elif pd.api.types.is_object_dtype(series):
            unique_ratio = series.nunique(dropna=True) / max(len(series), 1)
            inferred_type = "categorical" if unique_ratio <= 0.2 else "string"
        else:
            inferred_type = "string"
        
        # Get sample values
        sample_values = []
        for val in series.dropna().head(3):
            sample_values.append(str(val))
        
        # Build summary
        summary = {
            "name": str(col),
            "inferred_type": inferred_type,
            "sample_values": sample_values,
            "missing_count": int(series.isna().sum()),
            "unique_count": int(series.nunique(dropna=True)),
        }
        summaries.append(summary)
    
    return summaries

# app/code_analysis.py
"""
Code-based dataset analysis using Claude's native code execution tool.
Replaces the custom sandbox with Anthropic's built-in secure code execution.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import anthropic
import pandas as pd
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Models for Code Execution Results
# ============================================================================


class CodeInvestigation(BaseModel):
    """Results from a code-based investigation."""

    code: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class EnhancedIssueModel(BaseModel):
    """Issue model with code investigation results."""

    id: str
    type: str
    severity: str
    description: str
    affectedColumns: List[str]
    suggestedAction: str
    category: str
    affectedRows: Optional[int] = None
    temporalPattern: Optional[str] = None
    investigation: Optional[CodeInvestigation] = None


# ============================================================================
# Claude Code Execution Integration
# ============================================================================


def _load_example_script() -> str:
    """
    Load example data quality script to include in system prompt.
    This helps Claude learn effective patterns for data analysis.
    """
    from pathlib import Path
    
    example_path = Path(__file__).parent.parent / "tests" / "detect_correct.py"
    
    if not example_path.exists():
        logger.warning(f"Example script not found at {example_path}")
        return "# No example script available"
    
    try:
        return example_path.read_text()
    except Exception as e:
        logger.error(f"Failed to load example script: {e}")
        return "# Error loading example script"


async def analyze_dataset_with_code(
    dataset_id: str,
    df: pd.DataFrame,
    dataset_understanding: Dict[str, Any],
    user_instructions: str = "",
) -> Dict[str, Any]:
    """
    Analyze dataset using Claude's code execution tool.

    The agent will write Python code to investigate the dataset and generate
    data-driven insights based on actual analysis results.

    Args:
        dataset_id: Unique dataset identifier
        df: Pandas DataFrame to analyze
        dataset_understanding: Output from dataset understanding step
        user_instructions: Optional context from user

    Returns:
        Dict with issues array and investigation results
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Prepare dataset summary for the agent (limit size for context)
    dataset_summary = {
        "id": dataset_id,
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_rows": df.head(10).to_dict(orient="records"),
        "missing_values": df.isnull().sum().to_dict(),
        "understanding": dataset_understanding,
    }

    # Load example script for reference
    example_script = _load_example_script()
    
    # Create the analysis prompt
    system_prompt = f"""You are a data quality expert analyzing a dataset.

    Your task is to:
    1. Write Python code to investigate data quality issues
    2. Execute the code to gather evidence
    3. Generate a structured JSON report of issues found

    You have access to a pandas DataFrame called 'df' with the dataset.

    EXAMPLE REFERENCE SCRIPT:
    Below is an example data quality detection script. You can adapt these patterns for your analysis:
    
    {example_script}

    For each issue you find, you MUST:
    - Write Python code to investigate it (similar to the example patterns above)
    - Execute the code to get concrete numbers/patterns
    - Include the investigation results in your response

    Return ONLY valid JSON (no markdown, no code fences) in this format:
    {{
    "issues": [
        {{
        "id": "dataset_id_issue_slug",
        "type": "missing_values|duplicates|outliers|inconsistent_categories|etc",
        "severity": "low|medium|high",
        "description": "Detailed description WITH specific numbers from your analysis",
        "affectedColumns": ["column1"],
        "suggestedAction": "What to do",
        "category": "quick_fixes|smart_fixes",
        "affectedRows": 123,
        "temporalPattern": "optional pattern description",
        "investigation": {{
            "code": "df['column'].isna().sum()",
            "output": "actual output from code execution",
            "findings": "what the code revealed"
        }}
        }}
    ],
    "summary": "Analysis complete. Found X issues.",
    "completedAt": "ISO timestamp"
    }}

    CRITICAL:
    - Use code execution to gather REAL data, not estimates
    - Adapt patterns from the example script to the actual dataset
    - Include specific numbers, percentages, date ranges in descriptions
    - investigation.code must be the actual Python you executed
    - investigation.output must be the actual result
    - Return ONLY the JSON, nothing else"""

    user_prompt = f"""Analyze this dataset for data quality issues:

    Dataset Summary:
    {json.dumps(dataset_summary, indent=2, default=str)}

    User Context: {user_instructions or "None provided"}

    Instructions:
    1. Use the code execution tool to investigate the dataset
    2. Look for: missing values, duplicates, outliers, temporal patterns, category drift
    3. For each issue, write and execute Python code to gather evidence
    4. Generate the JSON report with investigation results

    Available in code environment:
    - `df`: pandas DataFrame with the full dataset
    - All standard pandas/numpy operations

    Begin your analysis now. Use code execution to investigate, then return the JSON report."""

    try:
        # Prepare the DataFrame as CSV for the code execution environment
        df_csv = df.to_csv(index=False)

        # Create message with code execution tool
        response = await asyncio.to_thread(
            client.beta.messages.create,
            model=settings.claude_model,
            betas=["code-execution-2025-08-25"],
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"""First, load the dataset:

                ```python
                import pandas as pd
                import numpy as np
                from io import StringIO

                csv_data = '''
                {df_csv}
                '''

                df = pd.read_csv(StringIO(csv_data))
                ```

                Now: {user_prompt}""",
                }
            ],
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
        )

        logger.info(f"Claude response: {response}")

        # Extract the final text response (should be JSON)
        final_text = None
        for block in response.content:
            if hasattr(block, "type") and block.type == "text":
                final_text = block.text

        if not final_text:
            raise ValueError("No text response from Claude")

        # Parse the JSON response
        result = _parse_analysis_response(final_text, dataset_id)

        return result

    except Exception as e:
        logger.error(f"Code-based analysis failed: {e}")
        raise


def _parse_analysis_response(response_text: str, dataset_id: str) -> Dict[str, Any]:
    """Parse and validate the agent's JSON response."""
    # Strip code fences if present
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        data = json.loads(text)

        # Ensure completedAt is set
        if "completedAt" not in data:
            data["completedAt"] = datetime.now(timezone.utc).isoformat()

        # Validate issues structure
        if "issues" not in data:
            raise ValueError("Response missing 'issues' field")

        # Ensure all issues have required fields
        for issue in data["issues"]:
            if "id" not in issue:
                issue["id"] = f"{dataset_id}_{issue.get('type', 'unknown')}"
            if "category" not in issue:
                issue["category"] = "quick_fixes"
            if "severity" not in issue:
                issue["severity"] = "medium"

        return data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}\nResponse: {text[:500]}")
        raise ValueError(f"Invalid JSON response: {e}")


# ============================================================================
# Backward Compatible API
# ============================================================================


async def generate_analysis_issues_with_code(
    dataset_id: str,
    df: pd.DataFrame,
    dataset_understanding: Dict[str, Any],
    user_instructions: str = "",
) -> Dict[str, Any]:
    """
    Generate analysis issues using code execution.

    This is a drop-in replacement for the original generate_analysis_issues
    but uses Claude's code execution tool to gather real evidence.

    Args:
        dataset_id: Unique dataset identifier
        df: Pandas DataFrame to analyze
        dataset_understanding: Output from dataset understanding step
        user_instructions: Optional context from user

    Returns:
        Dict with issues array (same format as before)
    """
    return await analyze_dataset_with_code(
        dataset_id=dataset_id,
        df=df,
        dataset_understanding=dataset_understanding,
        user_instructions=user_instructions,
    )


# ============================================================================
# Simplified Analysis for Quick Testing
# ============================================================================


async def run_quick_investigation(
    df: pd.DataFrame,
    investigation_type: str = "missing_values",
) -> CodeInvestigation:
    """
    Run a quick code-based investigation on a DataFrame.

    Args:
        df: DataFrame to investigate
        investigation_type: Type of investigation (missing_values, duplicates, etc.)

    Returns:
        CodeInvestigation with results
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompts = {
        "missing_values": "Analyze missing values. Return dict with column names and counts.",
        "duplicates": "Find duplicate rows. Return count of duplicates.",
        "outliers": "Detect outliers using IQR method. Return count and values.",
        "temporal": "Analyze temporal patterns in the data. Return findings.",
    }

    df_csv = df.to_csv(index=False)

    try:
        response = await asyncio.to_thread(
            client.beta.messages.create,
            model=settings.claude_model,
            betas=["code-execution-2025-08-25"],
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"""Load this dataset and {prompts.get(investigation_type, prompts["missing_values"])}

                ```python
                import pandas as pd
                from io import StringIO

                csv_data = '''
                {df_csv}
                '''

                df = pd.read_csv(StringIO(csv_data))
                ```

                Now investigate and return your findings as a dict.""",
                }
            ],
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
        )

        # Extract code and output from tool use
        code_used = None
        output = None

        for block in response.content:
            if hasattr(block, "type"):
                if block.type == "tool_use" and block.name == "code_execution":
                    code_used = block.input.get("code", "")
                elif block.type == "text":
                    output = block.text

        return CodeInvestigation(
            code=code_used or "No code extracted",
            success=True,
            output=output,
        )

    except Exception as e:
        logger.error(f"Quick investigation failed: {e}")
        return CodeInvestigation(
            code="",
            success=False,
            output=None,
            error=str(e),
        )

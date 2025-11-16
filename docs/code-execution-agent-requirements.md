# Code Execution Agent - Requirements & Features

## Overview

We need an AI agent that analyzes uploaded datasets (CSV/Excel files) for data quality issues using Claude's code execution capabilities. The agent should intelligently detect problems, write Python scripts to investigate them, and return structured findings that the frontend can display to users.

## Core User Flow

1. **User uploads a dataset** → Backend stores it
2. **User requests analysis** → Agent examines the data
3. **Agent discovers issues** → Returns structured findings with evidence
4. **Frontend displays issues** → User sees problems organized by category
5. **User applies fixes** → Backend remediates the data

## Key Features

### Intelligent Issue Detection

The agent should autonomously discover various data quality problems:

- **Missing values**: Detect nulls, empty strings, placeholder values
- **Duplicates**: Find exact and near-duplicate records
- **Outliers**: Identify statistical anomalies in numeric columns
- **Inconsistencies**: Spot categorical variations, whitespace issues, formatting problems
- **Temporal patterns**: Notice changes over time (e.g., category drift after a certain date)
- **Invalid data**: Find unparseable dates, negative quantities where impossible, etc.

The agent should use code execution to investigate and gather concrete evidence for each issue found.

### Smart Sampling Strategy

For large datasets, the agent should work with a sample to stay within token limits:

- Send a manageable sample (target: ~1000 rows) to Claude for analysis
- Truncate long text fields to save tokens
- Drop high-cardinality columns if needed to fit budget
- Write detection scripts that work on samples but can scale to full datasets
- Execute validated scripts on the complete dataset for accurate counts

The system should automatically handle datasets from small (hundreds of rows) to very large (millions of rows).

### Evidence-Based Reporting

Don't just report abstract counts—show users what the problems actually look like:

- Extract real examples of problematic data from their file
- Show "before" and "after" for proposed fixes with actual values
- Provide concrete transformations: `"  John Doe  "` → `"John Doe"`, not just "remove whitespace"
- Include representative samples so users understand the pattern

### Two Types of Issues

**Quick Fixes** (Automated):
- Can be applied automatically without user input
- Examples: trimming whitespace, removing exact duplicates, filling forward dates
- User clicks "Apply" and it's done

**Smart Fixes** (Interactive):
- Require business context or user decision
- Examples: which category name is correct? how to handle this outlier? 
- System asks user questions, then applies fix based on their answer

### Structured Output

The agent must return well-formed JSON that the frontend can reliably parse and display:

- Standard schema with required fields
- Deterministic IDs for each issue
- Severity levels (low/medium/high)
- Clear descriptions with specific numbers
- Executable Python code showing how issues were detected
- Metadata: affected columns, row counts, timestamps

### Progress Streaming

Show users what's happening during analysis:

- Stream live updates as the agent works
- Meaningful status messages: "Investigating missing values in 'Product' column..."
- Progress indication for long-running analyses
- Final results delivered when complete

### Graceful Error Handling

The system should never crash from unexpected agent responses:

- Parse malformed JSON safely
- Handle missing fields with sensible defaults
- Log errors with context for debugging
- Fall back to simpler heuristic detection if agent fails
- Continue processing other issues even if one script fails

### Caching & Performance

- Cache analysis results so reloading the page doesn't re-run everything
- Provide a "Re-analyze" option to force fresh analysis
- Target completion times: <10s for small datasets, <60s for large ones
- Keep memory usage reasonable even with huge files

### Frontend Integration

The frontend should display:

- Issues organized into "Quick Fixes" and "Smart Fixes" tabs
- Each issue card showing: severity, description, affected columns, row count, suggested action
- Expandable investigation details: Python code used, execution results, findings
- Evidence section with real examples from the data
- Apply buttons for quick fixes
- Dialog prompts for smart fixes requiring user input

### Configuration Flexibility

Make key parameters configurable:

- Sample size for code execution
- Maximum dataset size to process
- Timeout limits for agent calls
- Feature flag to enable/disable agent (fall back to heuristics)
- Model selection (which Claude version to use)

### Observability

Log everything needed for debugging and monitoring:

- Analysis start/complete with timing
- Sampling decisions (rows reduced, columns dropped)
- Token usage estimates
- Success/failure rates per issue type
- Any errors with full context
- Performance metrics for each phase

## Success Criteria

**Agent works well if:**
- It reliably returns valid JSON that frontend can parse
- Descriptions are specific and actionable (include real numbers and examples)
- Investigation code executes successfully on full datasets
- Evidence shows concrete examples from the actual data
- Quick fixes work automatically
- Smart fixes provide helpful context for user decisions
- Analysis completes in reasonable time
- System degrades gracefully when things go wrong

**User experience is good if:**
- Issues are easy to understand at a glance
- Examples make problems immediately clear
- Users trust the findings (backed by real evidence)
- Fix suggestions are practical and safe to apply
- Progress is visible during long analyses
- Error messages are friendly and actionable

## Technical Considerations

- Use Anthropic's code execution tool (not custom sandbox)
- Handle token limits intelligently with adaptive sampling
- Execute scripts on full dataset after validating on sample
- Support both CSV and Excel file formats
- Work with datasets containing millions of rows
- Process multiple issues in parallel where possible
- Store results for quick retrieval
- Stream progress updates via Server-Sent Events

## Future Enhancements

Consider adding later:
- Column-level statistics and profiling
- Automated fix previews (show what will change before applying)
- Batch operations across multiple datasets
- Custom user-defined quality rules
- Export cleaned datasets
- Audit trail of all changes made
- Comparison before/after applying fixes
- Machine learning for pattern detection
- Integration with data catalogs and lineage tools

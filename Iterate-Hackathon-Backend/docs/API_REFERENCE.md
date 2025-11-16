# API Reference

Complete API documentation for the Iterate Data Quality Analysis Platform backend.

**Base URL**: `http://localhost:8000`  
**API Version**: 1.0  
**Authentication**: None (add JWT/API key in production)

## Table of Contents

1. [Dataset Management](#dataset-management)
2. [AI Agent Endpoints](#ai-agent-endpoints)
3. [Chat Interface](#chat-interface)
4. [Smart Fix Workflows](#smart-fix-workflows)
5. [Error Responses](#error-responses)

---

## Dataset Management

### Upload Dataset

Upload a CSV or Excel file for analysis.

**Endpoint**: `POST /upload-dataset`

**Request**:
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: File (required) - CSV or Excel file
  - `user_instructions`: String (optional) - Business context for the dataset

**Example**:
```bash
curl -X POST http://localhost:8000/upload-dataset \
  -F "file=@sales_data.csv" \
  -F "user_instructions=Q3 2024 sales data with known duplicates"
```

**Response**: `200 OK`
```json
{
  "dataset_id": "dataset_abc123def456",
  "file_name": "sales_data.csv",
  "file_type": "csv",
  "file_size_bytes": 524288,
  "delimiter": ",",
  "storage_path": "/data/dataset_abc123def456/sales_data.csv",
  "uploaded_at": "2025-11-16T10:30:00.123Z"
}
```

**Supported File Types**:
- CSV (`.csv`) - auto-detects delimiter (`,` `;` `\t` `|`)
- Excel (`.xlsx`, `.xls`) - reads first sheet by default

**Validation**:
- Max file size: 100MB
- Max rows: 1,000,000
- Valid column names (no special characters)

---

### Get Dataset Metadata

Retrieve metadata for an uploaded dataset.

**Endpoint**: `GET /dataset/{dataset_id}/metadata`

**Parameters**:
- `dataset_id`: String (path) - Dataset identifier

**Response**: `200 OK`
```json
{
  "dataset_id": "dataset_abc123def456",
  "file_name": "sales_data.csv",
  "file_type": "csv",
  "row_count": 10432,
  "column_count": 12,
  "columns": ["date", "product", "revenue", "quantity", ...],
  "uploaded_at": "2025-11-16T10:30:00.123Z",
  "last_analyzed_at": "2025-11-16T10:35:00.456Z"
}
```

---

### Download Dataset

Download original or cleaned dataset.

**Endpoint**: `GET /dataset/{dataset_id}/download`

**Parameters**:
- `dataset_id`: String (path) - Dataset identifier
- `version`: String (query, optional) - `original` or `cleaned` (default: `original`)

**Response**: `200 OK`
- **Content-Type**: `text/csv` or `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Body**: File download

---

## AI Agent Endpoints

### Generate Dataset Understanding

Trigger the Dataset Understanding Agent to analyze uploaded data.

**Endpoint**: `POST /understand-dataset`

**Request**:
```json
{
  "dataset_id": "dataset_abc123def456",
  "user_instructions": "This is quarterly sales data with regional breakdowns"
}
```

**Response**: `200 OK`
```json
{
  "summary": {
    "name": "sales_data.csv",
    "description": "Quarterly sales data tracking product revenue across multiple regions",
    "rowCount": 10432,
    "columnCount": 12,
    "observations": [
      "Dataset spans Q3 2024 (July-September)",
      "Contains transaction-level sales records",
      "Includes regional and product category breakdowns",
      "Some missing values in revenue column (2.3%)"
    ]
  },
  "columns": [
    {
      "name": "date",
      "dataType": "date",
      "description": "Transaction date in YYYY-MM-DD format",
      "sampleValues": ["2024-07-01", "2024-07-02", "2024-07-03"]
    },
    {
      "name": "product",
      "dataType": "categorical",
      "description": "Product name or SKU identifier",
      "sampleValues": ["Widget A", "Widget B", "Gadget X"]
    },
    {
      "name": "revenue",
      "dataType": "numeric",
      "description": "Sales revenue in USD for this transaction",
      "sampleValues": ["149.99", "299.50", "89.00"]
    }
  ],
  "suggested_context": "This appears to be point-of-sale data for a retail business. The dataset tracks individual product sales with regional attribution, useful for revenue analysis and inventory planning."
}
```

**Agent Behavior**:
- Temperature: 0.1 (consistent outputs)
- Timeout: 30 seconds
- Retries: 2 attempts
- Validation: Strict Pydantic schema

---

### Analyze Dataset

Run full analysis pipeline with issue detection and optional code investigations.

**Endpoint**: `POST /analyze-dataset`

**Request**:
```json
{
  "dataset_id": "dataset_abc123def456",
  "user_instructions": "Focus on revenue anomalies and missing customer IDs",
  "run_code_investigations": true,
  "enable_smart_fixes": true
}
```

**Response**: `200 OK` (streaming)

**Streaming Format**: Server-sent events (SSE)
```
data: {"type": "log", "message": "Starting analysis..."}

data: {"type": "progress", "message": "Dataset understanding complete"}

data: {"type": "progress", "message": "Detecting issues... (1/3 complete)"}

data: {"type": "issue", "data": {"id": "...", "type": "missing_values", ...}}

data: {"type": "complete", "data": <AnalysisResultModel>}
```

**Final Result** (`AnalysisResultModel`):
```json
{
  "issues": [
    {
      "id": "dataset_abc123_missing_revenue",
      "type": "missing_values",
      "severity": "medium",
      "description": "Revenue column contains 234 missing values (2.3% of total)",
      "affectedColumns": ["revenue"],
      "suggestedAction": "Review transactions with missing revenue. Consider using 0 for cancelled orders or removing incomplete records.",
      "category": "quick_fixes",
      "affectedRows": 234,
      "temporalPattern": "Higher missing rate on weekends (7.1% vs 1.8% weekdays)",
      "investigation": {
        "code": "import pandas as pd\nimport json\n\ndf = pd.read_csv('data.csv')\n...",
        "success": true,
        "output": {
          "missing_count": 234,
          "missing_percentage": 2.24,
          "affected_rows": [12, 45, 67, 89, ...],
          "weekend_missing": 156,
          "weekday_missing": 78
        },
        "execution_time_ms": 1234.5
      }
    },
    {
      "id": "dataset_abc123_supplier_variations",
      "type": "categorical_variations",
      "severity": "low",
      "description": "Supplier names show formatting inconsistencies (e.g., 'Acme Corp' vs 'ACME CORP')",
      "affectedColumns": ["supplier"],
      "suggestedAction": "Standardize supplier names for consistent reporting",
      "category": "smart_fixes",
      "affectedRows": null,
      "temporalPattern": null,
      "investigation": null
    }
  ],
  "summary": "Analysis complete. Found 2 data quality issues: 1 quick fix (missing values) and 1 smart fix (supplier standardization). Total affected rows: 234 of 10,432 (2.2%).",
  "completedAt": "2025-11-16T10:40:00.789Z"
}
```

**Issue Categories**:
- `quick_fixes`: Automated resolution (duplicates, missing values, formatting)
- `smart_fixes`: Requires business judgment (anomalies, variations, context)

**Issue Severities**:
- `high`: Blocks analysis or critical errors (>50% missing)
- `medium`: May lead to incorrect insights (20-50% missing)
- `low`: Minor inconsistencies (<20% missing)

---

### Get Analysis History

Retrieve past analysis results for a dataset.

**Endpoint**: `GET /dataset/{dataset_id}/analysis-history`

**Parameters**:
- `dataset_id`: String (path) - Dataset identifier
- `limit`: Integer (query, optional) - Max results (default: 10)

**Response**: `200 OK`
```json
{
  "analyses": [
    {
      "analysis_id": "analysis_xyz789",
      "completed_at": "2025-11-16T10:40:00.789Z",
      "issue_count": 2,
      "user_instructions": "Focus on revenue anomalies",
      "summary": "Found 2 issues..."
    }
  ]
}
```

---

## Chat Interface

### Send Chat Message

Conversational interface with dataset context awareness.

**Endpoint**: `POST /chat`

**Request**:
```json
{
  "session_id": "user_session_123",
  "message": "What are the main quality issues in my dataset?",
  "dataset_id": "dataset_abc123def456"
}
```

**Response**: `200 OK`
```json
{
  "reply": "Based on the analysis of your sales data, I found 2 main quality issues:\n\n1. **Missing Revenue Values** (Medium Severity)\n   - 234 transactions (2.3%) have missing revenue amounts\n   - This primarily affects weekend transactions (7.1% missing rate)\n   - Suggestion: Review if these are cancelled orders or data entry errors\n\n2. **Supplier Name Variations** (Low Severity)\n   - Inconsistent formatting (e.g., 'Acme Corp' vs 'ACME CORP')\n   - Affects reporting accuracy\n   - Suggestion: Standardize to a canonical format\n\nWould you like me to help you fix either of these issues?"
}
```

**Chat Features**:
- **Context-aware**: Accesses dataset understanding and analysis results
- **Persistent history**: Conversation stored in MongoDB per `session_id`
- **Multi-turn**: Maintains context across messages
- **Dataset grounding**: Cites specific metrics and examples

---

### Get Chat History

Retrieve conversation history for a session.

**Endpoint**: `GET /chat/{session_id}/history`

**Parameters**:
- `session_id`: String (path) - Session identifier
- `limit`: Integer (query, optional) - Max messages (default: 50)

**Response**: `200 OK`
```json
{
  "session_id": "user_session_123",
  "messages": [
    {
      "role": "user",
      "content": "What are the main issues?",
      "timestamp": "2025-11-16T10:45:00Z"
    },
    {
      "role": "assistant",
      "content": "Based on the analysis...",
      "timestamp": "2025-11-16T10:45:02Z"
    }
  ]
}
```

---

## Smart Fix Workflows

### Generate Smart Fix Follow-up

Get contextual follow-up question for a smart fix issue.

**Endpoint**: `POST /smart-fix-followup`

**Request**:
```json
{
  "dataset_id": "dataset_abc123def456",
  "issue_id": "dataset_abc123_supplier_variations",
  "user_response": null
}
```

**Response**: `200 OK`
```json
{
  "prompt": "Should these supplier name variations be consolidated into a single canonical name?",
  "options": [
    {
      "key": "consolidate",
      "label": "Yes, standardize to one format"
    },
    {
      "key": "keep_separate",
      "label": "No, keep as distinct suppliers"
    },
    {
      "key": "review_first",
      "label": "Let me review the variations first"
    }
  ],
  "examples": "Example variations:\n- 'Acme Corp' (234 occurrences)\n- 'ACME CORP' (156 occurrences)\n- 'Acme Corporation' (78 occurrences)",
  "onResponse": {
    "consolidate": {
      "nextPrompt": "Which format should be the canonical name?"
    },
    "review_first": {
      "action": "show_variations",
      "endpoint": "/dataset/{dataset_id}/column-values?column=supplier"
    }
  }
}
```

---

### Submit Smart Fix Response

Continue smart fix conversation with user's choice.

**Endpoint**: `POST /smart-fix-response`

**Request**:
```json
{
  "dataset_id": "dataset_abc123def456",
  "issue_id": "dataset_abc123_supplier_variations",
  "response_key": "consolidate",
  "history": [
    {
      "prompt": "Should these supplier names be consolidated?",
      "response": "consolidate"
    }
  ]
}
```

**Response**: `200 OK` (next question or final action)
```json
{
  "prompt": "Which format should be the canonical supplier name?",
  "options": [
    {
      "key": "most_frequent",
      "label": "Most common: 'Acme Corp' (234 occurrences)"
    },
    {
      "key": "title_case",
      "label": "Title case: 'Acme Corp'"
    },
    {
      "key": "custom",
      "label": "Let me specify a custom name"
    }
  ],
  "onResponse": {
    "most_frequent": {
      "action": "execute_standardization",
      "parameters": {
        "column": "supplier",
        "canonical_value": "Acme Corp",
        "variations": ["ACME CORP", "Acme Corporation"]
      }
    }
  }
}
```

---

### Execute Smart Fix

Apply remediation action after conversation.

**Endpoint**: `POST /execute-smart-fix`

**Request**:
```json
{
  "dataset_id": "dataset_abc123def456",
  "issue_id": "dataset_abc123_supplier_variations",
  "action": "execute_standardization",
  "parameters": {
    "column": "supplier",
    "canonical_value": "Acme Corp",
    "variations": ["ACME CORP", "Acme Corporation"]
  }
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "modified_rows": 234,
  "preview": [
    {"before": "ACME CORP", "after": "Acme Corp"},
    {"before": "Acme Corporation", "after": "Acme Corp"}
  ],
  "cleaned_dataset_id": "dataset_abc123def456_cleaned_v1"
}
```

---

## Error Responses

### Standard Error Format

All errors follow this structure:

```json
{
  "error": {
    "type": "validation_error",
    "message": "Dataset not found",
    "details": {
      "dataset_id": "invalid_id"
    }
  }
}
```

### HTTP Status Codes

| Code | Type | Description |
|------|------|-------------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input parameters |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side failure |
| 503 | Service Unavailable | Agent timeout or failure |

### Error Types

**`validation_error`**: Invalid request format
```json
{
  "error": {
    "type": "validation_error",
    "message": "Invalid dataset_id format",
    "details": {"field": "dataset_id", "value": "abc"}
  }
}
```

**`agent_timeout`**: Agent exceeded timeout
```json
{
  "error": {
    "type": "agent_timeout",
    "message": "Dataset understanding agent timed out after 30 seconds",
    "details": {"agent": "understanding", "timeout_seconds": 30}
  }
}
```

**`agent_failure`**: Agent returned invalid response
```json
{
  "error": {
    "type": "agent_failure",
    "message": "Agent returned malformed JSON",
    "details": {"agent": "analysis", "retry_count": 3}
  }
}
```

**`dataset_not_found`**: Dataset doesn't exist
```json
{
  "error": {
    "type": "dataset_not_found",
    "message": "No dataset with ID dataset_xyz",
    "details": {"dataset_id": "dataset_xyz"}
  }
}
```

**`file_too_large`**: Upload exceeds size limit
```json
{
  "error": {
    "type": "file_too_large",
    "message": "File exceeds 100MB limit",
    "details": {"size_bytes": 157286400, "limit_bytes": 104857600}
  }
}
```

---

## Rate Limiting

**Development**: No rate limiting

**Production** (recommended):
- Upload: 10 requests/hour per IP
- Analysis: 5 requests/hour per dataset
- Chat: 60 requests/minute per session

Implement via reverse proxy (nginx, Cloudflare).

---

## Webhooks (Future)

**Coming Soon**: Register webhooks for async analysis completion

```json
POST /webhooks/register
{
  "url": "https://your-app.com/webhook",
  "events": ["analysis_complete", "smart_fix_ready"]
}
```

---

**API Version**: 1.0  
**Last Updated**: 2025-11-16  
**OpenAPI Spec**: Available at `/openapi.json`

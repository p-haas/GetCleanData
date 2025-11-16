# Iterate Data Quality Analysis Platform - Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Anthropic Claude](https://img.shields.io/badge/Claude-4.5_Haiku-8B5CF6?style=flat)](https://www.anthropic.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-1C3C3C?style=flat)](https://www.langchain.com/)

> An intelligent data quality analysis backend powered by autonomous AI agents for automated dataset understanding, error detection, and guided data remediation.

## 🎯 Overview

The Iterate Backend is a FastAPI-based service that leverages **autonomous AI agents** to provide intelligent, context-aware data quality analysis for tabular datasets (CSV/Excel). Unlike traditional rule-based systems, our agentic architecture enables:

- **Autonomous Dataset Understanding**: AI agents analyze datasets to generate business-focused summaries and column descriptions
- **Intelligent Error Detection**: Multi-stage agent pipeline for detecting missing values, duplicates, anomalies, and business logic issues
- **Code-Based Investigations**: Agents generate and execute Python code in secure sandboxes to validate hypotheses
- **Guided Remediation**: Smart fix workflows that engage users in conversational problem-solving
- **Contextual Chat**: MongoDB-backed conversational interface with dataset context awareness

## 🏗️ Architecture

### AI Agent Pipeline

The system employs a **multi-agent architecture** with specialized agents for different analysis stages:

```
┌──────────────────────────────────────────────────────────────┐
│                     Dataset Upload                            │
│              (CSV/Excel → Pandas → Storage)                   │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              🤖 Dataset Understanding Agent                   │
│  • Analyzes structure, types, sample data                    │
│  • Generates business-focused descriptions                   │
│  • Identifies domain & use case                              │
│  Output: DatasetUnderstandingModel                           │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              🤖 Analysis Issues Agent                         │
│  • Detects data quality issues                               │
│  • Classifies by severity & category                         │
│  • Generates remediation suggestions                         │
│  Output: AnalysisResultModel (list of issues)                │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│         🤖 Code Execution Investigation Agent                │
│  • Generates Python analysis scripts                         │
│  • Executes in Claude's secure sandbox                       │
│  • Validates hypotheses with real data                       │
│  Output: Enhanced issues with investigation results          │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              🤖 Smart Fix Follow-up Agent                     │
│  • Generates contextual questions                            │
│  • Provides guided remediation options                       │
│  • Adapts based on user responses                            │
│  Output: SmartFixFollowupModel                               │
└──────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Core Framework**
- **FastAPI**: High-performance async API framework
- **Pydantic**: Runtime type validation and settings management
- **Pandas**: Dataframe processing and CSV/Excel handling

**AI & Agent Infrastructure**
- **Anthropic Claude 4.5 Haiku**: Primary LLM for agent reasoning
- **LangChain**: Agent orchestration and prompt management
- **Native Code Execution**: Anthropic's secure sandbox for Python execution

**Data Persistence**
- **MongoDB**: Chat history and conversation state
- **File Storage**: Local filesystem for dataset persistence
- **PostgreSQL (optional)**: Vector embeddings for semantic search

**Agent Guardrails**
- Timeout protection (configurable, default 30s)
- Automatic retry logic with exponential backoff
- Response validation with Pydantic schemas
- Token budget management for large datasets

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB instance (local or Atlas)
- Anthropic API key

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Iterate-Hackathon-Backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```bash
# Required: Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Required: MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=chat_history
MONGODB_COLLECTION_NAME=message_store

# Optional: Model selection
CLAUDE_MODEL=claude-haiku-4-5-20251001
CLAUDE_CODE_EXEC_MODEL=claude-haiku-4-5-20251001

# Optional: Agent tuning
AGENT_TIMEOUT_SECONDS=30.0
AGENT_MAX_RETRIES=2
AGENT_MAX_DATASET_ROWS=100000
AGENT_SAMPLE_ROWS=1000
AGENT_ENABLED=true
```

### Running the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## 📚 API Reference

### Core Endpoints

#### `POST /upload-dataset`
Upload and initialize dataset analysis.

**Request** (multipart/form-data):
```
file: <CSV or Excel file>
user_instructions: string (optional)
```

**Response**:
```json
{
  "dataset_id": "dataset_abc123",
  "file_name": "sales_data.csv",
  "file_type": "csv",
  "file_size_bytes": 1048576,
  "delimiter": ",",
  "storage_path": "/data/dataset_abc123/sales_data.csv",
  "uploaded_at": "2025-11-16T10:30:00Z"
}
```

#### `POST /understand-dataset`
Trigger Dataset Understanding Agent to analyze uploaded data.

**Request**:
```json
{
  "dataset_id": "dataset_abc123",
  "user_instructions": "This is quarterly sales data"
}
```

**Response**: `DatasetUnderstandingModel` (see Agent Contracts)

#### `POST /analyze-dataset`
Run full analysis pipeline with code-based investigations.

**Request**:
```json
{
  "dataset_id": "dataset_abc123",
  "user_instructions": "Focus on revenue anomalies",
  "run_code_investigations": true
}
```

**Response**: Streaming JSON with progress updates and `AnalysisResultModel`

#### `POST /chat`
Conversational interface with dataset context.

**Request**:
```json
{
  "session_id": "user_session_123",
  "message": "What are the main quality issues?",
  "dataset_id": "dataset_abc123"
}
```

**Response**:
```json
{
  "reply": "Based on the analysis, there are 3 main issues..."
}
```

### Smart Fix Endpoints

#### `POST /smart-fix-followup`
Generate contextual follow-up questions for complex issues.

**Request**:
```json
{
  "dataset_id": "dataset_abc123",
  "issue_id": "issue_supplier_variations",
  "user_response": "I want to standardize supplier names"
}
```

**Response**: `SmartFixFollowupModel` with next question and options

## 🤖 AI Agent System

### Agent Architecture Details

#### 1. Dataset Understanding Agent

**Purpose**: Generate business-focused understanding of uploaded datasets

**Input**:
- Dataset metadata (rows, columns, file type)
- Sample rows (max 1000 for large datasets)
- Column statistics and type inference
- User-provided context

**Process**:
1. Analyzes data structure and patterns
2. Infers business domain and use case
3. Generates human-readable descriptions
4. Identifies key observations

**Output**: Structured `DatasetUnderstandingModel`

**Configuration**:
- Temperature: 0.1 (low for consistency)
- Timeout: 30 seconds
- Retries: 2 attempts
- Validation: Strict Pydantic schema

#### 2. Analysis Issues Agent

**Purpose**: Detect and categorize data quality issues

**Detection Categories**:
- **Quick Fixes**: Automated resolution (missing values, duplicates, formatting)
- **Smart Fixes**: Requires business judgment (anomalies, context misalignment)

**Issue Severity Levels**:
- `high`: Blocks analysis or indicates critical errors
- `medium`: May lead to incorrect insights
- `low`: Minor inconsistencies

**Process**:
1. Receives dataset understanding from previous agent
2. Applies domain-aware heuristics
3. Generates hypotheses for each potential issue
4. Optionally triggers code investigations
5. Classifies and prioritizes issues

**Output**: `AnalysisResultModel` with categorized issues

#### 3. Code Execution Investigation Agent

**Purpose**: Validate hypotheses through secure Python code execution

**Capabilities**:
- Generate pandas analysis scripts
- Execute in Anthropic's native sandbox
- Handle datasets up to 120k tokens (~60k rows)
- Extract specific metrics and evidence

**Example Investigation Flow**:
```python
# Agent generates code like:
import pandas as pd

# Load and analyze
df = pd.read_csv('dataset.csv')
missing_pct = df['revenue'].isna().sum() / len(df) * 100

# Return structured result
{
    "missing_percentage": missing_pct,
    "affected_rows": df['revenue'].isna().sum(),
    "example_indices": df[df['revenue'].isna()].index[:5].tolist()
}
```

**Safety Guardrails**:
- Sandboxed execution (no network, no filesystem)
- Token budget limits
- Execution timeouts
- Output sanitization

**Output**: Enhanced issues with `investigation` field containing code, results, and execution metrics

#### 4. Smart Fix Follow-up Agent

**Purpose**: Guide users through complex remediation decisions

**Interaction Pattern**:
1. User selects a "smart fix" issue
2. Agent generates contextual question
3. Provides multiple choice options
4. Adapts follow-up based on response
5. Culminates in actionable fix recommendation

**Example Flow**:
```
Issue: "Supplier name variations detected (95% similarity)"

Agent Q1: "Did the supplier rebrand or change names?"
Options: [Yes - Intentional | No - Data entry errors | Unsure]

User: "No - Data entry errors"

Agent Q2: "Which should be the canonical name?"
Options: [Most frequent | Most recent | Let me specify]

User: "Most frequent"

Agent: Generates merge script to consolidate variants
```

### Agent Communication Contracts

All agents follow strict input/output schemas defined in `docs/agent-contracts.md`. This ensures:
- Type safety between frontend and backend
- Predictable error handling
- Easy testing and validation
- Clear API evolution path

**Key Contract Types**:
- `DatasetUnderstandingModel`: Dataset summary and column descriptions
- `AnalysisResultModel`: List of categorized issues
- `IssueModel`: Individual issue with metadata and suggested action
- `InvestigationModel`: Code execution results
- `SmartFixFollowupModel`: Contextual questions and options

See [`docs/AGENT_ARCHITECTURE.md`](docs/AGENT_ARCHITECTURE.md) for detailed agent design patterns.

## 🔧 Configuration & Tuning

### Agent Performance Tuning

**Timeout Settings**:
```bash
# Balance between thoroughness and responsiveness
AGENT_TIMEOUT_SECONDS=30.0  # Increase for complex datasets
AGENT_MAX_RETRIES=2         # Retry failed agent calls
```

**Dataset Size Limits**:
```bash
# Prevent token overflow
AGENT_MAX_DATASET_ROWS=100000   # Max rows for full processing
AGENT_SAMPLE_ROWS=1000          # Rows sent to Claude for code gen
```

**Model Selection**:
```bash
# Trade cost vs. quality
CLAUDE_MODEL=claude-haiku-4-5-20251001        # Fast, cost-effective
CLAUDE_CODE_EXEC_MODEL=claude-sonnet-4-5      # More capable for code
```

### Fallback Strategies

When `AGENT_ENABLED=false` or agent calls fail:
1. System falls back to `backup_analysis.py` heuristics
2. Uses rule-based detection (missing values, duplicates)
3. No code execution or smart fixes
4. Reduced quality but guaranteed availability

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Test specific module
pytest tests/test_agent.py -v

# Integration tests (requires .env)
pytest tests/integration/ -v
```

## 📂 Project Structure

```
Iterate-Hackathon-Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app and endpoints
│   ├── agent.py                # Core agent execution logic
│   ├── code_analysis.py        # Code execution agent
│   ├── chat.py                 # Conversational interface
│   ├── tools.py                # Code generation tools
│   ├── config.py               # Settings and environment
│   ├── db.py                   # MongoDB client
│   ├── dataset_store.py        # File storage management
│   ├── backup_analysis.py      # Fallback heuristics
│   ├── excel_context.py        # Dataset context building
│   └── sampling.py             # Data sampling utilities
├── data/                       # Dataset storage (gitignored)
├── scripts/                    # Generated analysis scripts
├── docs/
│   ├── AGENT_ARCHITECTURE.md   # Detailed agent design
│   ├── agent-contracts.md      # Input/output schemas
│   └── CODE_EXECUTION.md       # Code sandbox details
├── tests/
│   ├── test_agent.py
│   ├── test_code_analysis.py
│   └── integration/
├── requirements.txt
├── .env.example
└── README.md
```

## 🔒 Security Considerations

- **API Key Protection**: Store `ANTHROPIC_API_KEY` in environment, never commit
- **Code Execution**: Uses Anthropic's native sandbox (no arbitrary code execution)
- **Input Validation**: Pydantic schemas validate all agent inputs/outputs
- **Rate Limiting**: Implement at reverse proxy level (nginx/Cloudflare)
- **CORS**: Configured for specific frontend origins
- **File Upload**: Limit file sizes, validate CSV/Excel formats

## 🚧 Known Limitations

- **Dataset Size**: Claude context limits dataset samples to ~120k tokens
- **Code Execution**: Limited to pandas/numpy operations (no external libraries)
- **Processing Time**: Large datasets (>50k rows) may take 30-60 seconds
- **Cost**: Each analysis run consumes ~50k-200k tokens depending on dataset size
- **Concurrent Users**: MongoDB connection pooling required for high traffic

## 🛣️ Roadmap

- [ ] **Multi-tenant Support**: Workspace isolation and user management
- [ ] **Advanced Agents**: Time-series analysis, correlation detection
- [ ] **Auto-remediation**: One-click fixes for common issues
- [ ] **Vector Search**: Semantic similarity detection for categorical data
- [ ] **Streaming Analysis**: Real-time progress updates via WebSockets
- [ ] **Custom Rules**: User-defined validation rules via DSL
- [ ] **Caching Layer**: Redis for dataset summaries and analysis results

## 📄 License

[Specify your license here]

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests.

## 📞 Support

For issues and questions:
- GitHub Issues: [Link to issues]
- Documentation: [Link to full docs]
- Contact: [Your contact info]

---

**Built with ❤️ using Claude 4.5, FastAPI, and LangChain**

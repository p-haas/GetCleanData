# Developer Quickstart Guide

Get the Iterate backend running locally in under 5 minutes.

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.11+** installed ([Download](https://www.python.org/downloads/))
- ✅ **MongoDB** running ([Install Guide](#mongodb-setup))
- ✅ **Anthropic API Key** ([Get one here](https://console.anthropic.com/))

## 5-Minute Setup

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd Iterate-Hackathon-Backend
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env  # or your preferred editor
```

**Minimum required in `.env`**:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
MONGODB_URI=mongodb://localhost:27017
```

### 5. Start the Server
```bash
uvicorn app.main:app --reload
```

🎉 **That's it!** Your API is running at `http://localhost:8000`

Visit `http://localhost:8000/docs` for interactive API documentation.

---

## MongoDB Setup

### Option 1: Docker (Recommended)
```bash
docker run -d \
  --name iterate-mongo \
  -p 27017:27017 \
  mongo:7.0
```

### Option 2: Homebrew (macOS)
```bash
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

### Option 3: MongoDB Atlas (Cloud)
1. Sign up at https://www.mongodb.com/atlas
2. Create free cluster (M0)
3. Get connection string
4. Update `.env` with connection string

---

## First API Request

### Upload a Dataset

**Using curl**:
```bash
curl -X POST http://localhost:8000/upload-dataset \
  -F "file=@your_data.csv" \
  -F "user_instructions=Sample sales data"
```

**Using Python**:
```python
import requests

with open('your_data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload-dataset',
        files={'file': f},
        data={'user_instructions': 'Sample sales data'}
    )

dataset_id = response.json()['dataset_id']
print(f"Dataset uploaded: {dataset_id}")
```

### Analyze Dataset

```bash
curl -X POST http://localhost:8000/analyze-dataset \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "dataset_abc123",
    "user_instructions": "Focus on missing values",
    "run_code_investigations": true
  }'
```

---

## Project Structure

```
Iterate-Hackathon-Backend/
├── app/
│   ├── main.py              # FastAPI app & endpoints
│   ├── agent.py             # AI agent logic
│   ├── code_analysis.py     # Code execution
│   ├── chat.py              # Chat interface
│   ├── config.py            # Settings
│   ├── db.py                # MongoDB client
│   └── ...
├── data/                    # Dataset storage (auto-created)
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
└── README.md
```

---

## Development Workflow

### 1. Make Changes
Edit files in `app/` directory.

### 2. Auto-Reload
Server automatically reloads when you save files (thanks to `--reload` flag).

### 3. Test Changes
```bash
# Interactive docs
open http://localhost:8000/docs

# Make API request
curl http://localhost:8000/health
```

### 4. Run Tests
```bash
pytest

# With coverage
pytest --cov=app
```

---

## Common Tasks

### View Logs
```bash
# Server is already logging to stdout
# Add custom logging:
import logging
logger = logging.getLogger(__name__)
logger.info("Custom log message")
```

### Clear Uploaded Datasets
```bash
rm -rf data/dataset_*
```

### Clear Chat History
```bash
# Connect to MongoDB
mongosh

# Delete all messages
use chat_history
db.message_store.deleteMany({})
```

### Stop Server
Press `Ctrl+C` in terminal

### Deactivate Virtual Environment
```bash
deactivate
```

---

## Environment Variables Explained

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | - | Your Anthropic API key |
| `MONGODB_URI` | ✅ Yes | - | MongoDB connection string |
| `CLAUDE_MODEL` | ❌ No | `claude-haiku-4-5-20251001` | Model for agents |
| `AGENT_TIMEOUT_SECONDS` | ❌ No | `30.0` | Max time for agent calls |
| `AGENT_SAMPLE_ROWS` | ❌ No | `1000` | Rows sent to Claude |
| `AGENT_ENABLED` | ❌ No | `true` | Enable/disable AI agents |

**Full list**: See `.env.example` or [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Troubleshooting

### "ModuleNotFoundError"
```
Solution: Ensure virtual environment is activated
source venv/bin/activate
```

### "Connection refused" (MongoDB)
```
Solution: Start MongoDB
docker start iterate-mongo
# or
brew services start mongodb-community@7.0
```

### "Invalid API key"
```
Solution: Check ANTHROPIC_API_KEY in .env
echo $ANTHROPIC_API_KEY  # Should not be empty
```

### "Port already in use"
```
Solution: Use different port
uvicorn app.main:app --reload --port 8001
```

---

## Next Steps

1. **Read the docs**:
   - [Agent Architecture](docs/AGENT_ARCHITECTURE.md) - How AI agents work
   - [Code Execution](docs/CODE_EXECUTION.md) - Sandboxed Python execution
   - [API Reference](docs/API_REFERENCE.md) - Complete endpoint documentation

2. **Try the chat interface**:
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "test_session",
       "message": "Hello! What can you help me with?"
     }'
   ```

3. **Explore smart fixes**:
   Upload a dataset with quality issues and see the AI guide you through remediation.

4. **Integrate with frontend**:
   Connect to the React frontend (see `frontend/` directory).

---

## Getting Help

- **Documentation**: See `docs/` directory
- **API Docs**: http://localhost:8000/docs
- **Issues**: [GitHub Issues](#)
- **Examples**: See `tests/` for usage examples

---

**Happy Coding! 🚀**

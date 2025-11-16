# Documentation Index

Complete documentation for the Iterate Data Quality Analysis Platform - Backend

## 📚 Quick Links

- **[README.md](../README.md)** - Project overview and getting started
- **[Quickstart Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[API Reference](API_REFERENCE.md)** - Complete endpoint documentation
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions

## 🤖 AI Agent System Documentation

### Core Architecture
- **[Agent Architecture](AGENT_ARCHITECTURE.md)** - Comprehensive guide to the multi-agent system
  - Agent execution framework
  - Dataset Understanding Agent
  - Analysis Issues Agent
  - Code Execution Investigation Agent
  - Smart Fix Follow-up Agent
  - Error handling and fallbacks
  - Performance optimization
  - Testing strategies

### Code Execution
- **[Code Execution System](CODE_EXECUTION.md)** - Secure Python code execution
  - Anthropic's native sandbox integration
  - Token budget management
  - Code generation strategies
  - Security considerations
  - Use cases and examples
  - Performance characteristics

### Agent Contracts
- **[Agent Contracts](agent-contracts.md)** - Input/output schemas
  - Dataset Understanding schema
  - Analysis Issues schema
  - Smart Fix Follow-up schema
  - Contract validation

## 📖 User Guides

### For Developers

**Getting Started**:
1. [Quickstart Guide](QUICKSTART.md) - 5-minute setup
2. [README.md](../README.md) - Architecture overview
3. [API Reference](API_REFERENCE.md) - Endpoint documentation

**Development**:
- Local development setup
- Environment configuration
- Running tests
- Debugging techniques

**Advanced Topics**:
- [Agent Architecture](AGENT_ARCHITECTURE.md) - Understanding the AI system
- [Code Execution](CODE_EXECUTION.md) - How code investigations work
- Custom agent prompts
- Performance tuning

### For DevOps

**Deployment**:
1. [Deployment Guide](DEPLOYMENT.md) - Full deployment instructions
   - Docker deployment
   - AWS EC2 deployment
   - Azure App Service
   - Google Cloud Run

**Operations**:
- Monitoring and logging
- Health checks
- Scaling considerations
- Backup and recovery
- Security best practices

## 🔧 Technical Reference

### API Documentation
- **[API Reference](API_REFERENCE.md)** - Complete endpoint reference
  - Dataset management endpoints
  - AI agent endpoints
  - Chat interface
  - Smart fix workflows
  - Error responses

### Configuration
- **Environment Variables** - See [Deployment Guide](DEPLOYMENT.md#environment-configuration)
  - Required configuration
  - Optional tuning parameters
  - Security settings
  - Performance optimization

### Architecture
- **System Architecture** - See [README.md](../README.md#architecture)
  - Multi-agent pipeline
  - Technology stack
  - Agent guardrails
  - Data flow

## 📂 Project Structure

```
Iterate-Hackathon-Backend/
├── README.md                    # Project overview
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
│
├── app/                         # Application code
│   ├── main.py                  # FastAPI application
│   ├── agent.py                 # Agent execution framework
│   ├── code_analysis.py         # Code execution system
│   ├── chat.py                  # Chat interface
│   ├── tools.py                 # Code generation tools
│   ├── config.py                # Configuration
│   ├── db.py                    # Database client
│   ├── dataset_store.py         # File management
│   ├── backup_analysis.py       # Fallback heuristics
│   └── ...
│
├── docs/                        # Documentation
│   ├── README.md                # This file
│   ├── QUICKSTART.md            # 5-minute setup guide
│   ├── AGENT_ARCHITECTURE.md    # Agent system deep dive
│   ├── CODE_EXECUTION.md        # Code execution details
│   ├── API_REFERENCE.md         # API documentation
│   ├── DEPLOYMENT.md            # Deployment guide
│   └── agent-contracts.md       # Input/output schemas
│
├── data/                        # Dataset storage (gitignored)
├── scripts/                     # Generated analysis scripts
└── tests/                       # Test suite
```

## 🎯 Documentation by Use Case

### "I want to understand how the AI agents work"
→ Start with [Agent Architecture](AGENT_ARCHITECTURE.md)

### "I need to deploy to production"
→ Start with [Deployment Guide](DEPLOYMENT.md)

### "I'm integrating with the frontend"
→ Start with [API Reference](API_REFERENCE.md)

### "I want to run this locally"
→ Start with [Quickstart Guide](QUICKSTART.md)

### "I need to understand code execution"
→ Start with [Code Execution System](CODE_EXECUTION.md)

### "I want to see example API calls"
→ See [API Reference](API_REFERENCE.md) examples

### "I'm debugging an agent issue"
→ See [Agent Architecture](AGENT_ARCHITECTURE.md#error-handling--fallbacks)

### "I need to optimize performance"
→ See [Agent Architecture](AGENT_ARCHITECTURE.md#performance-optimization) and [Deployment Guide](DEPLOYMENT.md#scaling-considerations)

## 🔍 Key Concepts

### Multi-Agent Architecture
The system uses **specialized AI agents** for different tasks:
- **Understanding Agent**: Analyzes dataset structure and business context
- **Analysis Agent**: Detects quality issues and categorizes them
- **Investigation Agent**: Generates and executes Python code to validate hypotheses
- **Follow-up Agent**: Guides users through complex remediation decisions

See: [Agent Architecture](AGENT_ARCHITECTURE.md)

### Code Execution
Agents can generate and execute **Python pandas scripts** in a secure sandbox to:
- Validate hypotheses with real data
- Calculate custom metrics
- Extract specific evidence
- Analyze complex patterns

See: [Code Execution System](CODE_EXECUTION.md)

### Smart Fixes
Issues requiring business judgment trigger **conversational workflows**:
1. User selects a smart fix issue
2. Agent asks contextual questions
3. User provides answers
4. Agent generates tailored remediation code

See: [API Reference](API_REFERENCE.md#smart-fix-workflows)

### Agent Guardrails
Production-ready safety mechanisms:
- **Timeout protection**: 30-second default limit
- **Retry logic**: Automatic retry with backoff
- **Schema validation**: Pydantic models enforce structure
- **Token budgeting**: Prevents context overflow
- **Fallback strategies**: Rule-based heuristics when agents fail

See: [Agent Architecture](AGENT_ARCHITECTURE.md#agent-execution-framework)

## 📊 Decision Trees

### Which Documentation Should I Read?

```
Are you...
├─ Setting up for the first time?
│  └─ → Quickstart Guide
│
├─ Deploying to production?
│  └─ → Deployment Guide
│
├─ Building a frontend integration?
│  └─ → API Reference
│
├─ Understanding the AI system?
│  ├─ High-level overview?
│  │  └─ → README.md (Architecture section)
│  ├─ Agent implementation details?
│  │  └─ → Agent Architecture
│  └─ Code execution specifics?
│     └─ → Code Execution System
│
└─ Debugging an issue?
   ├─ Agent timeout/failure?
   │  └─ → Agent Architecture (Error Handling)
   ├─ API error?
   │  └─ → API Reference (Error Responses)
   └─ Deployment issue?
      └─ → Deployment Guide (Troubleshooting)
```

## 🛠️ Development Resources

### Code Examples

**Upload and Analyze**:
```python
import requests

# Upload dataset
with open('data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload-dataset',
        files={'file': f},
        data={'user_instructions': 'Sales data Q3 2024'}
    )
dataset_id = response.json()['dataset_id']

# Run analysis
analysis = requests.post(
    'http://localhost:8000/analyze-dataset',
    json={
        'dataset_id': dataset_id,
        'run_code_investigations': True
    }
)
print(analysis.json())
```

**Chat Interface**:
```python
response = requests.post(
    'http://localhost:8000/chat',
    json={
        'session_id': 'user_123',
        'message': 'What quality issues did you find?',
        'dataset_id': dataset_id
    }
)
print(response.json()['reply'])
```

More examples: [API Reference](API_REFERENCE.md)

### Testing

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

See: [Agent Architecture](AGENT_ARCHITECTURE.md#testing-strategies)

## 🔒 Security

### Best Practices
- Store API keys in environment variables
- Use HTTPS in production
- Implement rate limiting
- Validate all user inputs
- Use Anthropic's native sandbox for code execution

See: [Deployment Guide](DEPLOYMENT.md#security)

### Data Privacy
- Code execution in secure sandbox (no network/filesystem)
- No data persistence after execution
- Encrypted API transmission
- Chat history isolated by session

See: [Code Execution System](CODE_EXECUTION.md#security-considerations)

## 📈 Performance

### Optimization Strategies
- Token budget management for large datasets
- Parallel code investigations
- Caching dataset understanding results
- Async execution for non-blocking I/O

See: [Agent Architecture](AGENT_ARCHITECTURE.md#performance-optimization)

### Scaling
- Vertical scaling: Increase CPU/RAM
- Horizontal scaling: Load-balanced instances
- Database scaling: MongoDB sharding/replicas
- Caching layer: Redis for metadata

See: [Deployment Guide](DEPLOYMENT.md#scaling-considerations)

## 🚧 Future Roadmap

- [ ] Multi-tenant support
- [ ] Advanced time-series analysis agents
- [ ] Auto-remediation for common issues
- [ ] Vector search for semantic similarity
- [ ] WebSocket streaming for real-time updates
- [ ] Custom validation rules DSL
- [ ] Redis caching layer

See: [README.md](../README.md#roadmap)

## 📞 Support

### Getting Help
- **Documentation**: You're reading it!
- **API Docs**: http://localhost:8000/docs (interactive)
- **GitHub Issues**: [Link to issues]
- **Examples**: See `tests/` directory

### Contributing
See contribution guidelines (coming soon)

---

## Document Index

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](../README.md) | Project overview, quick start | All users |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide | Developers |
| [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) | Deep dive into AI agents | Developers, ML Engineers |
| [CODE_EXECUTION.md](CODE_EXECUTION.md) | Code execution system | Developers, Security |
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API documentation | Frontend Developers |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment | DevOps, SRE |
| [agent-contracts.md](agent-contracts.md) | Input/output schemas | Developers, QA |

---

**Documentation Version**: 1.0  
**Last Updated**: 2025-11-16  
**Maintained By**: Backend Team

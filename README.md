# README - AI Talent Advisor

## 🎯 Project Overview

The **AI Talent Advisor** is an end-to-end intelligence system for university campus hiring. It uses retrieval-augmented generation (RAG), prompt chaining, and multimodal enrichment to help university placement cells efficiently identify and prepare top student candidates for company interviews.

### Key Capabilities

- 🔍 **RAG-Powered Search**: Query student profiles with natural language questions
- 🤖 **Intelligent Ranking**: Score students using AI based on job requirements
- 📝 **Auto-Generated Artifacts**: Create interview questions and outreach emails
- 🎓 **Media Enrichment**: Incorporate certificates and portfolios into profiles
- 📊 **Transparent Citations**: Every answer references source resume chunks
- 🚀 **Production-Ready**: Local deployment with zero API dependencies (mock mode)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- ~2GB disk space

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd ai-talent-advisor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (optional - defaults work)
cp .env.example .env
```

### Running the Application

```bash
# Start API server
python -m app.main

# Server will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## 📖 Usage Examples

### 1. Ingest Student Resumes

```bash
curl -X POST http://localhost:8000/api/rag/ingest
```

### 2. Query for Candidates

```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Find Python developers with AWS experience",
    "job_description": "Senior Backend Engineer",
    "company_name": "TechCorp"
  }'
```

### 3. Run Full Hiring Workflow

```bash
curl -X POST http://localhost:8000/api/orchestration/company-hiring \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TechCorp",
    "job_title": "Senior Software Engineer",
    "job_description": "5+ years experience with Python, React, AWS",
    "max_candidates": 5
  }'
```

### 4. Upload Student Certificate

```bash
curl -X POST http://localhost:8000/api/resumes/upload-media \
  -F "file=@certificate.png" \
  -F "student_id=student_001" \
  -F "media_type=certificate"
```

## 📁 Project Structure

```
ai-talent-advisor/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── api/                    # API endpoints
│   │   ├── rag_routes.py      # RAG endpoints
│   │   ├── orchestration_routes.py
│   │   └── multimodal_routes.py
│   ├── core/                   # Core utilities
│   │   ├── config.py          # Configuration
│   │   ├── models.py          # Pydantic models
│   │   └── observability.py   # Logging & metrics
│   ├── rag/                    # RAG pipeline
│   │   ├── ingestion.py       # PDF loading
│   │   ├── chunking.py        # Text chunking
│   │   ├── vector_store.py    # FAISS wrapper
│   │   └── pipeline.py        # RAG orchestration
│   ├── orchestration/          # Prompt chaining
│   │   ├── llm_client.py      # LLM interface
│   │   ├── prompts.py         # Prompt templates
│   │   └── chain.py           # Chain orchestration
│   └── multimodal/             # Media enrichment
│       ├── media.py           # Media processing
│       └── enrichment.py      # Integration
├── tests/                      # Test suite
│   ├── test_rag.py
│   ├── test_orchestration.py
│   ├── test_multimodal.py
│   └── test_integration.py
├── docs/                       # Documentation
│   ├── solution_advanced.md   # Technical deep-dive
│   ├── prompts.md            # Prompt templates
│   └── ai_assistance.md      # AI usage disclosure
├── student_profiles/          # Synthetic resumes
│   └── synthetic_student_*.pdf
├── data/                       # Generated data
│   ├── faiss_index.faiss     # Vector store
│   └── metadata.json         # Chunk metadata
├── requirements.txt
├── .env.example
└── README.md
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_integration.py -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
```

### Test Coverage

- ✅ RAG retrieval and chunking
- ✅ Prompt chaining orchestration
- ✅ Media upload (success & failure paths)
- ✅ End-to-end hiring workflow
- ✅ Error handling & edge cases

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# LLM
OPENAI_API_KEY=your_key_here  # Optional for production
USE_MOCK_LLM=true             # Use mock by default

# Embedding
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
USE_MOCK_EMBEDDINGS=false

# Vision (for media)
USE_MOCK_VISION=true          # Use mock OCR by default

# RAG
CHUNK_SIZE=512
TOP_K_RETRIEVAL=5

# Paths
STUDENT_PROFILES_PATH=./student_profiles
DATA_PATH=./data
```

## 📊 API Documentation

### Available Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/rag/ingest` | Ingest student resumes |
| POST | `/api/rag/query` | Query student database |
| GET | `/api/rag/health` | RAG health check |
| POST | `/api/orchestration/company-hiring` | Full hiring workflow |
| GET | `/api/orchestration/health` | Orchestration health |
| POST | `/api/resumes/upload-media` | Upload certificate/portfolio |
| GET | `/api/resumes/health` | Multimodal health check |

### Full API Documentation

Visit `http://localhost:8000/docs` (Swagger UI) or `/redoc` (ReDoc) for interactive documentation.

## 🎓 Data & Privacy

- **Synthetic Data**: Provided resumes are 100% synthetic (no real student data)
- **Local Processing**: All data stays on your machine by default
- **No Cloud Calls**: Mock mode uses no external APIs
- **Easy Redaction**: To use production APIs, see `.env.example`

## 🔧 Production Deployment

### Docker

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

```bash
docker build -t ai-talent-advisor .
docker run -p 8000:8000 ai-talent-advisor
```

### With Real APIs

```bash
# Edit .env
OPENAI_API_KEY=sk-...
USE_MOCK_LLM=false

# Also update embedding model if needed
EMBEDDING_MODEL=text-embedding-3-small

# Restart server
python -m app.main
```

## 📚 Documentation

- [**solution_advanced.md**](docs/solution_advanced.md): Architecture, design, and technical deep-dive
- [**prompts.md**](docs/prompts.md): All prompts used with examples and rationale
- [**ai_assistance.md**](docs/ai_assistance.md): AI tool usage disclosure
- [**API Docs**](http://localhost:8000/docs): Interactive Swagger UI

## 🎯 Key Features

### 1. Retrieval-Augmented Generation (RAG)
- Ingest PDFs from `student_profiles/`
- Chunk with 512-token context windows
- FAISS vector store with semantic search
- Grounded answers with chunk citations

### 2. Prompt Chaining
- **Stage 1**: Role summary generation
- **Stage 2**: Candidate retrieval & ranking (0-100 score)
- **Stage 3**: Interview question generation (3 per student)
- **Stage 4**: Outreach email creation

### 3. Multimodal Enrichment
- Upload certificates/portfolios as images
- Extract text via mock OCR (or real pytesseract/API)
- Tag skills automatically
- Integrate into RAG for searchability

### 4. Observability
- Latency tracking per stage
- Token counting
- Full execution logs
- Metrics in every response

## 🚦 Performance

Typical latencies:
- Resume ingest: 150-300ms
- RAG query: 100-200ms
- LLM completion: 1000-3000ms (mock: <100ms)
- Full orchestration: 5-8 seconds

## 🐛 Troubleshooting

### Issue: "No module named 'app'"
**Solution**: Run from project root directory
```bash
cd ai-talent-advisor
python -m app.main
```

### Issue: No chunks indexed
**Solution**: Call `/api/rag/ingest` first
```bash
curl -X POST http://localhost:8000/api/rag/ingest
```

### Issue: Embedding model download takes time
**Solution**: First run downloads `sentence-transformers` model (~70MB). Subsequent runs are instant.

### Issue: Out of memory with large datasets
**Solution**: Increase `CHUNK_SIZE` in `.env` to reduce total chunks
```bash
CHUNK_SIZE=1024  # Larger chunks = fewer total chunks
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is provided as-is for educational and research purposes.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Vector search via [FAISS](https://github.com/facebookresearch/faiss)
- Embeddings from [Sentence Transformers](https://www.sbert.net/)
- LLM integration with [OpenAI](https://openai.com/)

## 📧 Contact & Support

For issues, questions, or suggestions:
1. Check [docs/solution_advanced.md](docs/solution_advanced.md)
2. Review [docs/ai_assistance.md](docs/ai_assistance.md) for implementation details
3. Run tests: `pytest tests/ -v`
4. Check logs for error messages

## 🗺️ Roadmap

- [ ] Fine-tuned embedding model on resume data
- [ ] Distributed FAISS for large-scale deployment
- [ ] Real-time resume updates and notifications
- [ ] Interview feedback loop for continuous improvement
- [ ] Bias detection and mitigation
- [ ] Multi-language support
- [ ] Web UI for recruiters

---

**Version**: 1.0.0  
**Last Updated**: June 2024  
**Status**: Production-Ready (Mock Mode) / Ready for Production APIs

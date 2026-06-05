# AI Talent Advisor - Solution & Technical Documentation

## Overview

The AI Talent Advisor is an end-to-end intelligence system designed for university campus hiring. It leverages retrieval-augmented generation (RAG), prompt chaining, and multimodal enrichment to enable recruiters to efficiently identify and prepare students for interview lists across multiple companies.

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           API Layer (FastAPI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  RAG Routes  │  │ Orchestration│  │  Multimodal  │              │
│  │   /api/rag   │  │  /api/orch   │  │  /api/resume │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
         │                    │                      │
┌─────────────────────────────────────────────────────────────────────┐
│                      Core Processing Layers                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │  RAG Pipeline    │  │ Prompt Chain     │  │  Multimodal    │   │
│  │ - Ingestion      │  │ - Role Summary   │  │ - Media Proc   │   │
│  │ - Chunking       │  │ - Scoring        │  │ - OCR/Vision   │   │
│  │ - Vector Store   │  │ - Questions      │  │ - Enrichment   │   │
│  │ - Retrieval      │  │ - Outreach       │  │ - Integration  │   │
│  └──────────────────┘  └──────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
         │                                             │
┌─────────────────────────────────────────────────────────────────────┐
│                      Data & Integration Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ FAISS Index  │  │  LLM Client  │  │ File Storage │              │
│  │ (Vector DB)  │  │  (OpenAI)    │  │ (PDFs, Media)│              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. RAG Pipeline (`app/rag/`)

#### Ingestion (`ingestion.py`)
- **Purpose**: Extract text from PDF resumes
- **Implementation**: Uses PyPDF2 for PDF parsing
- **Process**: 
  1. Scan `student_profiles/` directory
  2. Extract text from each PDF
  3. Parse student ID from filename
  4. Pass to chunking stage

#### Chunking (`chunking.py`)
- **Purpose**: Split texts into semantically meaningful chunks
- **Configuration**:
  - `chunk_size`: 512 tokens (configurable)
  - `chunk_overlap`: 50 tokens (for context preservation)
- **Skill Extraction**: Heuristic-based extraction of 30+ common technical skills
- **Metadata**: Each chunk stores:
  - `chunk_id`: Unique identifier
  - `student_id`: Source student
  - `source_type`: 'resume' or 'media'
  - `skills`: Extracted skill tags

#### Vector Store (`vector_store.py`)
- **Backend**: FAISS (Local in-memory with disk persistence)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- **Index Type**: FlatL2 (exhaustive search for accuracy)
- **Persistence**: 
  - Index: `data/faiss_index.faiss`
  - Metadata: `data/metadata.json`
- **Search**: L2 distance-based retrieval with similarity score conversion

#### Retrieval (`pipeline.py`)
- **Query Processing**: Combines query + job description for better context
- **Top-K Retrieval**: Configurable (default: 5 results)
- **Grounding**: Answers synthesized directly from retrieved chunks
- **Citation**: Each answer includes chunk IDs for traceability
- **Observability**: Latency, token counts, and retrieval metrics logged

### 2. Prompt Chaining Orchestration (`app/orchestration/`)

#### Chain Flow

```
1. ROLE SUMMARY GENERATION
   └─> LLM synthesizes role requirements
   └─> 2-3 sentence summary

2. CANDIDATE RETRIEVAL & SCORING  
   └─> RAG queries for matching students
   └─> LLM scores each candidate (0-100)
   └─> Rank and filter top N

3. INTERVIEW QUESTION GENERATION
   ├─> Q1: Technical question (tied to resume evidence)
   ├─> Q2: Experience question (behavioral)
   └─> Q3: Problem-solving question

4. OUTREACH EMAIL CREATION
   └─> Personalized 150-250 word email
   └─> References specific resume highlights
   └─> Clear CTA for interview scheduling
```

#### LLM Client (`llm_client.py`)
- **Mode**: Dual-mode (Production + Mock)
  - **Production**: OpenAI GPT-3.5-turbo API (requires `OPENAI_API_KEY`)
  - **Mock**: Deterministic responses for testing (always enabled by default)
- **Features**:
  - Automatic fallback to mock if API fails
  - Token counting for observability
  - Configurable via `.env` (`USE_MOCK_LLM=true/false`)

#### Prompt Templates (`prompts.py`)
- 5 main prompt templates:
  1. `ROLE_SUMMARY_PROMPT`: Generates job summary
  2. `STUDENT_SCORING_PROMPT`: Evaluates candidate fit
  3. `INTERVIEW_QUESTION_PROMPT`: Generates 3 contextual questions
  4. `OUTREACH_EMAIL_PROMPT`: Creates personalized email
  5. `SCORECARD_PROMPT`: Comprehensive evaluation

#### Chain Orchestrator (`chain.py`)
- **Main Method**: `orchestrate_company_hiring()`
- **Inputs**:
  - `company_name`: Hiring company
  - `job_description`: Detailed job requirements
  - `job_title`: Position title
  - `max_candidates`: Number of top candidates to process
- **Outputs**: `ChainOrchestrationResponse` with:
  - Role summary
  - Top 5 ranked students (with scores)
  - 3 interview questions per student
  - Personalized outreach email per student
  - Full execution metrics

### 3. Multimodal Enrichment (`app/multimodal/`)

#### Media Processing (`media.py`)

**Workflow**:
```
Image Upload
    ↓
Validation (PNG/JPG)
    ↓
Storage (data/media/)
    ↓
OCR/Vision Processing
    ↓
Text Extraction
    ↓
Skill Tag Extraction
    ↓
Metadata Generation
```

**Vision Client Features**:
- **Mode**: Mock by default (`USE_MOCK_VISION=true`)
- **Real Options** (in `config.py`):
  - OpenAI Vision API (GPT-4 Vision)
  - Google Cloud Vision API
  - pytesseract (local OCR)
- **Mock OCR**: Deterministic extraction based on media type
  - Certificates → Extracts course names, skills, dates
  - Portfolio → Extracts project descriptions, technologies

#### Skill Tag Extraction
Maps extracted text to 9+ skill categories:
- Machine Learning / TensorFlow / Keras
- Python / Pandas / NumPy
- React / JavaScript
- Node.js / Express
- AWS / Cloud
- Database / SQL
- FullStack Development
- DevOps / Docker / Kubernetes
- API Design / Microservices

#### Enrichment Orchestrator (`enrichment.py`)
- **Integration**: Automatically adds media chunks to RAG vector store
- **Flow**:
  1. Process image → Extract text
  2. Chunk extracted text with media metadata
  3. Generate embeddings
  4. Add to FAISS index
  5. Chunks become searchable in RAG queries
- **Citation**: Media-sourced information explicitly marked in results

### 4. API Layer (`app/api/`)

#### RAG Endpoints (`rag_routes.py`)
- `POST /api/rag/ingest`: Ingest all resumes from `student_profiles/`
- `POST /api/rag/query`: Query with question, optional job description
  - Request: `RAGQuery` (question, job_description, company_name, top_k)
  - Response: `RAGResponse` (answer, cited_chunks, metrics)
- `GET /api/rag/health`: Health check

#### Orchestration Endpoints (`orchestration_routes.py`)
- `POST /api/orchestration/company-hiring`: Full hiring workflow
  - Request: `ChainOrchestrationRequest`
  - Response: `ChainOrchestrationResponse`
- `GET /api/orchestration/health`: Health check

#### Multimodal Endpoints (`multimodal_routes.py`)
- `POST /api/resumes/upload-media`: Upload certificate/portfolio
  - Accepts: Image file (PNG/JPG) + metadata
  - Response: Extracted text, tags, success status
- `GET /api/resumes/health`: Health check

### 5. Core Utilities

#### Config (`app/core/config.py`)
- Pydantic-based settings from `.env`
- Feature flags for mock vs production
- Path configuration for data storage

#### Observability (`app/core/observability.py`)
- `ChainStep`: Context manager for logging chain execution
- `QueryMetrics`: Collects latency, token counts, step timings
- All responses include `metrics` dict with observability data

#### Models (`app/core/models.py`)
- Pydantic models for type safety:
  - Request: `RAGQuery`, `ChainOrchestrationRequest`, `MediaUploadRequest`
  - Response: `RAGResponse`, `ChainOrchestrationResponse`, `MediaUploadResponse`

## Prompt Design & Grounding

### Design Philosophy
1. **Specificity**: Prompts include structured context (job description, resume excerpts)
2. **Composability**: Each prompt solves one specific problem in the chain
3. **Debuggability**: LLM outputs parsed and validated before use
4. **Fallback**: All LLM calls have sensible defaults if parsing fails

### Grounding Approach
- **RAG Grounding**: All answers reference specific resume chunks
- **Citation Format**: `chunk_id` (e.g., `student_001_chunk_3`)
- **Evidence Linking**: Interview questions tied to resume evidence
- **Transparency**: Users can inspect source material for each claim

## Data Flow: Multimodal Integration

```
Certificate Upload
    ↓ (multimodal_routes.py)
MediaProcessor.process_image()
    ├─→ Validate & store image
    ├─→ Extract text via OCR
    └─→ Extract skill tags
    ↓
TextChunker.chunk_text()
    ├─→ Create chunks with media metadata
    └─→ Chunk ID format: `student_id_chunk_N`
    ↓
RAG Vector Store
    ├─→ Generate embeddings
    ├─→ Add to FAISS index
    └─→ Store metadata with source='media'
    ↓
RAG Queries
    └─→ Results now include media-sourced citations
```

## Local Setup & Deployment

### Prerequisites
- Python 3.8+
- pip or conda
- ~2GB free disk space (for models & data)

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/ai-talent-advisor.git
cd ai-talent-advisor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings (optional OpenAI key)
```

### Running the Application

```bash
# Option 1: Direct execution
python -m app.main

# Option 2: Using Uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Server will start at http://localhost:8000
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ app/
COPY student_profiles/ student_profiles/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t ai-talent-advisor .
docker run -p 8000:8000 -v $(pwd)/data:/app/data ai-talent-advisor
```

## Sample Requests & Responses

### 1. Ingest Resumes

```bash
curl -X POST http://localhost:8000/api/rag/ingest
```

**Response**:
```json
{
  "status": "success",
  "message": "Student resumes ingested successfully"
}
```

### 2. RAG Query

```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Find developers with Python and AWS experience",
    "job_description": "Senior backend engineer with cloud expertise",
    "company_name": "TechCorp",
    "top_k": 5
  }'
```

**Response**:
```json
{
  "answer": "Based on student profiles, here are relevant candidates:\n• Student 001:\n  - 5+ years Python experience with Django and Flask...\n• Student 002:\n  - AWS certified architect with microservices background...",
  "cited_chunks": [
    {
      "chunk_id": "student_001_chunk_0",
      "content": "5+ years of full-stack development experience...",
      "source_type": "resume",
      "student_id": "student_001",
      "metadata": {
        "skills": ["python", "aws", "django"],
        "source_file": "synthetic_student_001.pdf"
      }
    }
  ],
  "metrics": {
    "total_latency_ms": 145.3,
    "total_tokens": 320,
    "retrieval_time_ms": 23.5,
    "steps": {}
  }
}
```

### 3. Company Hiring Orchestration

```bash
curl -X POST http://localhost:8000/api/orchestration/company-hiring \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TechCorp",
    "job_title": "Senior Software Engineer",
    "job_description": "5+ years full-stack experience with Python, React, and AWS",
    "max_candidates": 3
  }'
```

**Response**:
```json
{
  "company_name": "TechCorp",
  "job_title": "Senior Software Engineer",
  "role_summary": "This is a challenging senior software engineering role requiring 5+ years of experience in full-stack development...",
  "top_students": [
    {
      "student_id": "student_001",
      "student_name": "Student 001",
      "company_name": "TechCorp",
      "job_title": "Senior Software Engineer",
      "score": 85,
      "match_reasons": ["Strong Python background", "AWS certified", "React expertise"],
      "interview_questions": [
        {
          "question_text": "Tell us about your experience with cloud platforms...",
          "evidence_citation": "student_001_chunk_0",
          "difficulty": "medium"
        }
      ],
      "outreach_email": "Subject: Exciting Senior Engineer Opportunity at TechCorp\n\nDear Student 001,\n\nWe are impressed by your background in full-stack development..."
    }
  ],
  "metrics": {
    "total_latency_ms": 2340.5,
    "total_tokens": 4500,
    "company": "TechCorp",
    "job_title": "Senior Software Engineer",
    "total_students": 3
  }
}
```

### 4. Media Upload

```bash
curl -X POST http://localhost:8000/api/resumes/upload-media \
  -F "file=@certificate.png" \
  -F "student_id=student_001" \
  -F "media_type=certificate" \
  -F "description=AWS Solutions Architect Certification"
```

**Response**:
```json
{
  "media_id": "a1b2c3d4-e5f6-4g7h-8i9j-0k1l2m3n4o5p",
  "student_id": "student_001",
  "media_type": "certificate",
  "extracted_text": "CERTIFICATE OF COMPLETION\nAdvanced Machine Learning with TensorFlow...",
  "tags": ["machine learning", "tensorflow", "python"],
  "status": "success"
}
```

## Configuration Reference

### `.env` File

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | (empty) | OpenAI API key (optional, uses mock if empty) |
| `LLM_MODEL` | gpt-3.5-turbo | Model for LLM calls |
| `USE_MOCK_LLM` | true | Enable mock LLM (no API calls) |
| `EMBEDDING_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | Embedding model |
| `USE_MOCK_EMBEDDINGS` | false | Use mock embeddings |
| `USE_MOCK_VISION` | true | Enable mock vision (no API calls) |
| `RAG_BACKEND` | faiss | Vector store backend |
| `CHUNK_SIZE` | 512 | Text chunk size in tokens |
| `CHUNK_OVERLAP` | 50 | Overlap between chunks |
| `TOP_K_RETRIEVAL` | 5 | Default top-K for search |
| `STUDENT_PROFILES_PATH` | ./student_profiles | Resume directory |
| `DATA_PATH` | ./data | Data storage directory |
| `DEBUG` | true | Debug mode |

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_rag.py -v

# Specific test
pytest tests/test_integration.py::test_end_to_end_hiring_workflow -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Coverage

- **test_rag.py**: RAG pipeline (chunking, FAISS, retrieval)
- **test_orchestration.py**: Prompt chaining (LLM, scoring, questions)
- **test_multimodal.py**: Media processing (upload, OCR, enrichment)
- **test_integration.py**: End-to-end workflows

## Performance & Optimization

### Latency Breakdown (Typical)
- Ingest resume: 150-300ms
- RAG query: 100-200ms
- LLM completion: 1000-3000ms
- Full orchestration: 5000-8000ms

### Optimization Strategies
1. **Batch Processing**: Process multiple queries together
2. **Caching**: Cache embeddings and frequent queries
3. **Index Size**: Periodically prune old chunks
4. **Async Processing**: Use async endpoints for long operations

### Scaling
- **Vertical**: Increase chunk size, embedding model
- **Horizontal**: Distribute FAISS index across machines
- **Cloud**: Deploy to AWS/GCP with auto-scaling

## Known Limitations & Future Work

### Current Limitations
1. Mock LLM provides fixed responses (production requires OpenAI key)
2. Mock vision extracts text via rules (real OCR requires pytesseract or API)
3. FAISS index not distributed (suitable for <10M chunks)
4. No fine-tuning of embedding models

### Future Enhancements
1. Custom embedding model fine-tuned on resume data
2. Distributed FAISS with IVF indexing
3. Real-time resume updates
4. Interview feedback loop
5. Bias detection & mitigation
6. Multi-language support

## Observability & Debugging

### Logging
All components log to console in format:
```
YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - message
[CHAIN_STEP] Starting: step_name
[METADATA] key=value pairs
```

### Metrics
Every API response includes `metrics` dict:
```json
{
  "total_latency_ms": 1234.5,
  "total_tokens": 450,
  "embedding_calls": 2,
  "retrieval_time_ms": 23.4,
  "steps": {}
}
```

### Debugging Tips
1. Check `.env` configuration
2. Verify `student_profiles/` has PDF files
3. Inspect `data/metadata.json` for indexed chunks
4. Enable logging in `app/core/observability.py`
5. Use `/health` endpoints for service status

## Privacy & Security

### Data Handling
- **Local Storage**: All data stored locally in `data/` and `student_profiles/`
- **No Cloud Upload**: By default, uses mock LLM/Vision (no API calls)
- **Synthetic Data**: Provided PDFs are synthetic (no real student data)

### Production Considerations
- Redact API keys from version control (use `.env`)
- Encrypt sensitive data at rest
- Use HTTPS for API endpoints
- Implement rate limiting
- Add authentication/authorization
- Audit all data access

## References

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Timeline & Effort

- **Actual Time Spent**: 6-8 hours (estimated)
- **Development Phases**:
  1. Architecture & Setup: 1h
  2. RAG Pipeline: 2h
  3. Orchestration: 1.5h
  4. Multimodal: 1h
  5. API & Tests: 1.5h
  6. Documentation: 1h

---

**Last Updated**: June 2024
**Version**: 1.0.0

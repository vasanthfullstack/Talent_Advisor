# RUNBOOK - Operations & Deployment Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Daily Operations](#daily-operations)
3. [Monitoring & Debugging](#monitoring--debugging)
4. [Scaling & Performance](#scaling--performance)
5. [Backup & Recovery](#backup--recovery)

---

## Quick Start

### Installation (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/ai-talent-advisor.git
cd ai-talent-advisor

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment (optional)
cp .env.example .env
# Edit .env if you want to use real APIs, otherwise defaults are mock

# 5. Start server
python -m app.main
```

**Server is now running at http://localhost:8000**

### First Run Checklist

- [ ] Server starts without errors
- [ ] Visit http://localhost:8000/docs to see API documentation
- [ ] Run health checks:
  ```bash
  curl http://localhost:8000/health
  curl http://localhost:8000/api/rag/health
  curl http://localhost:8000/api/orchestration/health
  curl http://localhost:8000/api/resumes/health
  ```
- [ ] All show `"status": "healthy"`

---

## Daily Operations

### 1. Ingesting New Student Resumes

**Add new PDF to `student_profiles/` folder:**

```bash
# Copy resume to folder (filename format: synthetic_student_XXX.pdf)
cp john_smith_resume.pdf student_profiles/synthetic_student_006.pdf

# Trigger ingestion
curl -X POST http://localhost:8000/api/rag/ingest

# Verify ingestion
curl http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Find developers with relevant skills",
    "top_k": 10
  }'
```

**Expected Response**: Should include chunks from newly added resume

### 2. Querying for Candidates

**Basic query:**

```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Find Python developers",
    "job_description": "Senior Python developer needed",
    "company_name": "MyCompany"
  }'
```

**Response includes**:
- Grounded answer with synthesis of relevant resumes
- Cited chunks with source information
- Metrics (latency, tokens, etc.)

### 3. Running Full Hiring Workflow

**For each company + role:**

```bash
curl -X POST http://localhost:8000/api/orchestration/company-hiring \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TechCorp",
    "job_title": "Senior Software Engineer",
    "job_description": "5+ years experience with Python, React, and AWS. Must have experience with microservices.",
    "max_candidates": 5
  }'
```

**This returns**:
- Role summary (1 per company/role)
- Top 5 ranked students with scores
- 3 interview questions per student (tied to resume evidence)
- Personalized outreach email per student
- Full metrics for each stage

**Save output to file:**

```bash
curl -X POST http://localhost:8000/api/orchestration/company-hiring \
  -H "Content-Type: application/json" \
  -d '{"company_name":"TechCorp","job_title":"Engineer","job_description":"...","max_candidates":5}' \
  > techcorp_hiring_results.json
```

### 4. Enriching Student Profiles with Media

**Upload certificate:**

```bash
curl -X POST http://localhost:8000/api/resumes/upload-media \
  -F "file=@aws_cert.png" \
  -F "student_id=student_001" \
  -F "media_type=certificate" \
  -F "description=AWS Solutions Architect Certification"
```

**Upload portfolio:**

```bash
curl -X POST http://localhost:8000/api/resumes/upload-media \
  -F "file=@portfolio_screenshot.jpg" \
  -F "student_id=student_001" \
  -F "media_type=portfolio" \
  -F "description=Personal portfolio with projects"
```

**Verification**: Run RAG query - results should now include text extracted from media

---

## Monitoring & Debugging

### 1. Check Server Health

```bash
# All services
curl http://localhost:8000/health

# Individual services
curl http://localhost:8000/api/rag/health
curl http://localhost:8000/api/orchestration/health
curl http://localhost:8000/api/resumes/health
```

### 2. Monitor Logs

**Console logs** (when running in terminal):
- Look for `[CHAIN_STEP]` entries for stage tracking
- Look for `[METADATA]` entries for performance metrics
- Errors prefixed with `ERROR:` in red

**Log important outputs**:

```bash
# Save logs to file
python -m app.main > server.log 2>&1 &

# Monitor in real-time
tail -f server.log
```

### 3. Verify Data

**Check what's indexed:**

```bash
# Query metadata
python3 -c "
import json
with open('data/metadata.json') as f:
    metadata = json.load(f)
    print(f'Total chunks indexed: {len(metadata)}')
    print(f'Unique students: {len(set(m[\"metadata\"][\"student_id\"] for m in metadata))}')
    for m in metadata[:3]:
        print(f'  - {m[\"chunk_id\"]}: {m[\"content\"][:50]}...')
"
```

### 4. Run Diagnostic Queries

```bash
# Test RAG with simple query
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Any developers available?"}'

# Test orchestration with minimal input
curl -X POST http://localhost:8000/api/orchestration/company-hiring \
  -H "Content-Type: application/json" \
  -d '{
    "company_name":"Test",
    "job_title":"Any",
    "job_description":"Any role",
    "max_candidates":1
  }'
```

### 5. Troubleshooting Common Issues

**Issue: "No module found"**
```bash
# Ensure you're in project root and venv is activated
pwd  # Should show ai-talent-advisor directory
which python  # Should show path inside venv/
```

**Issue: "Index not found" or empty results**
```bash
# Re-ingest resumes
curl -X POST http://localhost:8000/api/rag/ingest

# Verify chunks were created
python3 -c "import json; chunks=json.load(open('data/metadata.json')); print(f'Indexed {len(chunks)} chunks')"
```

**Issue: Slow responses**
```bash
# Check metrics in response - look for:
# - high "total_latency_ms" (> 10000ms for orchestration is normal with LLM)
# - high "token" counts (reduce with CHUNK_SIZE)

# Reduce chunk size for faster indexing (at cost of less context)
# Edit .env: CHUNK_SIZE=256
```

**Issue: Memory usage increasing**
```bash
# Monitor memory
while true; do ps aux | grep python | grep app.main; sleep 2; done

# If memory grows unbounded:
# 1. Restart server
# 2. Check for memory leaks in vector store
# 3. Reduce TOP_K_RETRIEVAL in .env
```

---

## Scaling & Performance

### Performance Baseline

| Operation | Duration | Notes |
|-----------|----------|-------|
| Ingest 5 resumes | 500-1000ms | One-time |
| RAG query | 100-500ms | FAISS search |
| LLM completion | 1000-3000ms | Network + inference |
| Full orchestration | 5-8 seconds | 4 sequential LLM calls |

### Optimization Tips

**1. Reduce Token Usage**
```bash
# In .env, reduce chunk size:
CHUNK_SIZE=256  # Default 512

# Reduces from ~200 chunks to ~100
# Faster retrieval, less context per chunk
```

**2. Batch Processing**
```python
# Send multiple queries in parallel
import asyncio
import httpx

async def batch_queries(questions):
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post(
                "http://localhost:8000/api/rag/query",
                json={"question": q}
            ) for q in questions
        ]
        return await asyncio.gather(*tasks)
```

**3. Cache Frequently Asked Questions**
```python
# Implement Redis cache layer (future enhancement)
# Cache schema: hash(question) -> response
```

**4. Use Production LLM**
```bash
# Mock LLM: <100ms
# OpenAI API: 1000-3000ms

# For production: Use streaming responses
# (Currently not implemented)
```

### Scaling to Multiple Servers

**Current Limitation**: FAISS index is in-memory and local

**Scaling Path**:
1. Share `data/faiss_index.faiss` across servers
2. Use shared file storage (NFS, S3)
3. Implement index versioning and sync
4. Use load balancer (nginx, HAProxy)

---

## Backup & Recovery

### Backup Strategy

**What to backup**:
```bash
# Critical data
- data/faiss_index.faiss       # Vector store
- data/metadata.json           # Chunk metadata
- student_profiles/*.pdf       # Source resumes
- .env                         # Configuration
```

**Backup script**:

```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup data
cp -r data/ $BACKUP_DIR/
cp -r student_profiles/ $BACKUP_DIR/
cp .env $BACKUP_DIR/

# Compress
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR/
rm -rf $BACKUP_DIR

echo "Backup created: $BACKUP_DIR.tar.gz"
```

**Automated backup (cron)**:

```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh

# Keep last 7 days
find backups/ -type f -mtime +7 -delete
```

### Recovery Procedure

**To restore from backup**:

```bash
# 1. Stop server
pkill -f "app.main"

# 2. Extract backup
tar -xzf backups/20240601_020000.tar.gz

# 3. Restore files
cp backups/20240601_020000/data/* data/
cp backups/20240601_020000/.env .env

# 4. Restart
python -m app.main
```

### Disaster Recovery

**If FAISS index is lost:**

```bash
# 1. Remove corrupted index
rm data/faiss_index.faiss
rm data/metadata.json

# 2. Re-ingest from PDFs
curl -X POST http://localhost:8000/api/rag/ingest

# Takes ~1 second per resume
```

**If student_profiles/ is lost:**

```bash
# Need to restore from backup
# Or re-download resumes from students
# System will not work without source resumes
```

---

## Maintenance Tasks

### Weekly

- [ ] Review logs for errors
- [ ] Check disk usage: `du -sh data/`
- [ ] Test backup restoration
- [ ] Query performance metrics

### Monthly

- [ ] Review student enrollment changes
- [ ] Update synthetic data if needed
- [ ] Performance analysis
- [ ] Security audit

### Quarterly

- [ ] Update dependencies: `pip install -r requirements.txt --upgrade`
- [ ] Test with new LLM model versions
- [ ] Capacity planning for next period

---

## Emergency Procedures

### Server Crash Recovery

```bash
# 1. Check if process is running
ps aux | grep app.main

# 2. Kill zombie process if needed
pkill -9 -f app.main

# 3. Check logs for errors
tail -100 server.log

# 4. Restart
python -m app.main

# 5. Verify health
curl http://localhost:8000/health
```

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
python -m app.main --port 8001
```

### Out of Disk Space

```bash
# Check usage
du -sh data/
du -sh student_profiles/

# Clean old backups if needed
rm backups/*old*.tar.gz

# Increase chunk size to reduce total chunks
# Edit .env: CHUNK_SIZE=1024
# Re-ingest
```

---

## Support & Debugging

### Enable Debug Mode

```bash
# In .env
DEBUG=true

# Restart server
# More verbose logging will be displayed
```

### Generate Support Bundle

```bash
#!/bin/bash
mkdir -p support_bundle
cp README.md support_bundle/
cp docs/*.md support_bundle/
cp .env support_bundle/  # Redact API keys first!
du -sh data/ > support_bundle/disk_usage.txt
tail -100 server.log > support_bundle/recent_logs.txt
python -m pytest tests/ -v > support_bundle/test_results.txt 2>&1

tar -czf support_bundle.tar.gz support_bundle/
echo "Support bundle created: support_bundle.tar.gz"
```

### Contact Support

Include in issue report:
1. Error message and stack trace
2. Steps to reproduce
3. System info (OS, Python version)
4. Output of: `pip freeze > requirements_used.txt`
5. Recent logs from `server.log`

---

**Last Updated**: June 2024  
**For Latest**: See [docs/solution_advanced.md](docs/solution_advanced.md)

# Document Intelligence Pipeline


---

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic v2
- httpx (async HTTP client)
- Gemini API (LLM)
- pytest

---

## Setup

### Install Dependencies

pip install fastapi uvicorn httpx python-dotenv pytest

---

### Configure Environment

Create `.env`:

GEMINI_API_KEY=your_api_key_here

---

### Run Service

uvicorn app.main:app --reload

---

### 5. Open API Docs

http://127.0.0.1:8000/docs

---

## 📌 API Endpoints

### Health Check
GET /health

### Validate
POST /validate

### Match
POST /match

### Process (End-to-End)
POST /process

---

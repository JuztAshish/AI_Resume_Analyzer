# AI Resume Analyzer

A simple and clean **AI Resume Analyzer** focused on **AI Engineer recruitment**. Built with Python, NLP, Machine Learning, and LLM-based feedback — designed to demonstrate core AI/ML concepts in a company shortlisting round or technical interview.

---

## Features

| Feature | Description |
|---------|-------------|
| **Resume Upload** | Upload single or multiple PDF/DOCX resumes |
| **Resume Parsing** | Extract name, email, skills, education, experience, projects |
| **Job Description Input** | Paste an AI Engineer job description for matching |
| **Semantic Matching** | Sentence Transformers + cosine similarity for match scores |
| **Section-wise Analysis** | Skills, Experience, and Education match scores |
| **Resume Ranking** | Rank multiple candidates in a sortable table |
| **AI Feedback** | Strengths, missing skills, improvements, hiring recommendation |
| **Dashboard** | Match percentage, extracted skills, rankings, feedback report |
| **Authentication** | JWT-based login/register |
| **Error Handling** | Invalid files, empty resumes, API errors |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| PDF Parsing | PyMuPDF |
| DOCX Parsing | python-docx |
| NLP | spaCy |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Similarity | Scikit-Learn (cosine similarity) |
| AI Feedback | Google Gemini API / OpenAI API |
| Database | SQLite |
| Auth | JWT (python-jose + passlib) |

---

## Project Structure

```
ai_resume_analyzer/
│
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI app & API endpoints
│   ├── auth.py          # JWT authentication
│   ├── parser.py        # PDF/DOCX resume parsing
│   ├── matcher.py       # Embeddings & cosine similarity
│   ├── feedback.py      # AI feedback generation
│   └── database.py      # SQLite database
│
├── frontend/
│   └── app.py           # Streamlit dashboard
│
├── samples/
│   ├── sample_job_description.txt
│   ├── create_sample_resumes.py
│   └── resumes/         # Sample DOCX resumes (generated)
│
├── uploads/             # Temporary upload storage
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- pip

### 2. Clone and Install

```bash
# Navigate to project folder
cd ai_resume_analyzer

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy English model
python -m spacy download en_core_web_sm
```

### 3. Configure Environment

```bash
# Copy example env file
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
```

Edit `.env` and set your API keys:

```env
JWT_SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key    # Get free at https://aistudio.google.com/app/apikey
OPENAI_API_KEY=your-openai-api-key    # Optional fallback
API_URL=http://127.0.0.1:8000
```

> **Note:** AI feedback works without API keys using rule-based fallback, but Gemini/OpenAI keys enable richer LLM-powered feedback.

### 4. Generate Sample Resumes

```bash
python samples/create_sample_resumes.py
```

This creates three sample DOCX resumes in `samples/resumes/`:
- `alice_chen_ai_engineer.docx` — Strong match
- `bob_martinez_developer.docx` — Moderate match
- `carol_williams_analyst.docx` — Weak match

---

## Running the Application

You need **two terminals** — one for the backend, one for the frontend.

### Terminal 1: Start Backend (FastAPI)

```bash
# From project root
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

API docs available at: http://127.0.0.1:8000/docs

### Terminal 2: Start Frontend (Streamlit)

```bash
# From project root
streamlit run frontend/app.py
```

App opens at: http://localhost:8501

---

## How to Use

1. **Register** a new account (or login)
2. **Paste** the AI Engineer job description (sample pre-loaded)
3. **Upload** one or more resumes from `samples/resumes/`
4. Click **Analyze Resumes**
5. View the **ranking table**, **match scores**, and **AI feedback**

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | No |
| POST | `/auth/register` | Create account | No |
| POST | `/auth/login` | Login & get JWT | No |
| POST | `/analyze` | Upload resumes + analyze | Yes |

### Example: Analyze via curl

```bash
# Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Analyze
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -F "job_description=@samples/sample_job_description.txt" \
  -F "files=@samples/resumes/alice_chen_ai_engineer.docx"
```

---

## How It Works

```
Resume (PDF/DOCX)
       │
       ▼
  [Parser]  ──► Extract: name, email, skills, education, experience, projects
       │
       ▼
  [Matcher] ──► Sentence Transformers embeddings
       │         Cosine similarity vs job description
       │         Section-wise scores (skills, experience, education)
       ▼
  [Feedback] ──► Gemini/OpenAI generates hiring insights
       │
       ▼
  [Dashboard] ──► Ranked candidates + scores + feedback
```

### Matching Algorithm

1. Resume sections and job description are converted to **384-dimensional embeddings** using `all-MiniLM-L6-v2`
2. **Cosine similarity** computes semantic match between each section and the job description
3. A **weighted score** combines overall (40%), skills (35%), experience (20%), and education (5%) matches

---

## Concepts Demonstrated

- **NLP**: spaCy NER for name extraction, keyword-based skill extraction
- **Embeddings**: Sentence Transformers for semantic text representation
- **Machine Learning**: Cosine similarity for resume-job matching
- **LLM Integration**: Gemini/OpenAI API for structured feedback generation
- **Full-Stack Python**: FastAPI backend + Streamlit frontend
- **Authentication**: JWT token-based auth with bcrypt password hashing
- **Database**: SQLite for user management

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Cannot connect to backend API` | Ensure FastAPI is running on port 8000 |
| `en_core_web_sm not found` | Run `python -m spacy download en_core_web_sm` |
| Slow first analysis | Sentence Transformer model downloads on first run (~90MB) |
| AI feedback shows "rule-based" | Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env` |
| Invalid file error | Only PDF and DOCX files are supported |

---

## License

MIT License — free to use for learning, interviews, and portfolio projects.

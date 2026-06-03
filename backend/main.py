"""
FastAPI backend entry point.
Provides REST API for authentication, resume upload, and analysis.
"""

import shutil
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from backend.auth import create_access_token, get_current_user, hash_password, verify_password
from backend.database import create_user, get_user_by_email, get_user_by_username, init_db
from backend.feedback import generate_feedback
from backend.matcher import analyze_resume, rank_resumes
from backend.parser import ResumeParseError, parse_resume

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="AI Resume Analyzer API",
    description="Analyze and rank AI Engineer resumes against job descriptions",
    version="1.0.0",
)

# Allow Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models for request/response validation
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# ---------------------------------------------------------------------------
# Startup: initialize SQLite database
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup() -> None:
    init_db()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "message": "AI Resume Analyzer API is running"}


# ---------------------------------------------------------------------------
# Authentication endpoints
# ---------------------------------------------------------------------------
@app.post("/auth/register", response_model=TokenResponse)
def register(request: RegisterRequest) -> TokenResponse:
    """Register a new user account."""
    if get_user_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    if get_user_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed = hash_password(request.password)
    create_user(request.username, request.email, hashed)
    token = create_access_token(request.username)

    return TokenResponse(access_token=token, username=request.username)


@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest) -> TokenResponse:
    """Log in and receive a JWT access token."""
    user = get_user_by_username(request.username)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(request.username)
    return TokenResponse(access_token=token, username=request.username)


# ---------------------------------------------------------------------------
# Resume analysis endpoint
# ---------------------------------------------------------------------------
@app.post("/analyze")
async def analyze_resumes(
    job_description: str = Form(...),
    files: list[UploadFile] = File(...),
    username: str = Depends(get_current_user),
) -> dict:
    """
    Upload one or more resumes and analyze them against a job description.
    Returns ranked candidates with match scores and AI feedback.
    """
    if not job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description cannot be empty",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one resume file is required",
        )

    results = []
    errors = []

    for upload in files:
        # Save uploaded file to disk with a unique name
        session_id = uuid.uuid4().hex[:8]
        safe_name = Path(upload.filename or "resume").name
        file_path = UPLOAD_DIR / f"{session_id}_{safe_name}"

        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(upload.file, buffer)

            # Step 1: Parse resume
            parsed = parse_resume(file_path)

            # Step 2: Compute semantic match scores
            analysis = analyze_resume(parsed, job_description)

            # Step 3: Generate AI feedback
            feedback = generate_feedback(analysis, job_description)

            results.append({**analysis, "feedback": feedback})

        except ResumeParseError as exc:
            errors.append({"filename": upload.filename, "error": str(exc)})
        except Exception as exc:
            errors.append({"filename": upload.filename, "error": f"Unexpected error: {exc}"})
        finally:
            # Clean up uploaded file after processing
            if file_path.exists():
                file_path.unlink()

    if not results and errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "All uploads failed", "errors": errors},
        )

    # Rank candidates by overall match score
    ranked = rank_resumes(results)

    return {
        "total_analyzed": len(ranked),
        "candidates": ranked,
        "errors": errors,
        "analyzed_by": username,
    }

"""
Resume parsing module.
Extracts text from PDF/DOCX files and pulls structured fields
(name, email, skills, education, experience, projects).
"""

import re
from pathlib import Path

import fitz  # PyMuPDF
import spacy
from docx import Document

# Load spaCy English model for Named Entity Recognition (NER)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback: blank model if en_core_web_sm is not installed yet
    nlp = spacy.blank("en")

# Common AI/ML and software skills for keyword matching
AI_ENGINEER_SKILLS = {
    "python", "java", "c++", "javascript", "typescript", "sql",
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
    "pandas", "numpy", "matplotlib", "seaborn", "opencv",
    "transformers", "huggingface", "bert", "gpt", "llm", "langchain",
    "rag", "vector database", "pinecone", "faiss", "chromadb",
    "fastapi", "flask", "django", "docker", "kubernetes", "aws", "gcp", "azure",
    "mlflow", "airflow", "spark", "hadoop", "git", "github",
    "data structures", "algorithms", "statistics", "linear algebra",
    "reinforcement learning", "generative ai", "prompt engineering",
    "fine-tuning", "model deployment", "mlops", "api development",
    "rest api", "microservices", "mongodb", "postgresql", "redis",
    "streamlit", "gradio", "jupyter", "cuda", "gpu", "neural networks",
    "cnn", "rnn", "lstm", "transformer", "attention mechanism",
    "feature engineering", "data preprocessing", "a/b testing",
    "agile", "scrum", "ci/cd", "jenkins", "linux", "bash",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class ResumeParseError(Exception):
    """Raised when a resume cannot be parsed or is empty."""


def validate_file(filename: str) -> str:
    """
    Validate file extension.
    Returns the lowercase extension or raises ResumeParseError.
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ResumeParseError(
            f"Invalid file type '{ext}'. Only PDF and DOCX files are supported."
        )
    return ext


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract all text from a PDF file using PyMuPDF."""
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_text_from_docx(file_path: Path) -> str:
    """Extract all text from a DOCX file using python-docx."""
    doc = Document(file_path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)


def extract_text(file_path: Path) -> str:
    """Route to the correct extractor based on file extension."""
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext == ".docx":
        return extract_text_from_docx(file_path)
    raise ResumeParseError(f"Unsupported file type: {ext}")


def extract_email(text: str) -> str:
    """Find the first email address in the resume text."""
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0) if match else "Not found"


def extract_name(text: str) -> str:
    """
    Extract candidate name using spaCy NER.
    Falls back to the first non-empty line if no PERSON entity is found.
    """
    # Use first ~500 chars where name usually appears
    sample = text[:500]
    doc = nlp(sample)

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()

    # Fallback: first meaningful line (skip headers like "Resume")
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) < 60 and not line.lower().startswith("resume"):
            return line
    return "Unknown"


def extract_skills(text: str) -> list[str]:
    """
    Extract skills by matching against a curated AI/ML skill list.
    Case-insensitive keyword search in resume text.
    """
    text_lower = text.lower()
    found_skills = []

    for skill in sorted(AI_ENGINEER_SKILLS, key=len, reverse=True):
        if skill in text_lower and skill not in found_skills:
            found_skills.append(skill.title() if len(skill) <= 4 else skill)

    return found_skills


def extract_section(text: str, section_keywords: list[str]) -> str:
    """
    Extract a resume section by finding a heading keyword
    and reading text until the next section heading.
    """
    lines = text.split("\n")
    section_lines = []
    capturing = False

    # Common section headings that signal the end of current section
    all_headings = [
        "experience", "work experience", "employment", "professional experience",
        "education", "academic", "qualification", "skills", "technical skills",
        "projects", "certifications", "summary", "objective", "contact",
        "achievements", "publications", "references",
    ]

    for line in lines:
        line_lower = line.strip().lower()

        # Start capturing when we hit a matching section keyword
        if not capturing:
            if any(kw in line_lower for kw in section_keywords) and len(line.strip()) < 80:
                capturing = True
                continue
        else:
            # Stop when we hit another section heading
            if any(h in line_lower for h in all_headings) and len(line.strip()) < 80:
                if not any(kw in line_lower for kw in section_keywords):
                    break
            section_lines.append(line)

    return "\n".join(section_lines).strip()


def parse_resume(file_path: Path) -> dict:
    """
    Main parsing function.
    Returns a dictionary with all extracted resume fields.
    """
    validate_file(file_path.name)

    text = extract_text(file_path).strip()
    if not text or len(text) < 50:
        raise ResumeParseError(
            "Resume appears empty or too short. Please upload a valid resume."
        )

    skills = extract_skills(text)
    education = extract_section(text, ["education", "academic", "qualification"])
    experience = extract_section(
        text, ["experience", "work experience", "employment", "professional experience"]
    )
    projects = extract_section(text, ["projects", "personal projects", "key projects"])

    return {
        "filename": file_path.name,
        "raw_text": text,
        "name": extract_name(text),
        "email": extract_email(text),
        "skills": skills,
        "education": education or "Not explicitly listed",
        "experience": experience or "Not explicitly listed",
        "projects": projects or "Not explicitly listed",
    }

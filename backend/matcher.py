"""
Resume matching module.
Uses Sentence Transformers for embeddings and Scikit-Learn
for cosine similarity between resume sections and job description.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load pre-trained model once at startup (cached in memory)
# all-MiniLM-L6-v2 is lightweight and works well for semantic similarity
_model = None


def get_model() -> SentenceTransformer:
    """Lazy-load the Sentence Transformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two text strings.
    Returns a score between 0.0 and 1.0.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0

    model = get_model()
    embeddings = model.encode([text_a, text_b])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    # Clamp to [0, 1] range for display
    return float(max(0.0, min(1.0, score)))


def build_resume_text(parsed_resume: dict) -> str:
    """Combine all resume fields into one text block for overall matching."""
    skills_text = ", ".join(parsed_resume.get("skills", []))
    return "\n".join(
        [
            f"Skills: {skills_text}",
            f"Experience: {parsed_resume.get('experience', '')}",
            f"Education: {parsed_resume.get('education', '')}",
            f"Projects: {parsed_resume.get('projects', '')}",
        ]
    )


def analyze_resume(parsed_resume: dict, job_description: str) -> dict:
    """
    Perform section-wise and overall semantic matching
    between a parsed resume and a job description.
    """
    resume_text = build_resume_text(parsed_resume)
    skills_text = ", ".join(parsed_resume.get("skills", []))

    # Section-wise cosine similarity scores
    skills_score = compute_similarity(skills_text, job_description)
    experience_score = compute_similarity(
        parsed_resume.get("experience", ""), job_description
    )
    education_score = compute_similarity(
        parsed_resume.get("education", ""), job_description
    )

    # Overall match uses the full resume text
    overall_score = compute_similarity(resume_text, job_description)

    # Weighted average for a balanced final score
    weighted_score = (
        overall_score * 0.4
        + skills_score * 0.35
        + experience_score * 0.20
        + education_score * 0.05
    )

    return {
        "name": parsed_resume.get("name", "Unknown"),
        "email": parsed_resume.get("email", "Not found"),
        "filename": parsed_resume.get("filename", ""),
        "skills": parsed_resume.get("skills", []),
        "education": parsed_resume.get("education", ""),
        "experience": parsed_resume.get("experience", ""),
        "projects": parsed_resume.get("projects", ""),
        "overall_score": round(weighted_score * 100, 2),
        "skills_score": round(skills_score * 100, 2),
        "experience_score": round(experience_score * 100, 2),
        "education_score": round(education_score * 100, 2),
    }


def rank_resumes(results: list[dict]) -> list[dict]:
    """Sort resumes by overall_score in descending order and assign ranks."""
    ranked = sorted(results, key=lambda x: x["overall_score"], reverse=True)
    for i, item in enumerate(ranked, start=1):
        item["rank"] = i
    return ranked

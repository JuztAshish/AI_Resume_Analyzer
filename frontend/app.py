"""
Streamlit frontend for the AI Resume Analyzer.
Provides login/register, resume upload, job description input,
and a dashboard showing match scores, rankings, and AI feedback.
"""

import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Backend API URL (change if running on a different host/port)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Page configuration and custom CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1E3A5F;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1rem;
            color: #64748B;
            margin-bottom: 1.5rem;
        }
        .score-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 12px;
            color: white;
            text-align: center;
        }
        .score-value {
            font-size: 3rem;
            font-weight: 800;
        }
        .metric-box {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        .feedback-box {
            background: #F0FDF4;
            border-left: 4px solid #22C55E;
            padding: 1rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }
        .warning-box {
            background: #FEF3C7;
            border-left: 4px solid #F59E0B;
            padding: 1rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "results" not in st.session_state:
    st.session_state.results = None


def api_headers() -> dict:
    """Return authorization headers for authenticated API calls."""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def score_color(score: float) -> str:
    """Return a color based on match score percentage."""
    if score >= 75:
        return "#22C55E"
    if score >= 50:
        return "#F59E0B"
    return "#EF4444"


# ---------------------------------------------------------------------------
# Authentication pages
# ---------------------------------------------------------------------------
def show_login_page() -> None:
    """Render login and register forms."""
    st.markdown('<p class="main-header">🤖 AI Resume Analyzer</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Smart resume screening for AI Engineer recruitment</p>',
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/auth/login",
                            json={"username": username, "password": password},
                            timeout=10,
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.token = data["access_token"]
                            st.session_state.username = data["username"]
                            st.success(f"Welcome back, {data['username']}!")
                            st.rerun()
                        else:
                            st.error(response.json().get("detail", "Login failed"))
                    except requests.ConnectionError:
                        st.error(
                            "Cannot connect to backend API. "
                            "Make sure the FastAPI server is running on port 8000."
                        )

    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Username", key="reg_user")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Password", type="password", key="reg_pass")
            confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if new_password != confirm:
                    st.error("Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/auth/register",
                            json={
                                "username": new_username,
                                "email": new_email,
                                "password": new_password,
                            },
                            timeout=10,
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.token = data["access_token"]
                            st.session_state.username = data["username"]
                            st.success("Account created! You are now logged in.")
                            st.rerun()
                        else:
                            st.error(response.json().get("detail", "Registration failed"))
                    except requests.ConnectionError:
                        st.error("Cannot connect to backend API.")


# ---------------------------------------------------------------------------
# Dashboard helpers
# ---------------------------------------------------------------------------
def render_score_gauge(score: float, label: str) -> None:
    """Display a single score metric with color coding."""
    color = score_color(score)
    st.markdown(
        f"""
        <div class="metric-box">
            <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 4px;">{label}</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: {color};">{score:.1f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feedback(feedback: dict) -> None:
    """Display AI-generated feedback for a candidate."""
    st.markdown("#### 📋 AI Feedback Report")

    recommendation = feedback.get("hiring_recommendation", "N/A")
    rec_color = (
        "#22C55E"
        if "Strong" in recommendation
        else "#F59E0B"
        if "Consider" in recommendation
        else "#EF4444"
    )
    st.markdown(
        f"**Hiring Recommendation:** "
        f"<span style='color:{rec_color}; font-weight:700;'>{recommendation}</span>",
        unsafe_allow_html=True,
    )

    if feedback.get("summary"):
        st.info(feedback["summary"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**✅ Strengths**")
        for item in feedback.get("strengths", []):
            st.markdown(f"- {item}")

    with col2:
        st.markdown("**❌ Missing Skills**")
        for item in feedback.get("missing_skills", []):
            st.markdown(f"- {item}")

    st.markdown("**📈 Areas for Improvement**")
    for item in feedback.get("areas_for_improvement", []):
        st.markdown(f"- {item}")

    source = feedback.get("source", "")
    if source:
        st.caption(f"Feedback source: {source}")


def render_candidate_detail(candidate: dict) -> None:
    """Show detailed analysis for a single candidate."""
    st.markdown(f"### 👤 {candidate.get('name', 'Unknown')}")
    st.caption(f"📧 {candidate.get('email', 'N/A')}  |  📄 {candidate.get('filename', '')}")

    # Overall score highlight
    overall = candidate.get("overall_score", 0)
    st.markdown(
        f"""
        <div class="score-card">
            <div style="font-size: 0.9rem; opacity: 0.9;">Overall Match Score</div>
            <div class="score-value">{overall:.1f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Section-wise scores
    col1, col2, col3 = st.columns(3)
    with col1:
        render_score_gauge(candidate.get("skills_score", 0), "Skills Match")
    with col2:
        render_score_gauge(candidate.get("experience_score", 0), "Experience Match")
    with col3:
        render_score_gauge(candidate.get("education_score", 0), "Education Match")

    st.markdown("<br>", unsafe_allow_html=True)

    # Extracted skills
    skills = candidate.get("skills", [])
    if skills:
        st.markdown("**🔧 Extracted Skills**")
        st.markdown(" ".join([f"`{s}`" for s in skills]))

    # AI Feedback
    feedback = candidate.get("feedback", {})
    if feedback:
        render_feedback(feedback)

    with st.expander("View Extracted Sections"):
        st.markdown("**Experience**")
        st.text(candidate.get("experience", "N/A"))
        st.markdown("**Education**")
        st.text(candidate.get("education", "N/A"))
        st.markdown("**Projects**")
        st.text(candidate.get("projects", "N/A"))


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------
def show_dashboard() -> None:
    """Render the main analysis dashboard."""
    # Sidebar
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        if st.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.results = None
            st.rerun()

        st.markdown("---")
        st.markdown("### How it works")
        st.markdown(
            """
            1. Paste an AI Engineer job description
            2. Upload one or more resumes (PDF/DOCX)
            3. Click **Analyze Resumes**
            4. View match scores, rankings & AI feedback
            """
        )

    st.markdown('<p class="main-header">📊 Analysis Dashboard</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Upload resumes and compare them against your job description</p>',
        unsafe_allow_html=True,
    )

    # Job description input
    st.markdown("### 📝 Job Description")
    default_jd = ""
    sample_jd_path = os.path.join(
        os.path.dirname(__file__), "..", "samples", "sample_job_description.txt"
    )
    if os.path.exists(sample_jd_path):
        with open(sample_jd_path, encoding="utf-8") as f:
            default_jd = f.read()

    job_description = st.text_area(
        "Paste the AI Engineer job description here",
        value=default_jd,
        height=200,
        placeholder="Enter job requirements, skills, experience level...",
    )

    # Resume upload
    st.markdown("### 📤 Upload Resumes")
    uploaded_files = st.file_uploader(
        "Upload PDF or DOCX resumes (single or multiple)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.info(f"{len(uploaded_files)} file(s) selected: "
                + ", ".join(f.name for f in uploaded_files))

    # Analyze button
    analyze_clicked = st.button(
        "🔍 Analyze Resumes",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files or not job_description.strip(),
    )

    if analyze_clicked:
        with st.spinner("Analyzing resumes... This may take a moment on first run (loading ML model)."):
            try:
                files_payload = [
                    ("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files
                ]
                response = requests.post(
                    f"{API_URL}/analyze",
                    headers=api_headers(),
                    data={"job_description": job_description},
                    files=files_payload,
                    timeout=120,
                )

                if response.status_code == 200:
                    st.session_state.results = response.json()
                    st.success(
                        f"Analysis complete! "
                        f"{st.session_state.results['total_analyzed']} resume(s) processed."
                    )
                elif response.status_code == 401:
                    st.error("Session expired. Please log in again.")
                    st.session_state.token = None
                    st.rerun()
                else:
                    detail = response.json().get("detail", "Analysis failed")
                    if isinstance(detail, dict):
                        st.error(detail.get("message", "Analysis failed"))
                        for err in detail.get("errors", []):
                            st.warning(f"**{err['filename']}**: {err['error']}")
                    else:
                        st.error(detail)

            except requests.ConnectionError:
                st.error("Cannot connect to backend API. Is the server running?")
            except requests.Timeout:
                st.error("Request timed out. Try uploading fewer resumes.")

    # Display results
    if st.session_state.results:
        results = st.session_state.results
        candidates = results.get("candidates", [])

        if not candidates:
            st.warning("No candidates to display.")
            return

        st.markdown("---")
        st.markdown("### 🏆 Candidate Ranking")

        # Ranking table
        table_data = []
        for c in candidates:
            feedback = c.get("feedback", {})
            table_data.append(
                {
                    "Rank": c.get("rank", "-"),
                    "Name": c.get("name", "Unknown"),
                    "Email": c.get("email", "N/A"),
                    "Overall Score (%)": c.get("overall_score", 0),
                    "Skills Score (%)": c.get("skills_score", 0),
                    "Experience Score (%)": c.get("experience_score", 0),
                    "Education Score (%)": c.get("education_score", 0),
                    "Recommendation": feedback.get("hiring_recommendation", "N/A"),
                }
            )

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Show errors if any files failed
        errors = results.get("errors", [])
        if errors:
            st.markdown("### ⚠️ Upload Errors")
            for err in errors:
                st.warning(f"**{err['filename']}**: {err['error']}")

        # Detailed view per candidate
        st.markdown("---")
        st.markdown("### 🔍 Detailed Candidate Analysis")

        candidate_names = [
            f"#{c.get('rank', '?')} - {c.get('name', 'Unknown')} ({c.get('overall_score', 0):.1f}%)"
            for c in candidates
        ]
        selected = st.selectbox("Select a candidate to view details", candidate_names)

        if selected:
            idx = candidate_names.index(selected)
            render_candidate_detail(candidates[idx])


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------
def main() -> None:
    if st.session_state.token:
        show_dashboard()
    else:
        show_login_page()


if __name__ == "__main__":
    main()

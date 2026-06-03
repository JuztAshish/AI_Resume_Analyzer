"""
AI feedback generation module.
Uses Gemini API (primary) or OpenAI API (fallback) to generate
hiring insights: strengths, missing skills, improvements, recommendation.
"""

import json
import os
import re

# ---------------------------------------------------------------------------
# Prompt template sent to the LLM
# ---------------------------------------------------------------------------
FEEDBACK_PROMPT = """You are an expert AI Engineer hiring manager reviewing a candidate resume against a job description.

Resume Summary:
- Name: {name}
- Skills: {skills}
- Experience: {experience}
- Education: {education}
- Projects: {projects}

Match Scores:
- Overall: {overall_score}%
- Skills: {skills_score}%
- Experience: {experience_score}%
- Education: {education_score}%

Job Description:
{job_description}

Provide a structured hiring analysis. Respond ONLY with valid JSON in this exact format:
{{
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "missing_skills": ["skill 1", "skill 2"],
  "areas_for_improvement": ["area 1", "area 2"],
  "hiring_recommendation": "Strong Hire / Consider / Not Recommended",
  "summary": "2-3 sentence overall assessment"
}}
"""


def _parse_json_response(text: str) -> dict:
    """Extract and parse JSON from LLM response text."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in markdown code fence
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    # Try to find raw JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("Could not parse JSON from LLM response")


def _generate_with_gemini(prompt: str) -> str:
    """Call Google Gemini API for feedback generation."""
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text


def _generate_with_openai(prompt: str) -> str:
    """Call OpenAI API as fallback for feedback generation."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert AI Engineer hiring manager. Always respond with valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def _fallback_feedback(analysis: dict) -> dict:
    """
    Rule-based feedback when no LLM API key is configured.
    Still provides useful insights based on match scores.
    """
    score = analysis["overall_score"]
    skills = analysis.get("skills", [])

    if score >= 75:
        recommendation = "Strong Hire"
        summary = (
            f"{analysis['name']} shows strong alignment ({score}%) with the AI Engineer role. "
            "Their skill set and experience closely match the job requirements."
        )
    elif score >= 50:
        recommendation = "Consider"
        summary = (
            f"{analysis['name']} is a moderate match ({score}%) for the role. "
            "They have relevant skills but may need upskilling in some areas."
        )
    else:
        recommendation = "Not Recommended"
        summary = (
            f"{analysis['name']} has limited alignment ({score}%) with this AI Engineer position. "
            "Significant skill gaps exist relative to the job description."
        )

    return {
        "strengths": skills[:5] if skills else ["Resume submitted for review"],
        "missing_skills": ["Review job description for specific gaps"],
        "areas_for_improvement": [
            "Add quantifiable project outcomes",
            "Highlight AI/ML deployment experience",
        ],
        "hiring_recommendation": recommendation,
        "summary": summary,
        "source": "rule-based (no API key configured)",
    }


def generate_feedback(analysis: dict, job_description: str) -> dict:
    """
    Generate AI-powered hiring feedback for a single candidate.
    Falls back to rule-based feedback if API keys are unavailable.
    """
    prompt = FEEDBACK_PROMPT.format(
        name=analysis.get("name", "Unknown"),
        skills=", ".join(analysis.get("skills", [])),
        experience=analysis.get("experience", "")[:800],
        education=analysis.get("education", "")[:400],
        projects=analysis.get("projects", "")[:400],
        overall_score=analysis.get("overall_score", 0),
        skills_score=analysis.get("skills_score", 0),
        experience_score=analysis.get("experience_score", 0),
        education_score=analysis.get("education_score", 0),
        job_description=job_description[:2000],
    )

    # Try Gemini first, then OpenAI, then rule-based fallback
    llm_response = None
    source = "unknown"

    if os.getenv("GEMINI_API_KEY"):
        try:
            llm_response = _generate_with_gemini(prompt)
            source = "gemini"
        except Exception:
            pass

    if llm_response is None and os.getenv("OPENAI_API_KEY"):
        try:
            llm_response = _generate_with_openai(prompt)
            source = "openai"
        except Exception:
            pass

    if llm_response is None:
        feedback = _fallback_feedback(analysis)
        return feedback

    try:
        feedback = _parse_json_response(llm_response)
        feedback["source"] = source
        return feedback
    except (json.JSONDecodeError, ValueError):
        return _fallback_feedback(analysis)

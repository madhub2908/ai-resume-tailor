from __future__ import annotations

import io
import os
import re
from collections import Counter
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pypdf import PdfReader

load_dotenv()

app = FastAPI(title="AI Resume Tailor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "you",
    "your",
    "are",
    "our",
    "from",
    "will",
    "have",
    "has",
    "their",
    "they",
    "who",
    "all",
    "any",
    "not",
    "but",
    "job",
    "role",
    "work",
    "experience",
    "years",
    "skills",
    "requirements",
    "using",
    "ability",
    "team",
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in pdf_reader.pages]
    return "\n".join(pages).strip()


def normalize_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{2,}", text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def extract_priority_keywords(job_description: str, top_n: int = 25) -> list[str]:
    token_counts = Counter(normalize_tokens(job_description))
    return [token for token, _ in token_counts.most_common(top_n)]


def compute_keyword_match_score(resume_text: str, job_description: str) -> tuple[int, list[str]]:
    resume_tokens = set(normalize_tokens(resume_text))
    target_keywords = extract_priority_keywords(job_description)

    if not target_keywords:
        return 0, []

    matched = [keyword for keyword in target_keywords if keyword in resume_tokens]
    score = round((len(matched) / len(target_keywords)) * 100)
    missing = [keyword for keyword in target_keywords if keyword not in resume_tokens]
    return score, missing[:12]


def tailor_resume_sections(resume_text: str, job_description: str) -> dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set. Add it to your environment or .env file.",
        )

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are an expert resume editor.

Task:
- Rewrite ONLY the candidate's professional Summary and Core Capabilities/Skills section to better align with the job description.
- Do not fabricate achievements, employers, years, tools, or responsibilities.
- Preserve truthfulness: only reword or reorganize information that already exists in the resume.
- Avoid copying sentences from the job description.
- Keep language concise, ATS-friendly, and natural.

Return JSON with this exact shape:
{{
  "tailored_summary": "...",
  "tailored_core_capabilities": ["item 1", "item 2", "item 3"],
  "notes": "short explanation of what changed"
}}

Resume:
{resume_text}

Job Description:
{job_description}
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You tailor resumes honestly and never invent experience."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    content = completion.choices[0].message.content
    if not content:
        raise HTTPException(status_code=500, detail="OpenAI returned an empty response.")

    import json

    try:
        parsed: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Failed to parse OpenAI response.") from exc

    return {
        "tailored_summary": str(parsed.get("tailored_summary", "")).strip(),
        "tailored_core_capabilities": parsed.get("tailored_core_capabilities", []),
        "notes": str(parsed.get("notes", "")).strip(),
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/tailor")
async def tailor_resume(
    job_description: str = Form(...),
    resume_text: str = Form(""),
    resume_file: UploadFile | None = File(default=None),
) -> dict[str, Any]:
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")

    final_resume_text = resume_text.strip()

    if resume_file is not None:
        raw_file = await resume_file.read()
        if not raw_file:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        if resume_file.filename and resume_file.filename.lower().endswith(".pdf"):
            final_resume_text = extract_text_from_pdf(raw_file)
        else:
            final_resume_text = raw_file.decode("utf-8", errors="ignore").strip()

    if not final_resume_text:
        raise HTTPException(
            status_code=400,
            detail="Provide resume text or upload a .txt/.pdf file.",
        )

    score, missing_skills = compute_keyword_match_score(final_resume_text, job_description)
    tailored = tailor_resume_sections(final_resume_text, job_description)

    return {
        "ats_keyword_match_score": score,
        "missing_skills_and_requirements": missing_skills,
        "tailored_summary": tailored["tailored_summary"],
        "tailored_core_capabilities": tailored["tailored_core_capabilities"],
        "tailoring_notes": tailored["notes"],
    }

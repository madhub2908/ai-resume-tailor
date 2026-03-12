# AI Resume Tailor

AI Resume Tailor is a simple full-stack web app that helps you adapt your resume to a specific job description while staying truthful.

## Features

- Upload resume as **PDF** or **text file**, or paste resume text directly.
- Paste a target **job description**.
- Uses the OpenAI API to rewrite:
  - Professional Summary
  - Core Capabilities
- Guardrails in prompt to avoid fabricated experience and avoid copying the job description verbatim.
- Highlights missing skills/requirements based on keyword analysis.
- Provides an ATS keyword match score.
- Clean, simple React UI.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React + Vite

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key

---

## 1) Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in `backend/`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Start backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL: `http://localhost:8000`

---

## 2) Run the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

If needed, set API base URL:

```bash
VITE_API_BASE=http://localhost:8000 npm run dev
```

---

## API endpoint

`POST /api/tailor`

Form fields:
- `job_description` (required)
- `resume_text` (optional if `resume_file` provided)
- `resume_file` (optional `.pdf` or `.txt`)

Response includes:
- `ats_keyword_match_score`
- `missing_skills_and_requirements`
- `tailored_summary`
- `tailored_core_capabilities`
- `tailoring_notes`

---

## Notes

- The app is designed for **rewording existing experience only**.
- Always review generated output before using it in applications.

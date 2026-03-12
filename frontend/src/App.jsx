import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const [resumeText, setResumeText] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setResult(null)

    const form = new FormData()
    form.append('job_description', jobDescription)
    form.append('resume_text', resumeText)
    if (resumeFile) {
      form.append('resume_file', resumeFile)
    }

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/tailor`, {
        method: 'POST',
        body: form,
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || 'Request failed')
      }
      setResult(payload)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container">
      <h1>AI Resume Tailor</h1>
      <p className="subhead">Tailor your resume honestly for a target role.</p>

      <form onSubmit={submit} className="card">
        <label>
          Resume text
          <textarea
            rows={8}
            value={resumeText}
            onChange={(event) => setResumeText(event.target.value)}
            placeholder="Paste resume text here (or upload a .pdf/.txt below)"
          />
        </label>

        <label>
          Upload resume (.pdf or .txt)
          <input
            type="file"
            accept=".pdf,.txt"
            onChange={(event) => setResumeFile(event.target.files?.[0] || null)}
          />
        </label>

        <label>
          Job description
          <textarea
            rows={10}
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="Paste job description"
            required
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? 'Tailoring...' : 'Tailor Resume'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {result && (
        <section className="results">
          <div className="metric card">
            <h2>ATS Keyword Match</h2>
            <p className="score">{result.ats_keyword_match_score}%</p>
          </div>

          <div className="card">
            <h2>Tailored Summary</h2>
            <p>{result.tailored_summary}</p>
          </div>

          <div className="card">
            <h2>Tailored Core Capabilities</h2>
            <ul>
              {(result.tailored_core_capabilities || []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h2>Missing Skills & Requirements</h2>
            <ul>
              {(result.missing_skills_and_requirements || []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          {result.tailoring_notes && (
            <div className="card">
              <h2>Notes</h2>
              <p>{result.tailoring_notes}</p>
            </div>
          )}
        </section>
      )}
    </main>
  )
}

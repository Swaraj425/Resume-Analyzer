# AI Resume Analyzer & Job Recommendation System

A Streamlit web app that analyzes an uploaded resume (PDF/DOCX), extracts skills,
scores the resume, matches it against a job dataset using TF-IDF + cosine
similarity combined with explicit skill-overlap, and shows job recommendations,
skill-gap analysis, charts, and a downloadable PDF report.

## Project Structure

```
resume_analyzer/
├── app.py                 # Main Streamlit app (UI + orchestration)
├── requirements.txt
├── data/
│   └── jobs.csv            # Sample job postings dataset (title, description, required_skills)
├── src/
│   ├── __init__.py
│   ├── parser.py           # PDF/DOCX text extraction + section splitting
│   ├── skills.py            # Skill keyword database + extraction
│   ├── matcher.py           # TF-IDF + cosine similarity + skill-overlap matching
│   └── report.py            # PDF report generation
└── sample_resumes/          # (empty) put test resumes here
```

## Setup (in VS Code)

1. Open this folder in VS Code.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```
5. Your browser will open at `http://localhost:8501`.

## How It Works

1. **Upload** a PDF or DOCX resume.
2. **Text extraction** — `PyPDF2` / `python-docx` pull out raw text.
3. **Skill extraction** — the text is scanned against a curated skill
   dictionary (`src/skills.py`) covering programming, AI/ML, data science,
   web dev, databases, and tools.
4. **Matching** — for each job in `data/jobs.csv`:
   - TF-IDF vectors are built for the resume + all job descriptions, and
     cosine similarity gives a contextual closeness score.
   - Required skills per job are compared against extracted resume skills
     for an explicit overlap percentage.
   - The two are blended (skills weighted 65%, TF-IDF 35%) into a final
     match %.
5. **Skill gap** — for any job, missing required skills are listed so the
   candidate knows what to learn next.
6. **Resume score** — a transparent 0–100 heuristic based on word count,
   presence of contact info, bullet-point usage, and skill breadth.
7. **Report** — all of the above is compiled into a downloadable PDF.

## Extending the Project

Ideas to go further for your internship submission:
- Add user login + SQLite so users can save analysis history.
- Swap keyword-based skill extraction for a spaCy NER model trained on
  resume data.
- Add a live job-search integration (e.g. via a jobs API) instead of the
  static `jobs.csv`.
- Add resume improvement suggestions using an LLM API.
- Deploy on Streamlit Community Cloud for a live demo link.

## Tech Stack

- **Frontend:** Streamlit
- **Backend/Logic:** Python
- **AI/ML:** scikit-learn (TF-IDF, cosine similarity), keyword-based NLP
- **Resume Parsing:** PyPDF2, python-docx
- **Visualization:** Plotly
- **Reporting:** fpdf2

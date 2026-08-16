"""
matcher.py
----------
Core matching engine: compares a resume against a set of job postings
using two signals combined into one score:

  1. TF-IDF + Cosine Similarity  -> overall textual/contextual closeness
  2. Explicit skill-set overlap  -> how many *required* skills are present

Final match % = weighted blend of the two (skills weighted higher, since
that's what recruiters / ATS systems actually filter on).
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.skills import extract_skills

# Weight given to skill-overlap vs. TF-IDF textual similarity when
# computing the final blended match score.
SKILL_WEIGHT = 0.65
TFIDF_WEIGHT = 0.35


def _skill_overlap_pct(resume_skills: set, required_skills: set) -> float:
    """% of the job's required skills that the resume actually has."""
    if not required_skills:
        return 0.0
    matched = resume_skills & required_skills
    return 100 * len(matched) / len(required_skills)


def compute_matches(resume_text: str, jobs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Given raw resume text and a DataFrame of jobs with columns
    ['job_title', 'description', 'required_skills'], return a DataFrame
    ranked by match_pct, with per-job matched/missing skill breakdowns.
    """
    resume_skills = set(extract_skills(resume_text))

    # --- TF-IDF similarity across resume + all job descriptions ---
    corpus = [resume_text] + jobs_df["description"].fillna("").tolist()
    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
    tfidf_matrix = vectorizer.fit_transform(corpus)
    resume_vector = tfidf_matrix[0:1]
    job_vectors = tfidf_matrix[1:]
    tfidf_scores = cosine_similarity(resume_vector, job_vectors).flatten()

    results = []
    for i, row in jobs_df.reset_index(drop=True).iterrows():
        required_skills = {
            s.strip().lower() for s in str(row["required_skills"]).split(",") if s.strip()
        }
        matched_skills = resume_skills & required_skills
        missing_skills = required_skills - resume_skills

        skill_pct = _skill_overlap_pct(resume_skills, required_skills)
        tfidf_pct = tfidf_scores[i] * 100

        blended = (SKILL_WEIGHT * skill_pct) + (TFIDF_WEIGHT * tfidf_pct)
        blended = round(min(blended, 100), 1)

        results.append({
            "job_title": row["job_title"],
            "match_pct": blended,
            "skill_overlap_pct": round(skill_pct, 1),
            "tfidf_pct": round(tfidf_pct, 1),
            "matched_skills": sorted(matched_skills),
            "missing_skills": sorted(missing_skills),
            "required_skills": sorted(required_skills),
        })

    results_df = pd.DataFrame(results).sort_values("match_pct", ascending=False)
    return results_df.reset_index(drop=True)


def resume_quality_score(stats: dict, num_skills_found: int) -> int:
    """
    A simple 'resume score out of 100' heuristic combining a few
    ATS-style signals. This is intentionally transparent/explainable
    rather than a black-box model.
    """
    score = 0

    # Content depth (up to 30 pts)
    score += min(stats["word_count"] / 400 * 30, 30)

    # Contact info present (up to 15 pts)
    score += 10 if stats["has_email"] else 0
    score += 5 if stats["has_phone"] else 0

    # Uses bullet points / structured formatting (up to 15 pts)
    score += min(stats["bullet_count"] / 10 * 15, 15)

    # Breadth of recognized skills (up to 40 pts)
    score += min(num_skills_found / 12 * 40, 40)

    return round(min(score, 100))

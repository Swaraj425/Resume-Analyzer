"""
skills.py
----------
Holds the master skill dictionary (categorized) and the function used to
extract skills from raw resume / job-description text.

Approach: keyword + phrase matching over a curated skill list.
This avoids needing a paid NER API and is transparent / explainable,
which is exactly what you want to be able to describe in an internship
interview.
"""

import re

# ---------------------------------------------------------------------
# Master skill list, grouped by category (used for the "skill distribution"
# chart and for nicer reporting). Add / edit freely.
# ---------------------------------------------------------------------
SKILL_DB = {
    "Programming Languages": [
        "python", "java", "c++", "c", "javascript", "typescript", "r",
        "sql", "php", "go", "kotlin", "swift", "matlab", "scala"
    ],
    "AI / Machine Learning": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "neural networks", "tensorflow", "keras", "pytorch",
        "scikit-learn", "sklearn", "opencv", "reinforcement learning",
        "transformers", "llm", "large language models", "regression",
        "classification", "clustering", "random forest", "xgboost"
    ],
    "Data Science": [
        "pandas", "numpy", "matplotlib", "seaborn", "plotly", "data analysis",
        "data visualization", "statistics", "data cleaning", "eda",
        "feature engineering", "tableau", "power bi", "excel"
    ],
    "Web Development": [
        "html", "css", "react", "angular", "vue", "node.js",
        "django", "flask", "streamlit", "fastapi", "bootstrap", "rest api",
        "web development", "javascript"
    ],
    "Database": [
        "mysql", "postgresql", "mongodb", "sqlite", "oracle", "database",
        "nosql", "firebase"
    ],
    "Tools / DevOps": [
        "git", "github", "docker", "kubernetes", "linux", "aws", "azure",
        "gcp", "ci/cd", "jenkins", "jira", "agile", "scrum"
    ],
}

# Flat lookup: skill -> category
_SKILL_TO_CATEGORY = {
    skill: category
    for category, skills in SKILL_DB.items()
    for skill in skills
}

# Sort longest-first so multi-word skills ("machine learning") are matched
# before their substrings ever could cause a partial/duplicate match.
_ALL_SKILLS_SORTED = sorted(_SKILL_TO_CATEGORY.keys(), key=len, reverse=True)


def extract_skills(text: str) -> list[str]:
    """
    Extract known skills from a block of text using word-boundary
    regex matching. Case-insensitive. Returns a de-duplicated list
    of skills in the canonical (lowercase) form found in SKILL_DB.
    """
    if not text:
        return []

    text_lower = text.lower()
    found = set()

    for skill in _ALL_SKILLS_SORTED:
        # Escape regex special chars (e.g. "c++"), use word boundaries
        # where sensible. For skills containing symbols like "c++" or
        # "node.js" a plain boundary won't work well, so fall back to
        # simple substring search for those.
        if re.search(r"[^\w\s]", skill):
            if skill in text_lower:
                found.add(skill)
        else:
            pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
            if re.search(pattern, text_lower):
                found.add(skill)

    return sorted(found)


def categorize_skills(skill_list: list[str]) -> dict[str, list[str]]:
    """Group a flat list of skills back into their categories."""
    grouped: dict[str, list[str]] = {}
    for skill in skill_list:
        category = _SKILL_TO_CATEGORY.get(skill, "Other")
        grouped.setdefault(category, []).append(skill)
    return grouped


def skill_distribution(skill_list: list[str]) -> dict[str, int]:
    """Return counts of skills per category, for charting."""
    grouped = categorize_skills(skill_list)
    return {cat: len(skills) for cat, skills in grouped.items()}

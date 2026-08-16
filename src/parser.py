"""
parser.py
---------
Handles turning an uploaded PDF/DOCX resume into plain text, and doing a
light-weight section split (Education / Experience / Projects /
Certifications) using header-line detection.
"""

import re
import io
from PyPDF2 import PdfReader
import docx


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file given as bytes."""
    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract all text from a DOCX file given as bytes."""
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs)


def extract_text(file_name: str, file_bytes: bytes) -> str:
    """Dispatch to the right extractor based on file extension."""
    lower = file_name.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF or DOCX resume.")


# Section headers we look for (case-insensitive). Each key maps to a list
# of alternative spellings/phrasings that might appear in a resume.
SECTION_HEADERS = {
    "education": ["education", "academic background", "academic qualifications"],
    "experience": ["experience", "work experience", "employment history", "internship"],
    "projects": ["projects", "academic projects", "personal projects"],
    "certifications": ["certifications", "certificates", "courses"],
    "skills": ["skills", "technical skills", "key skills"],
}


def split_into_sections(text: str) -> dict[str, str]:
    """
    Very lightweight section splitter: scans line by line, and whenever a
    line matches one of our known headers, starts collecting text under
    that section until the next header is found.
    """
    lines = text.split("\n")
    sections: dict[str, list[str]] = {key: [] for key in SECTION_HEADERS}
    current_section = None

    for line in lines:
        clean = line.strip().lower().strip(":")
        matched = None
        for section_key, aliases in SECTION_HEADERS.items():
            if clean in aliases or any(clean == alias for alias in aliases):
                matched = section_key
                break
        if matched:
            current_section = matched
            continue
        if current_section and line.strip():
            sections[current_section].append(line.strip())

    return {key: "\n".join(value) for key, value in sections.items()}


def basic_resume_stats(text: str) -> dict:
    """A few cheap heuristics used for the resume 'quality' score."""
    word_count = len(text.split())
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text))
    has_phone = bool(re.search(r"(\+?\d[\d\-\s()]{8,}\d)", text))
    bullet_count = len(re.findall(r"(?m)^\s*[•\-\*]", text))
    return {
        "word_count": word_count,
        "has_email": has_email,
        "has_phone": has_phone,
        "bullet_count": bullet_count,
    }

"""
report.py
---------
Builds a downloadable PDF report summarizing the resume analysis:
resume score, top job matches, and skill gap for the best-matching job.
"""

from fpdf import FPDF


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Resume Analysis Report", ln=True, align="C")
        self.ln(2)

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, title, ln=True)
        self.set_draw_color(200, 200, 200)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(3)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(0, 0, 0)
        self.set_x(self.l_margin)
        self.multi_cell(w=0, h=7, text=text)
        self.ln(2)


def build_report(resume_score: int, found_skills: list[str], matches_df, top_n: int = 5) -> bytes:
    pdf = ReportPDF()
    pdf.add_page()

    pdf.section_title("Overall Resume Score")
    pdf.body_text(f"{resume_score} / 100")

    pdf.section_title("Detected Skills")
    pdf.body_text(", ".join(found_skills) if found_skills else "No known skills detected.")

    pdf.section_title(f"Top {top_n} Job Matches")
    for _, row in matches_df.head(top_n).iterrows():
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, f"{row['job_title']} - {row['match_pct']}% match", ln=True)
        pdf.set_font("Helvetica", "", 10)
        matched = ", ".join(row["matched_skills"]) or "None"
        missing = ", ".join(row["missing_skills"]) or "None"
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(w=0, h=6, text=f"Matched skills: {matched}")
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(w=0, h=6, text=f"Missing skills: {missing}")
        pdf.ln(2)

    # fpdf2 returns a bytearray with dest='S'; normalize to bytes for Streamlit
    return bytes(pdf.output(dest="S"))

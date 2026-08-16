"""
app.py
------
AI Resume Analyzer & Job Recommendation System
Main Streamlit application.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.parser import extract_text, basic_resume_stats, split_into_sections
from src.skills import extract_skills, skill_distribution
from src.matcher import compute_matches, resume_quality_score
from src.report import build_report

st.set_page_config(
    page_title="AI Resume Analyzer & Job Recommendation System",
    page_icon="📄",
    layout="wide",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@500;600;700&display=swap');

    /* Global Typography & Background */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        color: #1e293b !important;
    }
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Reduce top padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #fffff;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebarHeader"] {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        position: relative;
        z-index: 999;
    }
    
    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
        margin-top: -4rem !important;
        position: relative;
        z-index: 1;
        background-color: transparent !important;
        
    }
    
    /* Metrics / Cards Styling */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricValue"] {
        color: #4f46e5;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.5rem !important;
        white-space: normal !important;
        line-height: 1.2 !important;
    }

    /* Tabs Styling */
    button[data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.05rem !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
        color: white !important;
        border-color: transparent !important;
    }

    /* Custom Badges/Chips */
    .skill-chip {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        margin: 0.25rem;
        background-color: #e0e7ff;
        color: #4338ca;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        border: 1px solid #c7d2fe;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* Health check items */
    .health-check {
        padding: 0.85rem;
        margin-bottom: 0.75rem;
        border-radius: 0.5rem;
        background: white;
        border: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-weight: 500;
        color: #334155;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .health-check.passed { border-left: 4px solid #10b981; }
    .health-check.failed { border-left: 4px solid #ef4444; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Load job dataset (cached so it's not re-read on every interaction)
# ---------------------------------------------------------------------
@st.cache_data
def load_jobs():
    return pd.read_csv("data/jobs.csv")


jobs_df = load_jobs()

# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------
st.sidebar.title("📄 Resume Analyzer")
st.sidebar.markdown(
    "Upload a resume (PDF or DOCX) and get:\n"
    "- Resume score\n"
    "- Extracted skills\n"
    "- Job match recommendations\n"
    "- Skill-gap analysis\n"
    "- Downloadable report"
)
uploaded_file = st.sidebar.file_uploader("Upload your resume", type=["pdf", "docx"])
top_n = st.sidebar.slider("Number of job recommendations to show", 3, 10, 5)

st.title("AI Resume Analyzer & Job Recommendation System")

if uploaded_file is not None:
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
            // On mobile, Streamlit closes the sidebar when the ESC key is pressed
            const evt = new KeyboardEvent('keydown', { 'key': 'Escape', 'keyCode': 27, 'which': 27, 'bubbles': true });
            window.parent.document.dispatchEvent(evt);
            
            // Fallback: look for the X close button specifically used on mobile
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {
                if(btn.innerHTML.includes('svg') && btn.getAttribute('kind') === 'header') {
                    btn.click();
                }
            });
        </script>
        """, height=0
    )

if uploaded_file is None:
    st.info("👈 Upload a resume from the sidebar to get started.")
    st.markdown("#### Available job roles in this demo dataset")
    st.dataframe(jobs_df[["job_title", "required_skills"]], use_container_width=True)
    st.stop()

# ---------------------------------------------------------------------
# Extract text
# ---------------------------------------------------------------------
with st.spinner("Reading resume..."):
    file_bytes = uploaded_file.read()
    try:
        resume_text = extract_text(uploaded_file.name, file_bytes)
    except ValueError as e:
        st.error(str(e))
        st.stop()

if not resume_text.strip():
    st.error("Couldn't extract any text from this file. Try a different resume file "
              "(scanned/image-only PDFs aren't supported).")
    st.stop()

# ---------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------
with st.spinner("Analyzing resume..."):
    found_skills = extract_skills(resume_text)
    stats = basic_resume_stats(resume_text)
    score = resume_quality_score(stats, len(found_skills))
    sections = split_into_sections(resume_text)
    matches_df = compute_matches(resume_text, jobs_df)

tab_dashboard, tab_jobs, tab_gap, tab_report, tab_raw = st.tabs(
    ["📊 Dashboard", "🎯 Job Recommendations", "🧩 Skill Gap", "📥 Report", "📄 Raw Text"]
)

# ---------------------------------------------------------------------
# Dashboard tab
# ---------------------------------------------------------------------
with tab_dashboard:
    col1, col2, col3 = st.columns(3)
    col1.metric("Resume Score", f"{score} / 100")
    col2.metric("Skills Detected", len(found_skills))
    col3.metric("Best Match", f"{matches_df.iloc[0]['job_title']} ({matches_df.iloc[0]['match_pct']}%)")

    st.markdown("#### Detected Skills")
    if found_skills:
        chips_html = "".join([f'<span class="skill-chip">{s}</span>' for s in found_skills])
        st.markdown(chips_html, unsafe_allow_html=True)
    else:
        st.warning("No known skills detected. Consider adding a clear 'Skills' section.")

    colA, colB = st.columns(2, gap="large")
    
    with colA:
        st.markdown("#### Skill Category Distribution")
        dist = skill_distribution(found_skills)
        if dist:
            fig = px.pie(
                names=list(dist.keys()),
                values=list(dist.values()),
                title="Skills by Category",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", 
                paper_bgcolor="rgba(0,0,0,0)",
                font_family="Inter",
                margin=dict(t=40, b=40, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No categorized skills to chart yet.")

    with colB:
        st.markdown("#### Resume Health Checks")
        checks = {
            "Contains email address": stats["has_email"],
            "Contains phone number": stats["has_phone"],
            "Uses bullet points": stats["bullet_count"] > 0,
            "Sufficient length (200+ words)": stats["word_count"] >= 200,
        }
        for label, passed in checks.items():
            icon = "✅" if passed else "❌"
            status_class = "passed" if passed else "failed"
            st.markdown(f'<div class="health-check {status_class}"><span>{icon}</span> {label}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Job Recommendations tab
# ---------------------------------------------------------------------
with tab_jobs:
    st.markdown("#### Top Job Matches")
    top_matches = matches_df.head(top_n)

    fig_bar = px.bar(
        top_matches.sort_values("match_pct"),
        x="match_pct",
        y="job_title",
        orientation="h",
        text="match_pct",
        labels={"match_pct": "Match %", "job_title": "Job Role"},
        title="Match Percentage by Job Role",
        color="match_pct",
        color_continuous_scale="Purples"
    )
    fig_bar.update_layout(
        height=450,
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="Inter",
        xaxis_visible=False,
        coloraxis_showscale=False,
        margin=dict(t=40, b=10, l=10, r=10)
    )
    fig_bar.update_traces(texttemplate='%{text}%', textposition='auto')
    st.plotly_chart(fig_bar, use_container_width=True)

    for _, row in top_matches.iterrows():
        with st.expander(f"{row['job_title']} — {row['match_pct']}% match"):
            c1, c2 = st.columns(2)
            c1.markdown("**✅ Matched skills**")
            c1.write(", ".join(row["matched_skills"]) or "None")
            c2.markdown("**❌ Missing skills**")
            c2.write(", ".join(row["missing_skills"]) or "None")
            st.progress(min(int(row["match_pct"]), 100) / 100)

# ---------------------------------------------------------------------
# Skill Gap tab
# ---------------------------------------------------------------------
with tab_gap:
    col_gap1, col_gap2 = st.columns(2, gap="large")
    
    with col_gap1:
        st.markdown("#### Skill Gap Analysis for Best Match")
        best = matches_df.iloc[0]
        st.write(f"Best matching role: **{best['job_title']}** ({best['match_pct']}%)")

        if best["missing_skills"]:
            st.markdown("You're missing the following skills for this role:")
            missing_chips = "".join([f'<span class="skill-chip" style="background-color:#fee2e2;color:#991b1b;border-color:#fecaca">{s}</span>' for s in best["missing_skills"]])
            st.markdown(missing_chips, unsafe_allow_html=True)
            st.markdown("<br>**Suggestion:** consider adding relevant projects or certifications "
                         "in these areas to improve your match score.", unsafe_allow_html=True)
        else:
            st.success("You already have all the required skills for this role! 🎉")

    with col_gap2:
        st.markdown("#### Compare Against a Specific Job")
        job_choice = st.selectbox("Choose a job role", matches_df["job_title"])
        chosen = matches_df[matches_df["job_title"] == job_choice].iloc[0]
        c1, c2 = st.columns(2)
        c1.metric("Match %", f"{chosen['match_pct']}%")
        c2.metric("Skill Overlap", f"{chosen['skill_overlap_pct']}%")
        
        st.write("**Matched:**")
        if chosen["matched_skills"]:
            m_chips = "".join([f'<span class="skill-chip" style="background-color:#d1fae5;color:#065f46;border-color:#a7f3d0">{s}</span>' for s in chosen["matched_skills"]])
            st.markdown(m_chips, unsafe_allow_html=True)
        else:
            st.write("None")
            
        st.write("**Missing:**")
        if chosen["missing_skills"]:
            m_chips2 = "".join([f'<span class="skill-chip" style="background-color:#fee2e2;color:#991b1b;border-color:#fecaca">{s}</span>' for s in chosen["missing_skills"]])
            st.markdown(m_chips2, unsafe_allow_html=True)
        else:
            st.write("None")

# ---------------------------------------------------------------------
# Report tab
# ---------------------------------------------------------------------
with tab_report:
    st.markdown("#### Download Your Analysis Report")
    st.write("Generates a PDF summarizing your resume score, detected skills, "
              "and top job matches with skill gaps.")
    pdf_bytes = build_report(score, found_skills, matches_df, top_n=top_n)
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_bytes,
        file_name="resume_analysis_report.pdf",
        mime="application/pdf",
    )

# ---------------------------------------------------------------------
# Raw text / sections tab (useful for debugging / demo)
# ---------------------------------------------------------------------
with tab_raw:
    st.markdown("#### Extracted Sections")
    for name, content in sections.items():
        with st.expander(name.title()):
            st.text(content or "Not detected")

    st.markdown("#### Full Extracted Text")
    st.text_area("Raw resume text", resume_text, height=300)



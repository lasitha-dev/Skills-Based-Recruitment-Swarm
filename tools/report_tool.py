"""
ReportGeneratorTool: Formats and generates hiring recommendation PDF reports.

This tool takes recommendation data from Agent 4 (Recruitment Lead) and
generates a professionally styled PDF report with candidate evaluation details,
assessment scores, and final hiring recommendation. Reports are saved
to local files for documentation and audit trails.

Author: G.A. Sandaru (Agent 4: Recruitment Lead)
"""

import logging
import os
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional

from xhtml2pdf import pisa

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CSS Stylesheet – embedded directly for portability
# ---------------------------------------------------------------------------
_REPORT_CSS = """
@page {
    size: A4;
    margin: 2cm 2.5cm;
    @frame footer {
        -pdf-frame-content: page-footer;
        bottom: 0;
        height: 40px;
        margin-left: 0;
        margin-right: 0;
    }
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11px;
    color: #1a1a2e;
    line-height: 1.5;
}

/* ---- Header / Title ---- */
.report-header {
    background-color: #0f3460;
    color: #ffffff;
    padding: 24px 28px;
    margin: -10px -10px 20px -10px;
    border-radius: 4px;
}

.report-header h1 {
    font-size: 22px;
    margin: 0 0 4px 0;
    letter-spacing: 0.5px;
}

.report-header .subtitle {
    font-size: 11px;
    color: #a4b3cc;
    margin: 0;
}

.report-header .generated {
    font-size: 9px;
    color: #8899b0;
    margin: 8px 0 0 0;
}

/* ---- Section headings ---- */
h2 {
    font-size: 15px;
    color: #0f3460;
    border-bottom: 2px solid #e94560;
    padding-bottom: 4px;
    margin: 20px 0 10px 0;
}

h3 {
    font-size: 12px;
    color: #16213e;
    margin: 12px 0 6px 0;
}

/* ---- Candidate info card ---- */
.info-card {
    background-color: #f0f4f8;
    padding: 14px 18px;
    border-left: 4px solid #0f3460;
    margin-bottom: 16px;
}

.info-card p {
    margin: 3px 0;
    font-size: 11px;
}

.info-card .label {
    color: #555;
    font-weight: bold;
}

/* ---- Score table ---- */
.score-table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 16px 0;
}

.score-table th {
    background-color: #0f3460;
    color: #ffffff;
    text-align: left;
    padding: 8px 12px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.score-table td {
    padding: 8px 12px;
    border-bottom: 1px solid #dce3ea;
    font-size: 11px;
}

.score-table tr:nth-child(even) td {
    background-color: #f8fafc;
}

.score-good { color: #27ae60; font-weight: bold; }
.score-moderate { color: #f39c12; font-weight: bold; }
.score-low { color: #e74c3c; font-weight: bold; }

/* ---- Skills ---- */
.skill-tag {
    display: inline-block;
    background-color: #e8f0fe;
    color: #0f3460;
    padding: 3px 10px;
    margin: 2px 3px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: bold;
}

.skill-gap-tag {
    display: inline-block;
    background-color: #fde8e8;
    color: #c0392b;
    padding: 3px 10px;
    margin: 2px 3px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: bold;
}

/* ---- Lists ---- */
ul {
    padding-left: 18px;
    margin: 4px 0;
}

li {
    margin: 2px 0;
    font-size: 11px;
}

/* ---- Recommendation banner ---- */
.recommendation-box {
    padding: 16px 20px;
    margin: 16px 0;
    border-radius: 4px;
}

.rec-hire {
    background-color: #d5f5e3;
    border-left: 5px solid #27ae60;
}

.rec-conditional {
    background-color: #fef9e7;
    border-left: 5px solid #f39c12;
}

.rec-not-recommended {
    background-color: #fde8e8;
    border-left: 5px solid #e74c3c;
}

.recommendation-box h3 {
    margin: 0 0 6px 0;
    font-size: 14px;
}

.recommendation-box p {
    margin: 4px 0;
    font-size: 11px;
}

/* ---- Market benchmarks ---- */
.benchmark-table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 12px 0;
}

.benchmark-table th {
    background-color: #16213e;
    color: #fff;
    text-align: left;
    padding: 6px 10px;
    font-size: 10px;
}

.benchmark-table td {
    padding: 6px 10px;
    border-bottom: 1px solid #e0e0e0;
    font-size: 10px;
}

/* ---- Footer ---- */
.footer {
    text-align: center;
    font-size: 8px;
    color: #999;
    border-top: 1px solid #ddd;
    padding-top: 6px;
}

/* ---- Separator ---- */
hr {
    border: none;
    border-top: 1px solid #dce3ea;
    margin: 14px 0;
}
"""


def generate_report(recommendation_data: Dict[str, Any]) -> str:
    """
    Generate a styled PDF report from recommendation data and save to file.

    Args:
        recommendation_data: Dictionary containing recommendation details.

    Returns:
        str: Absolute path to the saved PDF report file.

    Raises:
        ValueError: If required fields are missing.
        IOError: If report file cannot be written.
    """
    logger.info("Starting PDF report generation process")

    if not isinstance(recommendation_data, dict):
        raise ValueError("recommendation_data must be a dictionary")

    candidate_name = recommendation_data.get("candidate_name")
    recommendation = recommendation_data.get("recommendation")

    if not candidate_name:
        raise ValueError("recommendation_data must contain 'candidate_name'")
    if not recommendation:
        raise ValueError("recommendation_data must contain 'recommendation'")

    logger.info(f"Generating PDF report for candidate: {candidate_name}")

    try:
        html_content = _build_report_html(recommendation_data)
        report_path = _save_report_as_pdf(candidate_name, html_content)
        logger.info(f"PDF report saved to: {report_path}")
        return report_path
    except IOError as e:
        logger.error(f"IO error while generating report: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        raise


def _score_css_class(score: Optional[float]) -> str:
    """Return a CSS class based on score value."""
    if score is None:
        return ""
    if score >= 0.7:
        return "score-good"
    if score >= 0.4:
        return "score-moderate"
    return "score-low"


def _format_pct(score: Optional[float]) -> str:
    """Format score as percentage string."""
    if score is None:
        return "N/A"
    try:
        return f"{float(score) * 100:.1f}%"
    except (ValueError, TypeError):
        return "N/A"


def _recommendation_css_class(rec: str) -> str:
    """Map recommendation label to CSS class."""
    rec_lower = rec.lower()
    if "not" in rec_lower or "reject" in rec_lower:
        return "rec-not-recommended"
    if "conditional" in rec_lower or "maybe" in rec_lower or "consider" in rec_lower:
        return "rec-conditional"
    return "rec-hire"


def _build_report_html(data: Dict[str, Any]) -> str:
    """Build complete HTML document for the report."""

    candidate_name = data.get("candidate_name", "Unknown Candidate")
    recommendation = data.get("recommendation", "Pending Review")
    reason = data.get("recommendation_reason", "No reasoning provided.")
    strength_score = data.get("strength_score")
    technical_score = data.get("technical_score")
    market_fit_score = data.get("market_fit_score")
    experience_years = data.get("experience_years")
    skills = data.get("skills", [])
    education = data.get("education")
    salary_range = data.get("salary_range")
    market_benchmarks = data.get("market_benchmarks")
    interview_performance = data.get("interview_performance")
    skill_gaps = data.get("skill_gaps", [])

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Build skills HTML ---
    skills_html = ""
    if skills:
        skills_html = "<h3>Key Skills</h3><div>"
        for s in skills:
            skills_html += f'<span class="skill-tag">{_esc(str(s))}</span> '
        skills_html += "</div>"

    # --- Build scores table ---
    scores_rows = ""
    score_items = [
        ("Resume Strength", strength_score),
        ("Technical Skills", technical_score),
        ("Market Fit", market_fit_score),
    ]
    for label, val in score_items:
        pct = _format_pct(val)
        css = _score_css_class(val)
        scores_rows += f'<tr><td>{label}</td><td class="{css}">{pct}</td></tr>\n'

    # --- Build market benchmarks ---
    market_html = ""
    if market_benchmarks:
        market_html = "<h3>Market Benchmarks</h3><table class='benchmark-table'>"
        market_html += "<tr><th>Metric</th><th>Value</th></tr>"
        sr = market_benchmarks.get("salary_range")
        if sr:
            market_html += f"<tr><td>Salary Range</td><td>{_esc(str(sr))}</td></tr>"
        demand = market_benchmarks.get("role_demand")
        if demand:
            market_html += f"<tr><td>Role Demand</td><td>{_esc(str(demand))}</td></tr>"
        trend = market_benchmarks.get("market_trend")
        if trend:
            market_html += f"<tr><td>Market Trend</td><td>{_esc(str(trend))}</td></tr>"
        market_html += "</table>"

    # --- Build interview performance ---
    interview_html = ""
    if interview_performance:
        interview_html = "<h3>Interview Performance</h3><ul>"
        qa = interview_performance.get("questions_answered")
        total = interview_performance.get("total_questions")
        if qa is not None and total is not None:
            interview_html += f"<li><strong>Questions Answered:</strong> {qa}/{total}</li>"
        quality = interview_performance.get("response_quality")
        if quality:
            interview_html += f"<li><strong>Response Quality:</strong> {_esc(str(quality))}</li>"
        notes = interview_performance.get("notes")
        if notes:
            interview_html += f"<li><strong>Interviewer Notes:</strong> {_esc(str(notes))}</li>"
        interview_html += "</ul>"

    # --- Skill gaps ---
    gaps_html = ""
    if skill_gaps:
        gaps_html = "<h3>Skill Gaps / Development Areas</h3><div>"
        for g in skill_gaps:
            gaps_html += f'<span class="skill-gap-tag">{_esc(str(g))}</span> '
        gaps_html += "</div>"

    # --- Recommendation banner ---
    rec_css = _recommendation_css_class(recommendation)

    # --- Compose full HTML ---
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
{_REPORT_CSS}
</style>
</head>
<body>
    <!-- Header -->
    <div class="report-header">
        <h1>Hiring Recommendation Report</h1>
        <p class="subtitle">Multi-Agent Recruitment Swarm (MARS)</p>
        <p class="generated">Generated: {timestamp}</p>
    </div>

    <!-- Candidate Information -->
    <h2>Candidate Information</h2>
    <div class="info-card">
        <p><span class="label">Name:</span> {_esc(candidate_name)}</p>
        {f'<p><span class="label">Experience:</span> {experience_years} years</p>' if experience_years is not None else ''}
        {f'<p><span class="label">Education:</span> {_esc(str(education))}</p>' if education else ''}
        {f'<p><span class="label">Expected Salary:</span> {_esc(str(salary_range))}</p>' if salary_range else ''}
    </div>

    {skills_html}

    <!-- Evaluation Scores -->
    <h2>Evaluation Summary</h2>
    <table class="score-table">
        <tr>
            <th>Assessment Area</th>
            <th>Score</th>
        </tr>
        {scores_rows}
    </table>

    {market_html}
    {interview_html}
    {gaps_html}

    <hr/>

    <!-- Final Recommendation -->
    <h2>Final Recommendation</h2>
    <div class="recommendation-box {rec_css}">
        <h3>Decision: {_esc(recommendation)}</h3>
        <p><strong>Reasoning:</strong> {_esc(reason)}</p>
    </div>

    <!-- Footer -->
    <div id="page-footer" class="footer">
        <p>This report was generated by the Multi-Agent Recruitment Swarm (MARS) &bull; For questions or appeals, contact the HR department.</p>
    </div>
</body>
</html>"""

    return html


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _save_report_as_pdf(candidate_name: str, html_content: str) -> str:
    """Convert HTML to PDF and save to the data/reports directory.

    Args:
        candidate_name: Name of the candidate (used in filename).
        html_content: The complete HTML string of the report.

    Returns:
        str: Absolute path to the saved PDF file.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(project_root, "data", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(
        c if c.isalnum() or c in (" ", "_", "-") else "_" for c in candidate_name
    ).replace(" ", "_")

    filename = f"recommendation_{safe_name}_{timestamp}.pdf"
    filepath = os.path.join(reports_dir, filename)

    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer, encoding="utf-8")

    if pisa_status.err:
        raise IOError(f"xhtml2pdf returned errors while generating PDF: {pisa_status.err}")

    with open(filepath, "wb") as f:
        f.write(pdf_buffer.getvalue())

    if not os.path.exists(filepath):
        raise IOError(f"PDF report file was not created: {filepath}")

    file_size = os.path.getsize(filepath)
    logger.info(f"PDF report saved to: {filepath} ({file_size} bytes)")

    return os.path.abspath(filepath)


# Export public interface
__all__ = ["generate_report"]

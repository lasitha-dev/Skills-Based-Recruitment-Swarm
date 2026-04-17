"""
ReportGeneratorTool: Formats and generates hiring recommendation reports.

This tool takes recommendation data from Agent 4 (Recruitment Lead) and
generates a structured markdown report with candidate evaluation details,
assessment scores, and final hiring recommendation. Reports are saved
to local files for documentation and audit trails.

Author: G.A. Sandaru (Agent 4: Recruitment Lead)
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_report(recommendation_data: Dict[str, Any]) -> str:
    """
    Generate a formatted markdown report from recommendation data and save to file.

    This function takes structured recommendation data from Agent 4 and creates
    a professional markdown report including candidate evaluation, scores,
    assessment details, and final hiring recommendation. The report is saved
    to the local 'data/' directory with a timestamped filename.

    Args:
        recommendation_data: Dictionary containing recommendation details.
            Expected keys:
                - candidate_name (str): Full name of the candidate
                - recommendation (str): Final recommendation label
                - recommendation_reason (str): Explanation for recommendation
                - strength_score (float): Resume/profile strength score (0.0-1.0)
                - technical_score (float): Technical evaluation score (0.0-1.0)
                - market_fit_score (float): Market fit score (0.0-1.0)
                - experience_years (int): Years of professional experience
                - skills (list, optional): List of key skills
                - education (str, optional): Education background
                - salary_range (str, optional): Expected salary range
                - market_benchmarks (dict, optional): Market data benchmarks
                - interview_performance (dict, optional): Interview details
                - skill_gaps (list, optional): Missing/weak skills

    Returns:
        str: Absolute path to the saved report file.

    Raises:
        ValueError: If required fields (candidate_name, recommendation) are missing.
        IOError: If report file cannot be written.
        KeyError: If recommendation_data structure is invalid.

    Example:
        >>> data = {
        ...     "candidate_name": "Alice Smith",
        ...     "recommendation": "Strong Hire",
        ...     "recommendation_reason": "Excellent technical skills and experience.",
        ...     "strength_score": 0.85,
        ...     "technical_score": 0.9,
        ...     "market_fit_score": 0.8,
        ...     "experience_years": 7,
        ...     "skills": ["Python", "SQL", "Docker"]
        ... }
        >>> report_path = generate_report(data)
        >>> print(f"Report saved to: {report_path}")
    """
    logger.info("Starting report generation process")
    
    # Validate required fields
    if not isinstance(recommendation_data, dict):
        logger.error(f"Invalid recommendation_data type: {type(recommendation_data)}")
        raise ValueError("recommendation_data must be a dictionary")
    
    candidate_name = recommendation_data.get("candidate_name")
    recommendation = recommendation_data.get("recommendation")
    
    if not candidate_name:
        logger.error("Missing required field: candidate_name")
        raise ValueError("recommendation_data must contain 'candidate_name'")
    
    if not recommendation:
        logger.error("Missing required field: recommendation")
        raise ValueError("recommendation_data must contain 'recommendation'")
    
    logger.info(f"Generating report for candidate: {candidate_name}")
    
    try:
        # Build markdown report
        report_content = _build_report_markdown(recommendation_data)
        
        # Save report to file
        report_path = _save_report_to_file(candidate_name, report_content)
        
        logger.info(f"Report successfully generated and saved to: {report_path}")
        return report_path
        
    except IOError as e:
        logger.error(f"IO error while generating report: {e}")
        raise IOError(f"Failed to write report file: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        raise


def _build_report_markdown(recommendation_data: Dict[str, Any]) -> str:
    """
    Build the markdown content for the hiring recommendation report.

    Constructs a well-formatted markdown report with all evaluation details
    from the recommendation data. Handles missing fields gracefully by
    omitting sections when data is not available.

    Args:
        recommendation_data: Dictionary with candidate evaluation data.

    Returns:
        str: Complete markdown report content.
    """
    logger.debug("Building markdown report content")
    
    # Extract data with safe defaults
    candidate_name: str = recommendation_data.get("candidate_name", "Unknown Candidate")
    recommendation: str = recommendation_data.get("recommendation", "Pending Review")
    recommendation_reason: str = recommendation_data.get(
        "recommendation_reason",
        "No reasoning provided."
    )
    strength_score: Optional[float] = recommendation_data.get("strength_score")
    technical_score: Optional[float] = recommendation_data.get("technical_score")
    market_fit_score: Optional[float] = recommendation_data.get("market_fit_score")
    experience_years: Optional[int] = recommendation_data.get("experience_years")
    skills: Optional[list] = recommendation_data.get("skills", [])
    education: Optional[str] = recommendation_data.get("education")
    salary_range: Optional[str] = recommendation_data.get("salary_range")
    market_benchmarks: Optional[dict] = recommendation_data.get("market_benchmarks")
    interview_performance: Optional[dict] = recommendation_data.get("interview_performance")
    skill_gaps: Optional[list] = recommendation_data.get("skill_gaps", [])
    
    # Start building report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines = [
        "# Hiring Recommendation Report",
        "",
        f"**Generated:** {timestamp}",
        "",
        "---",
        "",
    ]
    
    # Candidate Information Section
    report_lines.extend([
        "## Candidate Information",
        "",
        f"**Name:** {candidate_name}",
    ])
    
    if experience_years is not None:
        report_lines.append(f"**Experience:** {experience_years} years")
    
    if education:
        report_lines.append(f"**Education:** {education}")
    
    report_lines.append("")
    
    # Skills Section
    if skills:
        report_lines.extend([
            "### Key Skills",
            ""
        ])
        for skill in skills:
            report_lines.append(f"- {skill}")
        report_lines.append("")
    
    report_lines.append("---")
    report_lines.append("")
    
    # Evaluation Scores Section
    report_lines.extend([
        "## Evaluation Summary",
        ""
    ])
    
    if strength_score is not None:
        strength_pct = _format_score_percentage(strength_score)
        report_lines.append(f"**Resume Strength Score:** {strength_pct}")
    
    if technical_score is not None:
        technical_pct = _format_score_percentage(technical_score)
        report_lines.append(f"**Technical Skills Score:** {technical_pct}")
    
    if market_fit_score is not None:
        market_pct = _format_score_percentage(market_fit_score)
        report_lines.append(f"**Market Fit Score:** {market_pct}")
    
    report_lines.append("")
    
    # Market Benchmarks Section
    if market_benchmarks:
        report_lines.extend([
            "### Market Benchmarks",
            ""
        ])
        
        salary_bench = market_benchmarks.get("salary_range")
        if salary_bench:
            report_lines.append(f"- **Salary Range:** {salary_bench}")
        
        demand = market_benchmarks.get("role_demand")
        if demand:
            report_lines.append(f"- **Role Demand:** {demand}")
        
        trend = market_benchmarks.get("market_trend")
        if trend:
            report_lines.append(f"- **Market Trend:** {trend}")
        
        report_lines.append("")
    
    # Interview Performance Section
    if interview_performance:
        report_lines.extend([
            "### Interview Performance",
            ""
        ])
        
        questions_answered = interview_performance.get("questions_answered")
        total_questions = interview_performance.get("total_questions")
        if questions_answered is not None and total_questions is not None:
            report_lines.append(
                f"- **Questions Answered:** {questions_answered}/{total_questions}"
            )
        
        response_quality = interview_performance.get("response_quality")
        if response_quality:
            report_lines.append(f"- **Response Quality:** {response_quality}")
        
        notes = interview_performance.get("notes")
        if notes:
            report_lines.append(f"- **Interviewer Notes:** {notes}")
        
        report_lines.append("")
    
    # Skill Gaps Section
    if skill_gaps:
        report_lines.extend([
            "### Skill Gaps / Development Areas",
            ""
        ])
        for gap in skill_gaps:
            report_lines.append(f"- {gap}")
        report_lines.append("")
    
    if salary_range and not market_benchmarks:
        report_lines.extend([
            f"**Candidate Expected Salary:** {salary_range}",
            ""
        ])
    
    report_lines.append("---")
    report_lines.append("")
    
    # Final Recommendation Section
    report_lines.extend([
        "## Final Recommendation",
        "",
        f"### **Decision: {recommendation}**",
        "",
        f"**Reasoning:** {recommendation_reason}",
        "",
    ])
    
    # Footer
    report_lines.extend([
        "---",
        "",
        "*This report was generated by the Multi-Agent Recruitment Swarm (MARS).*",
        "*For questions or appeals, contact the HR department.*",
    ])
    
    markdown_report = "\n".join(report_lines)
    logger.debug("Markdown report content built successfully")
    
    return markdown_report


def _format_score_percentage(score: Optional[float]) -> str:
    """
    Format a numerical score (0.0-1.0) as a percentage string.

    Args:
        score: Score value between 0.0 and 1.0.

    Returns:
        str: Formatted percentage (e.g., "85.0%") or "N/A" if score is None.
    """
    if score is None:
        return "N/A"
    
    try:
        score_float = float(score)
        percentage = score_float * 100
        return f"{percentage:.1f}%"
    except (ValueError, TypeError):
        logger.warning(f"Could not format score: {score}")
        return "N/A"


def _save_report_to_file(candidate_name: str, report_content: str) -> str:
    """
    Save the markdown report to a timestamped file in the data directory.

    Creates the 'data/reports/' directory if it doesn't exist, then saves
    the report with a timestamped filename for easy organization and retrieval.

    Args:
        candidate_name: Name of the candidate (used in filename).
        report_content: The markdown report content to save.

    Returns:
        str: Absolute path to the saved report file.

    Raises:
        IOError: If the file cannot be written.
    """
    logger.debug(f"Preparing to save report for candidate: {candidate_name}")
    
    try:
        # Ensure data/reports directory exists (use absolute path for robustness)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(project_root, "data", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        logger.debug(f"Reports directory ensured: {reports_dir}")
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize candidate name for filename (remove special characters)
        safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' 
                           for c in candidate_name)
        safe_name = safe_name.replace(" ", "_")
        
        filename = f"recommendation_{safe_name}_{timestamp}.md"
        filepath = os.path.join(reports_dir, filename)
        
        # Write report to file
        with open(filepath, 'w', encoding='utf-8') as report_file:
            report_file.write(report_content)
        
        # Verify file was written
        if not os.path.exists(filepath):
            raise IOError(f"Report file was not created: {filepath}")
        
        file_size = os.path.getsize(filepath)
        logger.info(
            f"Report successfully saved to: {filepath} ({file_size} bytes)"
        )
        
        return os.path.abspath(filepath)
        
    except OSError as e:
        logger.error(f"OS error while saving report: {e}")
        raise IOError(f"Failed to save report file: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error while saving report: {e}")
        raise IOError(f"Unexpected error during file save: {e}") from e


# Export public interface
__all__ = ['generate_report']

"""
Agent 4: Recruitment Lead

This agent synthesizes evaluation data from Agents 1 (Profile Parser),
Agent 2 (Market Scout), and Agent 3 (Tech Evaluator) to generate a final
hiring recommendation. It applies rule-based logic to decide between five
recommendation categories and generates a professional report.

Author: G.A. Sandaru (Agent 4: Recruitment Lead)
"""

import logging
from typing import Dict, Any, Optional, Tuple

from tools.report_tool import generate_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Recommendation label constants (exact strings required)
STRONG_HIRE = "Strong Hire"
PROCEED_TO_INTERVIEW = "Proceed to Interview"
CONSIDER_WITH_UPSKILLING = "Consider with Upskilling"
NOT_RECOMMENDED = "Not Recommended"
INSUFFICIENT_DATA = "Insufficient data"


def lead_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesize candidate evaluation data and generate final hiring recommendation.

    This agent reads cumulative state from Agents 1, 2, and 3, applies
    rule-based decision logic to evaluate candidate fit, and generates
    a comprehensive hiring recommendation with supporting report.

    The recommendation is based on three key scores:
    - Resume/Profile Strength (0.0-1.0) from Agent 1
    - Technical Skills (0.0-1.0) from Agent 3
    - Market Fit (0.0-1.0) from Agent 2

    Args:
        state: Shared AgentState dictionary containing:
            - candidate_name (str): Full name of the candidate
            - parsed_resume (dict): Output from Agent 1 with profile data
            - market_data (dict): Output from Agent 2 with market benchmarks
            - technical_evaluation (dict): Output from Agent 3 with tech scores

    Returns:
        Dict containing state updates:
            - final_recommendation (str): One of five exact labels
            - recommendation_reason (str): Explanation for the recommendation
            - report_path (str): Path to generated report file

    Example:
        >>> state = {
        ...     "candidate_name": "Alice Smith",
        ...     "parsed_resume": {"strength_score": 0.8, "experience_years": 5},
        ...     "market_data": {"market_fit_score": 0.7},
        ...     "technical_evaluation": {"technical_score": 0.75}
        ... }
        >>> result = lead_agent(state)
        >>> print(result["final_recommendation"])
        "Proceed to Interview"
    """
    # Type check at the very beginning
    if not isinstance(state, dict):
        logger.warning("Invalid input state type")
        return {
            "final_recommendation": INSUFFICIENT_DATA,
            "recommendation_reason": "Invalid input state",
            "report_path": ""
        }
    
    logger.info("=" * 60)
    logger.info("Agent 4 (Recruitment Lead) started")
    logger.info(f"Processing candidate: {state.get('candidate_name', 'Unknown')}")
    
    try:
        logger.debug(f"State keys received: {list(state.keys())}")
        
        # Extract and validate required fields
        candidate_name: str = state.get("candidate_name")
        parsed_resume: Optional[Dict] = state.get("parsed_resume")
        market_data: Optional[Dict] = state.get("market_data")
        technical_evaluation: Optional[Dict] = state.get("technical_evaluation")
        
        # Check for missing critical data
        if not all([candidate_name, parsed_resume, market_data, technical_evaluation]):
            missing_fields = []
            if not candidate_name:
                missing_fields.append("candidate_name")
            if not parsed_resume:
                missing_fields.append("parsed_resume")
            if not market_data:
                missing_fields.append("market_data")
            if not technical_evaluation:
                missing_fields.append("technical_evaluation")
            
            logger.warning(f"Missing critical state fields: {missing_fields}")
            
            reason = (
                f"Cannot generate recommendation. Missing data from: "
                f"{', '.join(missing_fields)}"
            )
            
            state_update = {
                "final_recommendation": INSUFFICIENT_DATA,
                "recommendation_reason": reason,
                "report_path": ""
            }
            
            logger.info(f"Result: {INSUFFICIENT_DATA}")
            return state_update
        
        # Extract scores from provided data
        strength_score, tech_score, market_score, years_exp = _extract_scores(
            parsed_resume, technical_evaluation, market_data
        )
        
        # Check if we have sufficient score data
        if strength_score is None or tech_score is None or market_score is None:
            missing_scores = []
            if strength_score is None:
                missing_scores.append("strength_score")
            if tech_score is None:
                missing_scores.append("technical_score")
            if market_score is None:
                missing_scores.append("market_fit_score")
            
            logger.warning(f"Missing score data: {missing_scores}")
            
            reason = (
                f"Incomplete evaluation scores. Missing: "
                f"{', '.join(missing_scores)}"
            )
            
            state_update = {
                "final_recommendation": INSUFFICIENT_DATA,
                "recommendation_reason": reason,
                "report_path": ""
            }
            
            logger.info(f"Result: {INSUFFICIENT_DATA}")
            return state_update
        
        logger.debug(
            f"Extracted scores - Strength: {strength_score:.2f}, "
            f"Technical: {tech_score:.2f}, Market: {market_score:.2f}, "
            f"Years: {years_exp}"
        )
        
        # Apply decision logic
        recommendation, reason = _determine_recommendation(
            strength_score, tech_score, market_score, years_exp
        )
        
        logger.info(f"Decision: {recommendation}")
        logger.info(f"Reason: {reason}")
        
        # Prepare data for report generation
        report_data = _prepare_report_data(
            state, recommendation, reason,
            strength_score, tech_score, market_score
        )
        
        # Generate report
        logger.info("Generating hiring recommendation report...")
        try:
            report_path = generate_report(report_data)
            logger.info(f"Report generated: {report_path}")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            report_path = ""
        
        # Prepare state update
        state_update = {
            "final_recommendation": recommendation,
            "recommendation_reason": reason,
            "report_path": report_path
        }
        
        logger.info("=" * 60)
        return state_update
        
    except Exception as e:
        logger.error(f"Unexpected error in lead_agent: {e}", exc_info=True)
        
        # Return safe default on error
        return {
            "final_recommendation": INSUFFICIENT_DATA,
            "recommendation_reason": f"Error processing recommendation: {str(e)}",
            "report_path": ""
        }


def _extract_scores(
    parsed_resume: Dict[str, Any],
    technical_evaluation: Dict[str, Any],
    market_data: Dict[str, Any]
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[int]]:
    """
    Extract and validate evaluation scores from agent outputs.

    Safely extracts the four key metrics from the cumulative state:
    strength_score, technical_score, market_fit_score, and experience_years.
    Returns None for any score that cannot be extracted or parsed.

    Args:
        parsed_resume: Agent 1 output containing profile strength data.
        technical_evaluation: Agent 3 output containing technical assessment.
        market_data: Agent 2 output containing market alignment data.

    Returns:
        Tuple of (strength_score, technical_score, market_fit_score, experience_years)
        Each score is 0.0-1.0 float or None if unavailable.
        experience_years is int or None if unavailable.
    """
    logger.debug("Extracting scores from agent outputs")
    
    # Extract strength score (Agent 1)
    strength_score: Optional[float] = None
    try:
        strength = parsed_resume.get("strength_score")
        if strength is not None:
            strength_score = float(strength)
            if not 0.0 <= strength_score <= 1.0:
                logger.warning(
                    f"Strength score out of range: {strength_score}"
                )
                strength_score = None
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse strength_score: {e}")
        strength_score = None
    
    # Extract technical score (Agent 3)
    technical_score: Optional[float] = None
    try:
        technical = technical_evaluation.get("technical_score")
        if technical is not None:
            technical_score = float(technical)
            if not 0.0 <= technical_score <= 1.0:
                logger.warning(
                    f"Technical score out of range: {technical_score}"
                )
                technical_score = None
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse technical_score: {e}")
        technical_score = None
    
    # Extract market fit score (Agent 2)
    market_fit_score: Optional[float] = None
    try:
        market_fit = market_data.get("market_fit_score")
        if market_fit is not None:
            market_fit_score = float(market_fit)
            if not 0.0 <= market_fit_score <= 1.0:
                logger.warning(
                    f"Market fit score out of range: {market_fit_score}"
                )
                market_fit_score = None
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse market_fit_score: {e}")
        market_fit_score = None
    
    # Extract experience years (Agent 1)
    experience_years: Optional[int] = None
    try:
        years = parsed_resume.get("experience_years")
        if years is not None:
            experience_years = int(years)
            if experience_years < 0:
                logger.warning(
                    f"Invalid experience years: {experience_years}"
                )
                experience_years = None
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse experience_years: {e}")
        experience_years = None
    
    logger.debug(
        f"Extracted: strength={strength_score}, tech={technical_score}, "
        f"market={market_fit_score}, years={experience_years}"
    )
    
    return strength_score, technical_score, market_fit_score, experience_years


def _determine_recommendation(
    strength_score: float,
    technical_score: float,
    market_fit_score: float,
    experience_years: Optional[int]
) -> Tuple[str, str]:
    """
    Apply rule-based decision logic to determine hiring recommendation.

    Uses transparent threshold-based rules to classify candidates into one
    of five recommendation categories based on evaluation scores.

    Decision thresholds:
    - Strong Hire: All scores >= 0.80
    - Proceed to Interview: All scores >= 0.5, average >= 0.6
    - Consider with Upskilling: 1-2 scores < 0.5, junior (< 3 years exp)
    - Not Recommended: Any critical score < 0.3
    - Insufficient data: Checked before this function

    Args:
        strength_score: Resume/profile strength (0.0-1.0).
        technical_score: Technical assessment score (0.0-1.0).
        market_fit_score: Market alignment score (0.0-1.0).
        experience_years: Years of professional experience (int or None).

    Returns:
        Tuple of (recommendation_label, recommendation_reason)
        recommendation_label is one of five exact strings.
        recommendation_reason explains the decision in 1-2 sentences.
    """
    logger.debug(
        f"Applying decision logic: strength={strength_score:.2f}, "
        f"technical={technical_score:.2f}, market={market_fit_score:.2f}, "
        f"years={experience_years}"
    )
    
    # Check for critical failures
    if strength_score < 0.3 or technical_score < 0.3 or market_fit_score < 0.3:
        logger.info("Candidate has critical score deficiency")
        reason = (
            f"Candidate does not meet minimum requirements. "
            f"Critical score below 0.3 in one or more areas."
        )
        return NOT_RECOMMENDED, reason
    
    # Check for Strong Hire (all scores high)
    if (strength_score >= 0.80 and technical_score >= 0.80 and 
        market_fit_score >= 0.80):
        logger.info("Strong candidate identified")
        reason = (
            f"Excellent fit across all dimensions. Resume strength: {strength_score:.0%}, "
            f"Technical skills: {technical_score:.0%}, Market fit: {market_fit_score:.0%}."
        )
        return STRONG_HIRE, reason
    
    # Check for good fit (mid-range scores, strong average)
    average_score = (strength_score + technical_score + market_fit_score) / 3
    if (strength_score >= 0.5 and technical_score >= 0.5 and 
        market_fit_score >= 0.5 and average_score >= 0.60):
        logger.info("Mid-tier candidate ready for interview")
        reason = (
            f"Solid candidate with balanced skills. "
            f"Recommended for technical interview to assess depth."
        )
        return PROCEED_TO_INTERVIEW, reason
    
    # Check for upskilling candidate (junior with potential)
    if experience_years is not None and experience_years < 3:
        weak_scores = sum(1 for s in [strength_score, technical_score, 
                                      market_fit_score] if s < 0.5)
        if weak_scores <= 2:  # 1-2 weak scores
            logger.info("Junior candidate with upskilling potential")
            reason = (
                f"Junior professional ({experience_years} years) with foundational "
                f"skills. Recommend for junior role or training program."
            )
            return CONSIDER_WITH_UPSKILLING, reason
    
    # Default for ambiguous cases: proceed to interview if minimum met
    if (strength_score >= 0.4 and technical_score >= 0.4 and 
        market_fit_score >= 0.4):
        logger.info("Borderline candidate - recommend interview")
        reason = (
            f"Candidate meets minimum thresholds. "
            f"Interview required to assess cultural fit and potential."
        )
        return PROCEED_TO_INTERVIEW, reason
    
    # Fallback: not recommended
    logger.info("Candidate does not meet interview threshold")
    reason = (
        f"Candidate profile does not meet interview threshold. "
        f"Scores: strength {strength_score:.0%}, technical {technical_score:.0%}, "
        f"market fit {market_fit_score:.0%}."
    )
    return NOT_RECOMMENDED, reason


def _prepare_report_data(
    state: Dict[str, Any],
    recommendation: str,
    reason: str,
    strength_score: float,
    technical_score: float,
    market_score: float
) -> Dict[str, Any]:
    """
    Prepare comprehensive data for report generation.

    Collects and structures data from the cumulative state to pass to
    ReportGeneratorTool for markdown report creation.

    Args:
        state: Full shared state dictionary.
        recommendation: Final recommendation label.
        reason: Recommendation reasoning.
        strength_score: Resume strength score.
        technical_score: Technical assessment score.
        market_score: Market fit score.

    Returns:
        Dict with all fields needed by ReportGeneratorTool.generate_report().
    """
    parsed_resume = state.get("parsed_resume", {})
    market_data = state.get("market_data", {})
    technical_eval = state.get("technical_evaluation", {})
    
    report_data = {
        "candidate_name": state.get("candidate_name", "Unknown Candidate"),
        "recommendation": recommendation,
        "recommendation_reason": reason,
        "strength_score": strength_score,
        "technical_score": technical_score,
        "market_fit_score": market_score,
        "experience_years": parsed_resume.get("experience_years"),
        "skills": parsed_resume.get("skills", []),
        "education": parsed_resume.get("education"),
        "salary_range": market_data.get("salary_range"),
        "market_benchmarks": {
            "salary_range": market_data.get("salary_range"),
            "role_demand": market_data.get("role_demand"),
            "market_trend": market_data.get("market_trend"),
        } if market_data else None,
        "interview_performance": {
            "questions_answered": technical_eval.get("questions_answered"),
            "total_questions": technical_eval.get("total_questions"),
            "response_quality": technical_eval.get("response_quality"),
            "notes": technical_eval.get("interviewer_notes"),
        } if technical_eval else None,
        "skill_gaps": parsed_resume.get("skill_gaps", []),
    }
    
    logger.debug(f"Report data prepared with keys: {list(report_data.keys())}")
    return report_data


# Export public interface
__all__ = ['lead_agent']

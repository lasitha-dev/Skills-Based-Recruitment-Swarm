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
        parsed_resume, market_data, technical_evaluation = _normalize_agent_payloads(state)
        
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


def _normalize_agent_payloads(
    state: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Normalize upstream payloads from either legacy or merged state contracts.

    Args:
        state: Shared state containing outputs from Agents 1-3.

    Returns:
        Tuple of normalized payloads in order:
        (parsed_resume, market_data, technical_evaluation).
    """
    # Agent 1 payload: prefer legacy key, fallback to merged key.
    parsed_resume_raw = state.get("parsed_resume") or state.get("structured_profile")
    parsed_resume: Optional[Dict[str, Any]] = (
        dict(parsed_resume_raw) if isinstance(parsed_resume_raw, dict) else None
    )

    if parsed_resume is not None and parsed_resume.get("strength_score") is None:
        parsed_resume["strength_score"] = _derive_strength_score(parsed_resume)

    # Agent 2 payload: market_data is stable, but score may need deriving.
    market_data_raw = state.get("market_data")
    market_data: Optional[Dict[str, Any]] = (
        dict(market_data_raw) if isinstance(market_data_raw, dict) else None
    )

    if market_data is not None and market_data.get("market_fit_score") is None:
        market_data["market_fit_score"] = _derive_market_fit_score(market_data)

    # Agent 3 payload: prefer legacy key, fallback to merged key.
    technical_raw = state.get("technical_evaluation") or state.get("evaluation_results")
    technical_evaluation: Optional[Dict[str, Any]] = (
        dict(technical_raw) if isinstance(technical_raw, dict) else None
    )

    if technical_evaluation is not None and technical_evaluation.get("technical_score") is None:
        technical_evaluation["technical_score"] = _derive_technical_score(technical_evaluation)

    return parsed_resume, market_data, technical_evaluation


def _derive_strength_score(parsed_resume: Dict[str, Any]) -> Optional[float]:
    """Derive a resume strength score when Agent 1 did not provide one directly.

    Args:
        parsed_resume: Resume payload from Agent 1.

    Returns:
        Float in range [0.0, 1.0] or None when insufficient data exists.
    """
    years = parsed_resume.get("experience_years") or parsed_resume.get("years_of_experience")
    skills = parsed_resume.get("skills", [])

    years_score: Optional[float] = None
    if isinstance(years, (int, float)):
        years_score = min(max(float(years), 0.0), 10.0) / 10.0

    skills_score: Optional[float] = None
    if isinstance(skills, list):
        valid_skills = [item for item in skills if isinstance(item, str) and item.strip()]
        skills_score = min(len(valid_skills), 10) / 10.0

    components = [value for value in [years_score, skills_score] if value is not None]
    if not components:
        return None

    return sum(components) / len(components)


def _derive_technical_score(technical_evaluation: Dict[str, Any]) -> Optional[float]:
    """Derive technical score from Agent 3 evaluation_results when needed.

    Args:
        technical_evaluation: Agent 3 payload.

    Returns:
        Float in range [0.0, 1.0] or None when derivation is not possible.
    """
    skill_gaps = technical_evaluation.get("skill_gaps")
    if not isinstance(skill_gaps, dict):
        return None

    required = skill_gaps.get("required_skills", [])
    matched = skill_gaps.get("matched_skills", [])

    if not isinstance(required, list) or not isinstance(matched, list):
        return None
    if len(required) == 0:
        return None

    return min(max(len(matched) / len(required), 0.0), 1.0)


def _derive_market_fit_score(market_data: Dict[str, Any]) -> Optional[float]:
    """Derive market fit score from Agent 2 market trend categories.

    Args:
        market_data: Agent 2 output payload.

    Returns:
        Float in range [0.0, 1.0] or None when derivation is not possible.
    """
    trends = market_data.get("trends", {})
    if not isinstance(trends, dict) or not trends:
        return None

    demand_weights = {
        "high-demand": 1.0,
        "high": 1.0,
        "emerging": 0.7,
        "low-demand": 0.3,
        "low": 0.3,
        "unknown": 0.5,
        "error": 0.3,
    }

    values: list[float] = []
    for demand in trends.values():
        if isinstance(demand, str):
            values.append(demand_weights.get(demand.lower(), 0.5))

    if not values:
        return None

    return sum(values) / len(values)


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
        years = parsed_resume.get("experience_years") or parsed_resume.get("years_of_experience")
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


def _normalize_interview_questions(raw_questions: Any) -> Tuple[list[str], int]:
    """Normalize interview questions from state into plain text entries.

    Supports both legacy ``list[str]`` and Agent 3 ``QuestionRecord`` style
    entries where each item is a dictionary containing a ``question`` key.

    Args:
        raw_questions: Value from ``state["questions"]``.

    Returns:
        Tuple of (normalized_questions, dropped_count) where normalized questions
        are cleaned non-empty strings preserving source order.
    """
    if raw_questions is None:
        return [], 0

    if not isinstance(raw_questions, list):
        return [], 1

    normalized: list[str] = []
    dropped_count = 0

    for item in raw_questions:
        question_text = ""

        if isinstance(item, str):
            question_text = item.strip()
        elif isinstance(item, dict):
            maybe_question = item.get("question")
            if isinstance(maybe_question, str):
                question_text = maybe_question.strip()

        if question_text:
            normalized.append(question_text)
        else:
            dropped_count += 1

    return normalized, dropped_count


def _extract_skill_gaps(
    parsed_resume: Dict[str, Any],
    technical_eval: Dict[str, Any]
) -> list[str]:
    """Extract reportable skill gaps with Agent 3 output as primary source.

    Args:
        parsed_resume: Resume payload from Agent 1.
        technical_eval: Technical evaluation payload from Agent 3.

    Returns:
        Ordered list of human-readable missing skills.
    """
    tech_skill_gaps = technical_eval.get("skill_gaps")
    if isinstance(tech_skill_gaps, dict):
        missing_skills = tech_skill_gaps.get("missing_skills", [])
        if isinstance(missing_skills, list):
            normalized_missing = [
                skill.strip() for skill in missing_skills
                if isinstance(skill, str) and skill.strip()
            ]
            if normalized_missing:
                return normalized_missing

    resume_skill_gaps = parsed_resume.get("skill_gaps", [])
    if isinstance(resume_skill_gaps, list):
        return [
            skill.strip() for skill in resume_skill_gaps
            if isinstance(skill, str) and skill.strip()
        ]

    return []


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
    parsed_resume_raw, market_data_raw, technical_eval_raw = _normalize_agent_payloads(state)
    parsed_resume = parsed_resume_raw or {}
    market_data = market_data_raw or {}
    technical_eval = technical_eval_raw or {}
    interview_questions, dropped_questions = _normalize_interview_questions(state.get("questions"))
    skill_gaps = _extract_skill_gaps(parsed_resume, technical_eval)

    logger.info(
        "Prepared %d interview questions for report generation.",
        len(interview_questions)
    )
    if dropped_questions > 0:
        logger.warning(
            "Skipped %d malformed interview question entries while preparing report payload.",
            dropped_questions
        )
    
    report_data = {
        "candidate_name": state.get("candidate_name", "Unknown Candidate"),
        "recommendation": recommendation,
        "recommendation_reason": reason,
        "strength_score": strength_score,
        "technical_score": technical_score,
        "market_fit_score": market_score,
        "experience_years": parsed_resume.get("experience_years") or parsed_resume.get("years_of_experience"),
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
        "interview_questions": interview_questions,
        "skill_gaps": skill_gaps,
    }
    
    logger.debug(f"Report data prepared with keys: {list(report_data.keys())}")
    return report_data


# Export public interface
__all__ = ['lead_agent']

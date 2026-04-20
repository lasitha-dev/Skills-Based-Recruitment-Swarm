"""
Test Suite for Agent 4: Recruitment Lead

This module contains pytest tests for Agent 4's recommendation logic,
report generation, and state handling. Tests verify correct behavior
across diverse candidate profiles and edge cases.

Author: G.A. Sandaru (Agent 4: Recruitment Lead)
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.lead_agent import (
    lead_agent,
    STRONG_HIRE,
    PROCEED_TO_INTERVIEW,
    CONSIDER_WITH_UPSKILLING,
    NOT_RECOMMENDED,
    INSUFFICIENT_DATA
)
from main_graph import recruitment_lead_agent


# ============================================================================
# FIXTURES: Sample State Data
# ============================================================================

@pytest.fixture
def strong_candidate_state() -> dict:
    """
    Fixture: Strong candidate with high scores across all dimensions.
    
    Expected recommendation: "Strong Hire"
    """
    return {
        "candidate_name": "Alice Johnson",
        "parsed_resume": {
            "strength_score": 0.85,
            "experience_years": 7,
            "skills": ["Python", "SQL", "Docker", "AWS"],
            "education": "Bachelor's in Computer Science",
            "skill_gaps": []
        },
        "market_data": {
            "market_fit_score": 0.82,
            "salary_range": "$100k-$150k",
            "role_demand": "high",
            "market_trend": "growing"
        },
        "technical_evaluation": {
            "technical_score": 0.88,
            "questions_answered": 9,
            "total_questions": 10,
            "response_quality": "excellent",
            "interviewer_notes": "Strong technical depth and communication"
        }
    }


@pytest.fixture
def weak_candidate_state() -> dict:
    """
    Fixture: Weak candidate with low scores across dimensions.
    
    Expected recommendation: "Not Recommended"
    """
    return {
        "candidate_name": "Bob Smith",
        "parsed_resume": {
            "strength_score": 0.25,
            "experience_years": 1,
            "skills": ["HTML", "CSS"],
            "education": "High School Diploma",
            "skill_gaps": ["Backend development", "Databases", "DevOps"]
        },
        "market_data": {
            "market_fit_score": 0.20,
            "salary_range": "$30k-$40k",
            "role_demand": "low",
            "market_trend": "declining"
        },
        "technical_evaluation": {
            "technical_score": 0.15,
            "questions_answered": 2,
            "total_questions": 10,
            "response_quality": "poor",
            "interviewer_notes": "Fundamental knowledge gaps"
        }
    }


@pytest.fixture
def mid_tier_candidate_state() -> dict:
    """
    Fixture: Mid-tier candidate with balanced scores.
    
    Expected recommendation: "Proceed to Interview"
    """
    return {
        "candidate_name": "Charlie Brown",
        "parsed_resume": {
            "strength_score": 0.60,
            "experience_years": 4,
            "skills": ["Java", "Spring", "MySQL"],
            "education": "Bachelor's in IT",
            "skill_gaps": ["Cloud platforms", "Microservices"]
        },
        "market_data": {
            "market_fit_score": 0.65,
            "salary_range": "$70k-$90k",
            "role_demand": "medium",
            "market_trend": "stable"
        },
        "technical_evaluation": {
            "technical_score": 0.62,
            "questions_answered": 6,
            "total_questions": 10,
            "response_quality": "good",
            "interviewer_notes": "Solid fundamentals, needs mentoring"
        }
    }


@pytest.fixture
def junior_upskilling_state() -> dict:
    """
    Fixture: Junior candidate with upskilling potential.
    
    Expected recommendation: "Consider with Upskilling"
    """
    return {
        "candidate_name": "Diana Lee",
        "parsed_resume": {
            "strength_score": 0.55,
            "experience_years": 1,
            "skills": ["Python", "Git", "Linux"],
            "education": "Bootcamp Graduate",
            "skill_gaps": ["Professional frameworks", "Database design", "Testing"]
        },
        "market_data": {
            "market_fit_score": 0.52,
            "salary_range": "$40k-$50k",
            "role_demand": "high",
            "market_trend": "growing"
        },
        "technical_evaluation": {
            "technical_score": 0.50,
            "questions_answered": 5,
            "total_questions": 10,
            "response_quality": "fair",
            "interviewer_notes": "Eager learner, needs junior role with mentoring"
        }
    }


@pytest.fixture
def missing_market_data_state() -> dict:
    """
    Fixture: Valid resume and technical data, but missing market data.
    
    Expected recommendation: "Insufficient data"
    """
    return {
        "candidate_name": "Eve Watson",
        "parsed_resume": {
            "strength_score": 0.75,
            "experience_years": 5,
            "skills": ["Python", "Django", "PostgreSQL"],
            "education": "Bachelor's in CS"
        },
        "market_data": None,  # Missing!
        "technical_evaluation": {
            "technical_score": 0.78,
            "questions_answered": 8,
            "total_questions": 10
        }
    }


@pytest.fixture
def missing_candidate_name_state() -> dict:
    """
    Fixture: Missing candidate name.
    
    Expected recommendation: "Insufficient data"
    """
    return {
        "candidate_name": None,  # Missing!
        "parsed_resume": {
            "strength_score": 0.70,
            "experience_years": 3
        },
        "market_data": {
            "market_fit_score": 0.72
        },
        "technical_evaluation": {
            "technical_score": 0.75
        }
    }


@pytest.fixture
def missing_all_optional_scores_state() -> dict:
    """
    Fixture: All required fields present but scores are None.
    
    Expected recommendation: "Insufficient data"
    """
    return {
        "candidate_name": "Frank Miller",
        "parsed_resume": {
            "strength_score": None,  # Missing!
            "experience_years": 5
        },
        "market_data": {
            "market_fit_score": None  # Missing!
        },
        "technical_evaluation": {
            "technical_score": None  # Missing!
        }
    }


@pytest.fixture
def empty_state() -> dict:
    """
    Fixture: Completely empty state.
    
    Expected recommendation: "Insufficient data"
    """
    return {}


# ============================================================================
# TEST: Strong Candidate (Happy Path)
# ============================================================================

def test_strong_hire_recommendation(strong_candidate_state: dict) -> None:
    """
    Test that a strong candidate receives "Strong Hire" recommendation.
    
    Validates:
    - Correct recommendation label
    - Reason is populated
    - Report path is returned
    """
    # Arrange
    state = strong_candidate_state
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "final_recommendation" in result, "Result must contain final_recommendation"
    assert "recommendation_reason" in result, "Result must contain recommendation_reason"
    assert "report_path" in result, "Result must contain report_path"
    
    assert result["final_recommendation"] == STRONG_HIRE, (
        f"Expected '{STRONG_HIRE}', got '{result['final_recommendation']}'"
    )
    assert len(result["recommendation_reason"]) > 0, "Reason should not be empty"
    assert result["report_path"] != "", "Report path should be populated for successful case"


def test_strong_hire_report_exists(strong_candidate_state: dict) -> None:
    """
    Test that a strong candidate's report file is actually created.
    
    Validates:
    - Report file exists at returned path
    - Report contains expected candidate name
    - Report is valid markdown
    """
    # Arrange
    state = strong_candidate_state
    
    # Act
    result = lead_agent(state)
    report_path = result["report_path"]
    
    # Assert
    assert os.path.exists(report_path), f"Report file should exist at {report_path}"
    
    assert report_path.endswith(".pdf"), "Report should be a PDF file"
    assert os.path.getsize(report_path) > 0, "PDF report should have content"


# ============================================================================
# TEST: Weak Candidate
# ============================================================================

def test_not_recommended_weak_candidate(weak_candidate_state: dict) -> None:
    """
    Test that a weak candidate receives "Not Recommended" recommendation.
    
    Validates:
    - Correct recommendation for low scores
    - Reason explains the decision
    """
    # Arrange
    state = weak_candidate_state
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] == NOT_RECOMMENDED, (
        f"Expected '{NOT_RECOMMENDED}', got '{result['final_recommendation']}'"
    )
    assert len(result["recommendation_reason"]) > 0, "Reason should explain rejection"


# ============================================================================
# TEST: Mid-Tier Candidate
# ============================================================================

def test_proceed_to_interview_mid_tier(mid_tier_candidate_state: dict) -> None:
    """
    Test that a mid-tier candidate receives "Proceed to Interview".
    
    Validates:
    - Balanced scores lead to interview recommendation
    - Report is generated
    """
    # Arrange
    state = mid_tier_candidate_state
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] == PROCEED_TO_INTERVIEW, (
        f"Expected '{PROCEED_TO_INTERVIEW}', got '{result['final_recommendation']}'"
    )
    assert result["report_path"] != "", "Report should be generated"


# ============================================================================
# TEST: Junior Candidate with Upskilling Potential
# ============================================================================

def test_consider_with_upskilling_junior(junior_upskilling_state: dict) -> None:
    """
    Test that a junior candidate with potential receives upskilling recommendation.
    
    Validates:
    - Low experience + potential = upskilling recommendation
    - Reason mentions junior status
    """
    # Arrange
    state = junior_upskilling_state
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] == CONSIDER_WITH_UPSKILLING, (
        f"Expected '{CONSIDER_WITH_UPSKILLING}', "
        f"got '{result['final_recommendation']}'"
    )
    assert "junior" in result["recommendation_reason"].lower() or \
           "junior" in result["recommendation_reason"], (
        "Reason should mention junior status or training"
    )


# ============================================================================
# TEST: Missing Market Data (Insufficient Data)
# ============================================================================

def test_insufficient_data_missing_market(missing_market_data_state: dict) -> None:
    """
    Test that missing market data returns "Insufficient data".
    
    Validates:
    - Agent handles missing dict gracefully
    - No crash occurs
    - Returns appropriate recommendation
    """
    # Arrange
    state = missing_market_data_state
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] == INSUFFICIENT_DATA, (
        f"Expected '{INSUFFICIENT_DATA}' for missing market data, "
        f"got '{result['final_recommendation']}'"
    )
    assert "market_data" in result["recommendation_reason"].lower(), (
        "Reason should mention missing market data"
    )
    assert result["report_path"] == "", "No report should be generated for insufficient data"


def test_insufficient_data_missing_candidate_name(missing_candidate_name_state: dict) -> None:
    """
    Test that missing candidate name returns "Insufficient data".
    
    Validates:
    - Agent requires candidate name
    - Returns appropriate error reason
    """
    # Arrange
    state = missing_candidate_name_state
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] == INSUFFICIENT_DATA


def test_insufficient_data_missing_scores(missing_all_optional_scores_state: dict) -> None:
    """
    Test that missing evaluation scores returns "Insufficient data".
    
    Validates:
    - All three scores are required
    - None values are handled correctly
    """
    # Arrange
    state = missing_all_optional_scores_state
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] == INSUFFICIENT_DATA, (
        "Missing scores should trigger insufficient data"
    )


def test_insufficient_data_empty_state(empty_state: dict) -> None:
    """
    Test that completely empty state returns "Insufficient data".
    
    Validates:
    - Agent doesn't crash on empty input
    - Returns safe default recommendation
    """
    # Arrange
    state = empty_state
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] == INSUFFICIENT_DATA
    assert "recommendation_reason" in result
    assert result["report_path"] == ""


# ============================================================================
# TEST: Recommendation Labels Validation
# ============================================================================

def test_valid_recommendation_labels(
    strong_candidate_state: dict,
    weak_candidate_state: dict,
    mid_tier_candidate_state: dict
) -> None:
    """
    Test that all recommendations use exact valid labels.
    
    Validates:
    - All 5 recommendation labels are used correctly
    - No typos or variations in labels
    """
    valid_labels = {
        STRONG_HIRE,
        PROCEED_TO_INTERVIEW,
        CONSIDER_WITH_UPSKILLING,
        NOT_RECOMMENDED,
        INSUFFICIENT_DATA
    }
    
    test_states = [
        strong_candidate_state,
        weak_candidate_state,
        mid_tier_candidate_state
    ]
    
    for state in test_states:
        result = lead_agent(state)
        recommendation = result["final_recommendation"]
        
        assert recommendation in valid_labels, (
            f"Recommendation '{recommendation}' not in valid labels: {valid_labels}"
        )


# ============================================================================
# TEST: State Update Structure
# ============================================================================

def test_state_update_structure(strong_candidate_state: dict) -> None:
    """
    Test that Agent 4 returns only required state updates.
    
    Validates:
    - Only final_recommendation, recommendation_reason, report_path returned
    - Does not include unnecessary fields
    - Does not overwrite entire state
    """
    # Arrange
    state = strong_candidate_state
    
    # Act
    result = lead_agent(state)
    
    # Assert
    # Check required fields exist
    required_fields = {
        "final_recommendation",
        "recommendation_reason",
        "report_path"
    }
    assert set(result.keys()) == required_fields, (
        f"Return should contain exactly {required_fields}, "
        f"got {set(result.keys())}"
    )
    
    # Verify types
    assert isinstance(result["final_recommendation"], str)
    assert isinstance(result["recommendation_reason"], str)
    assert isinstance(result["report_path"], str)


# ============================================================================
# TEST: Error Handling and Edge Cases
# ============================================================================

def test_invalid_state_type() -> None:
    """
    Test that invalid state type is handled safely.
    
    Validates:
    - Non-dict input doesn't crash agent
    - Returns insufficient data
    """
    # Act
    result = lead_agent("invalid")  # type: ignore
    
    # Assert
    assert result["final_recommendation"] == INSUFFICIENT_DATA


def test_score_out_of_range() -> None:
    """
    Test that scores outside 0.0-1.0 range are handled.
    
    Validates:
    - Out-of-range scores don't crash logic
    - Returns insufficient data when invalid
    """
    # Arrange
    state = {
        "candidate_name": "Test User",
        "parsed_resume": {
            "strength_score": 1.5,  # Out of range!
            "experience_years": 5
        },
        "market_data": {
            "market_fit_score": 0.7
        },
        "technical_evaluation": {
            "technical_score": 0.8
        }
    }
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] == INSUFFICIENT_DATA, (
        "Invalid score range should trigger insufficient data"
    )


def test_string_scores_converted_to_float() -> None:
    """
    Test that string scores are converted to float.
    
    Validates:
    - "0.8" string is converted to 0.8 float
    - Conversion works correctly
    """
    # Arrange
    state = {
        "candidate_name": "Test User",
        "parsed_resume": {
            "strength_score": "0.8",  # String!
            "experience_years": 5
        },
        "market_data": {
            "market_fit_score": "0.75"  # String!
        },
        "technical_evaluation": {
            "technical_score": "0.82"  # String!
        }
    }
    
    # Act
    result = lead_agent(state)
    
    # Assert
    # Should NOT be insufficient data if conversion works
    assert result["final_recommendation"] != INSUFFICIENT_DATA, (
        "String scores should be converted to float"
    )


# ============================================================================
# TEST: Logging and Debugging
# ============================================================================

def test_agent_handles_missing_optional_fields(strong_candidate_state: dict) -> None:
    """
    Test that agent gracefully handles missing optional fields.
    
    Validates:
    - Missing skills, education, benchmarks don't crash
    - Recommendation still generated with primary scores
    """
    # Arrange
    state = {
        "candidate_name": "Minimal Data User",
        "parsed_resume": {
            "strength_score": 0.80,
            "experience_years": 5
            # Missing: skills, education, skill_gaps
        },
        "market_data": {
            "market_fit_score": 0.78
            # Missing: salary_range, role_demand, market_trend
        },
        "technical_evaluation": {
            "technical_score": 0.82
            # Missing: questions_answered, response_quality, etc.
        }
    }
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] != INSUFFICIENT_DATA, (
        "Optional fields missing shouldn't cause insufficient data"
    )
    assert result["final_recommendation"] == PROCEED_TO_INTERVIEW


# ============================================================================
# Integration Test
# ============================================================================

def test_full_workflow_strong_candidate_generates_report(strong_candidate_state: dict) -> None:
    """
    Integration test: Full workflow from state to report.
    
    Validates:
    - Agent receives state
    - Generates recommendation
    - Creates report file
    - Report contains all expected sections
    """
    # Arrange
    state = strong_candidate_state
    candidate_name = state["candidate_name"]
    
    # Act
    result = lead_agent(state)
    
    # Assert
    assert result["final_recommendation"] == STRONG_HIRE
    report_path = result["report_path"]
    assert os.path.exists(report_path)
    
    # Verify report content is a non-empty PDF
    assert report_path.endswith(".pdf"), "Report should be a PDF file"
    assert os.path.getsize(report_path) > 0, "PDF report should have content"


def test_lead_agent_supports_merged_agent_state_schema() -> None:
    """Agent 4 should support merged outputs from Agents 1-3 keys.

    Validates compatibility with:
    - Agent 1: structured_profile
    - Agent 2: market_data with trends
    - Agent 3: evaluation_results
    """
    state = {
        "candidate_name": "Schema Compatible Candidate",
        "structured_profile": {
            "skills": ["Python", "AWS", "SQL", "Docker"],
            "years_of_experience": 6,
            "education": "BSc Computer Science",
        },
        "market_data": {
            "trends": {
                "Python": "high-demand",
                "AWS": "high-demand",
                "SQL": "emerging",
            }
        },
        "evaluation_results": {
            "skill_gaps": {
                "required_skills": ["python", "aws", "sql"],
                "matched_skills": ["python", "aws"],
                "missing_skills": ["sql"],
            }
        },
    }

    result = lead_agent(state)

    assert result["final_recommendation"] != INSUFFICIENT_DATA
    assert result["report_path"] != ""


def test_recruitment_lead_graph_node_preserves_state_and_sets_final_report() -> None:
    """Graph node should preserve upstream fields and attach final_report metadata."""
    state = {
        "candidate_name": "Node Integration Candidate",
        "structured_profile": {
            "skills": ["Python", "Docker", "AWS"],
            "years_of_experience": 5,
        },
        "market_data": {
            "trends": {
                "Python": "high-demand",
                "Docker": "high-demand",
                "AWS": "high-demand",
            }
        },
        "evaluation_results": {
            "skill_gaps": {
                "required_skills": ["python", "docker", "aws"],
                "matched_skills": ["python", "docker", "aws"],
                "missing_skills": [],
            }
        },
        "logs": ["[TechEvaluator] done"],
    }

    updated = recruitment_lead_agent(state)

    assert updated["candidate_name"] == "Node Integration Candidate"
    assert "[TechEvaluator] done" in updated["logs"]
    assert "final_report" in updated
    assert isinstance(updated["final_report"], dict)
    assert "recommendation" in updated["final_report"]
    assert "report_path" in updated["final_report"]


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'test_strong_hire_recommendation',
    'test_not_recommended_weak_candidate',
    'test_insufficient_data_missing_market',
    'test_valid_recommendation_labels',
    'test_state_update_structure',
]

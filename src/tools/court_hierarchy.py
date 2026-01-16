"""
UK Court Hierarchy and Precedent Ranking System

This module defines the UK court system hierarchy and provides functions
to rank cases by their precedential authority based on the court level.
"""

from typing import List, Dict, Optional
from enum import IntEnum


class CourtLevel(IntEnum):
    """
    UK Court Hierarchy from highest to lowest precedential authority.
    Higher numeric values indicate higher precedential authority.
    """
    SUPREME_COURT = 100
    PRIVY_COUNCIL = 95  # For certain Commonwealth appeals
    COURT_OF_APPEAL_CIVIL = 90
    COURT_OF_APPEAL_CRIMINAL = 90
    HIGH_COURT = 70
    CROWN_COURT = 50
    COUNTY_COURT = 40
    FAMILY_COURT = 40
    TRIBUNAL_UPPER = 35
    MAGISTRATES_COURT = 20
    TRIBUNAL_FIRST_TIER = 15
    UNKNOWN = 0


# Court name patterns and their corresponding hierarchy levels
COURT_NAME_MAPPINGS = {
    # Supreme Court
    "supreme court": CourtLevel.SUPREME_COURT,
    "uksc": CourtLevel.SUPREME_COURT,
    "uk supreme court": CourtLevel.SUPREME_COURT,

    # Privy Council
    "privy council": CourtLevel.PRIVY_COUNCIL,
    "ukpc": CourtLevel.PRIVY_COUNCIL,
    "judicial committee": CourtLevel.PRIVY_COUNCIL,

    # Court of Appeal
    "court of appeal": CourtLevel.COURT_OF_APPEAL_CIVIL,
    "ewca": CourtLevel.COURT_OF_APPEAL_CIVIL,
    "ewca civ": CourtLevel.COURT_OF_APPEAL_CIVIL,
    "ewca crim": CourtLevel.COURT_OF_APPEAL_CRIMINAL,
    "court of appeal (civil division)": CourtLevel.COURT_OF_APPEAL_CIVIL,
    "court of appeal (criminal division)": CourtLevel.COURT_OF_APPEAL_CRIMINAL,

    # High Court
    "high court": CourtLevel.HIGH_COURT,
    "ewhc": CourtLevel.HIGH_COURT,
    "queen's bench": CourtLevel.HIGH_COURT,
    "king's bench": CourtLevel.HIGH_COURT,
    "chancery": CourtLevel.HIGH_COURT,
    "family division": CourtLevel.HIGH_COURT,
    "administrative court": CourtLevel.HIGH_COURT,
    "commercial court": CourtLevel.HIGH_COURT,
    "technology and construction court": CourtLevel.HIGH_COURT,

    # Crown Court
    "crown court": CourtLevel.CROWN_COURT,

    # County Court
    "county court": CourtLevel.COUNTY_COURT,

    # Family Court
    "family court": CourtLevel.FAMILY_COURT,

    # Tribunals
    "upper tribunal": CourtLevel.TRIBUNAL_UPPER,
    "employment appeal tribunal": CourtLevel.TRIBUNAL_UPPER,
    "eat": CourtLevel.TRIBUNAL_UPPER,
    "first-tier tribunal": CourtLevel.TRIBUNAL_FIRST_TIER,
    "first tier tribunal": CourtLevel.TRIBUNAL_FIRST_TIER,
    "employment tribunal": CourtLevel.TRIBUNAL_FIRST_TIER,

    # Magistrates
    "magistrates": CourtLevel.MAGISTRATES_COURT,
    "magistrates' court": CourtLevel.MAGISTRATES_COURT,
}


def identify_court_level(court_name: str) -> CourtLevel:
    """
    Identify the court level from a court name string.

    Args:
        court_name: The name or description of the court (e.g., "Court of Appeal")

    Returns:
        CourtLevel enum value representing the court's precedential authority
    """
    if not court_name or court_name == "N/A":
        return CourtLevel.UNKNOWN

    court_lower = court_name.lower().strip()

    # Check for exact or partial matches
    for pattern, level in COURT_NAME_MAPPINGS.items():
        if pattern in court_lower:
            return level

    return CourtLevel.UNKNOWN


def get_court_display_name(court_level: CourtLevel) -> str:
    """
    Get a human-readable display name for a court level.

    Args:
        court_level: The CourtLevel enum value

    Returns:
        Human-readable court name
    """
    display_names = {
        CourtLevel.SUPREME_COURT: "UK Supreme Court",
        CourtLevel.PRIVY_COUNCIL: "Privy Council",
        CourtLevel.COURT_OF_APPEAL_CIVIL: "Court of Appeal",
        CourtLevel.COURT_OF_APPEAL_CRIMINAL: "Court of Appeal",
        CourtLevel.HIGH_COURT: "High Court",
        CourtLevel.CROWN_COURT: "Crown Court",
        CourtLevel.COUNTY_COURT: "County Court",
        CourtLevel.FAMILY_COURT: "Family Court",
        CourtLevel.TRIBUNAL_UPPER: "Upper Tribunal",
        CourtLevel.TRIBUNAL_FIRST_TIER: "First-tier Tribunal",
        CourtLevel.MAGISTRATES_COURT: "Magistrates' Court",
        CourtLevel.UNKNOWN: "Unknown Court",
    }
    return display_names.get(court_level, "Unknown Court")


def rank_cases_by_authority(cases_metadata: List[Dict]) -> List[Dict]:
    """
    Rank cases by their precedential authority based on court hierarchy.
    Cases from higher courts are ranked first.

    Args:
        cases_metadata: List of case metadata dicts with 'court' field

    Returns:
        List of cases sorted by precedential authority (highest first),
        with added 'court_level' and 'precedent_rank' fields
    """
    ranked_cases = []

    for case in cases_metadata:
        court_name = case.get("court", "")
        court_level = identify_court_level(court_name)

        ranked_case = {
            **case,
            "court_level": court_level,
            "court_level_value": int(court_level),
            "court_level_name": get_court_display_name(court_level)
        }
        ranked_cases.append(ranked_case)

    # Sort by court level (highest first)
    ranked_cases.sort(key=lambda x: x["court_level_value"], reverse=True)

    # Assign precedent ranks
    for i, case in enumerate(ranked_cases, start=1):
        case["precedent_rank"] = i

    return ranked_cases


def identify_controlling_precedents(ranked_cases: List[Dict]) -> List[Dict]:
    """
    Identify the controlling precedent(s) - the highest authority case(s).
    If multiple cases are from the same highest court level, all are returned.

    Args:
        ranked_cases: List of cases already ranked by authority

    Returns:
        List of controlling precedent cases (may be multiple if equal authority)
    """
    if not ranked_cases:
        return []

    # Find the highest court level value
    highest_level = ranked_cases[0]["court_level_value"]

    # Return all cases at this highest level
    controlling = [
        case for case in ranked_cases
        if case["court_level_value"] == highest_level
    ]

    return controlling


def format_precedent_hierarchy(ranked_cases: List[Dict]) -> str:
    """
    Format the precedent hierarchy as a readable string for display in judgments.

    Args:
        ranked_cases: List of cases ranked by authority

    Returns:
        Formatted string showing the precedent hierarchy
    """
    if not ranked_cases:
        return "No cases found."

    # Group by court level
    by_level = {}
    for case in ranked_cases:
        level_name = case["court_level_name"]
        if level_name not in by_level:
            by_level[level_name] = []
        by_level[level_name].append(case)

    lines = []
    for level_name in sorted(by_level.keys(), key=lambda x: by_level[x][0]["court_level_value"], reverse=True):
        cases = by_level[level_name]
        lines.append(f"\n{level_name}:")
        for case in cases:
            citation = case.get("citation", "N/A")
            name = case.get("name", "Unknown Case")
            lines.append(f"  - {name} {citation}")

    return "\n".join(lines)

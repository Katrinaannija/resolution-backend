"""
Analyze Precedents Node

This node ranks cases by court hierarchy, identifies controlling precedents,
and uses LLM analysis to determine case relationships (agreement/distinction).
"""

import json
from typing import List, Dict

from src.case_law.case_law_state import CaseLawState
from src.tools.court_hierarchy import (
    rank_cases_by_authority,
    identify_controlling_precedents,
)
from src.utils.pull_prompt import pull_prompt_async


async def analyze_precedents(state: CaseLawState) -> CaseLawState:
    """
    Rank cases by precedential authority and analyze their relationships.

    This node:
    1. Ranks cases by UK court hierarchy
    2. Identifies controlling precedent(s)
    3. Uses LLM to analyze case agreements and distinctions
    4. Returns precedent analysis for use in recommendations
    """
    case_metadata: List[Dict] = state.get("case_metadata", [])
    issue = state.get("issue", {})
    legal_issue = issue.get("legal_issue", "")

    # If no cases were found, return early
    if not case_metadata:
        print("[analyze_precedents] No cases to analyze")
        return {
            "ranked_cases": [],
            "controlling_precedents": [],
            "precedent_analysis": "No case law precedents were found for this issue."
        }

    # Step 1: Rank cases by court hierarchy
    print(f"[analyze_precedents] Ranking {len(case_metadata)} cases by authority")
    ranked_cases = rank_cases_by_authority(case_metadata)

    # Step 2: Identify controlling precedent(s)
    controlling_precedents = identify_controlling_precedents(ranked_cases)
    print(f"[analyze_precedents] Identified {len(controlling_precedents)} controlling precedent(s)")

    # Step 3: Format cases for LLM analysis
    formatted_cases = format_cases_for_analysis(ranked_cases)

    # Step 4: Use LLM to analyze case relationships
    precedent_prompt = await pull_prompt_async(
        "case_law_precedent_analysis",
        include_model=True
    )

    result = await precedent_prompt.ainvoke({
        "legal_issue": legal_issue,
        "ranked_cases": formatted_cases
    })

    # Extract the text content from the LLM response
    if hasattr(result, 'content'):
        precedent_analysis = result.content
    else:
        precedent_analysis = str(result)

    print("[analyze_precedents] Precedent analysis completed")
    print(f"[analyze_precedents] Analysis preview: {precedent_analysis[:200]}...")

    return {
        "ranked_cases": ranked_cases,
        "controlling_precedents": controlling_precedents,
        "precedent_analysis": precedent_analysis
    }


def format_cases_for_analysis(ranked_cases: List[Dict]) -> str:
    """
    Format ranked cases into a readable string for LLM analysis.

    Args:
        ranked_cases: List of cases with ranking information

    Returns:
        Formatted string describing each case with its hierarchy position
    """
    if not ranked_cases:
        return "No cases available."

    lines = []
    for i, case in enumerate(ranked_cases, 1):
        name = case.get("name", "Unknown Case")
        citation = case.get("citation", "N/A")
        court = case.get("court", "N/A")
        court_level_name = case.get("court_level_name", "Unknown Court")
        date = case.get("date", "N/A")
        precedent_rank = case.get("precedent_rank", i)

        lines.append(
            f"{i}. {name} {citation}\n"
            f"   Court: {court} ({court_level_name})\n"
            f"   Date: {date}\n"
            f"   Precedent Rank: {precedent_rank}\n"
        )

    return "\n".join(lines)

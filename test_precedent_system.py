"""
Test script for the precedent scoring system
"""

import asyncio
from src.case_law.case_law_state import CaseLawState, Issue, CaseMetadata
from src.case_law.nodes.analyze_precedents import analyze_precedents

async def test_precedent_analysis():
    """Test the precedent analysis node with sample cases"""

    # Create test state with sample cases
    test_state = CaseLawState(
        issue_index=0,
        issue=Issue(
            legal_issue="Whether the defendant breached the contract by delivering goods late",
            date_event="2024-01-15",
            undisputed_facts="Goods were delivered 2 weeks late",
            claimant_position="Breach caused loss of profits",
            defendant_position="Delay was not foreseeable",
            relevant_documents=[]
        ),
        case_metadata=[
            CaseMetadata(
                name="Smith v Jones",
                citation="[2024] EWHC 123 (Comm)",
                court="High Court (Commercial Court)",
                date="2024-01-10",
                url="http://example.com/smith",
                keyword_set="breach contract late delivery"
            ),
            CaseMetadata(
                name="Brown v Green",
                citation="[2023] EWCA Civ 456",
                court="Court of Appeal (Civil Division)",
                date="2023-12-15",
                url="http://example.com/brown",
                keyword_set="contract delay damages"
            ),
            CaseMetadata(
                name="White v Black",
                citation="[2024] UKSC 789",
                court="Supreme Court",
                date="2024-02-01",
                url="http://example.com/white",
                keyword_set="contract breach remedies"
            ),
            CaseMetadata(
                name="Taylor v Wilson",
                citation="[2023] EWHC 321 (QB)",
                court="High Court (Queen's Bench Division)",
                date="2023-11-20",
                url="http://example.com/taylor",
                keyword_set="late delivery contract"
            ),
        ]
    )

    print("=" * 80)
    print("TESTING PRECEDENT SCORING SYSTEM")
    print("=" * 80)
    print(f"\nLegal Issue: {test_state['issue']['legal_issue']}")
    print(f"\nOriginal cases (unranked):")
    for i, case in enumerate(test_state['case_metadata'], 1):
        print(f"  {i}. {case['name']} {case['citation']}")
        print(f"     Court: {case['court']}")

    # Run the analyze_precedents node
    print("\n" + "=" * 80)
    print("RUNNING PRECEDENT ANALYSIS...")
    print("=" * 80)

    result = await analyze_precedents(test_state)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print("\nRANKED CASES (by court hierarchy):")
    for case in result['ranked_cases']:
        is_controlling = case in result['controlling_precedents']
        marker = " *** CONTROLLING PRECEDENT ***" if is_controlling else ""
        print(f"\n  Rank {case['precedent_rank']}: {case['name']} {case['citation']}{marker}")
        print(f"  Court: {case['court']}")
        print(f"  Court Level: {case['court_level_name']} (Authority: {case['court_level_value']})")

    print("\n" + "=" * 80)
    print("CONTROLLING PRECEDENT(S):")
    print("=" * 80)
    for case in result['controlling_precedents']:
        print(f"\n  {case['name']} {case['citation']}")
        print(f"  Court: {case['court_level_name']}")
        print(f"  This is the highest authority case that must be followed")

    print("\n" + "=" * 80)
    print("PRECEDENT ANALYSIS (LLM-generated):")
    print("=" * 80)
    print(f"\n{result['precedent_analysis']}")

    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_precedent_analysis())

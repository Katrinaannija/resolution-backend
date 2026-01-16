from typing import TypedDict, List

class Issue(TypedDict, total=False):
    date_event: str
    undisputed_facts: str
    claimant_position: str
    defendant_position: str
    legal_issue: str
    relevant_documents: List[str]

class CaseMetadata(TypedDict, total=False):
    name: str
    citation: str
    court: str
    date: str
    url: str
    keyword_set: str
    court_level: int  # Precedential authority level
    court_level_value: int  # Numeric value for sorting
    court_level_name: str  # Human-readable court level
    precedent_rank: int  # Ranking by authority (1 = highest)

class CaseLawState(TypedDict, total=False):
    # index from court issues json, work on a specific issue
    issue_index: int
    issue: Issue

    # partial or final output of the pipeline
    # contains legal resolution on the issue
    recommendation: str
    # intermidiate value used for next iteration to resolve the issue
    suggestion: str
    # history of searched keywords
    seen_keywords: set[str]

    keywords: List[str]
    cases: List[dict]
    fetched_case_documents: List[str]  # Snippet text strings
    case_metadata: List[CaseMetadata]  # Metadata for each fetched case (parallel to fetched_case_documents)

    # Pipeline B: judgement focus analysis
    focus_area: str

    # Joined output
    issue_guidelines: List[str]  # Changed to list to store multiple guidelines

    # Micro verdicts from update_recommendation
    micro_verdicts: List[dict]  # List of micro verdicts generated from issue guidelines

    # Supporting cases for the final recommendation
    supporting_cases: List[dict]  # Cases cited in the recommendation with principles

    # Precedent analysis
    controlling_precedents: List[dict]  # The highest authority case(s)
    precedent_analysis: str  # LLM analysis of case relationships (agreement/distinction)
    ranked_cases: List[dict]  # All cases ranked by authority

    solved: bool
    documents: bool
    case_law: bool

    output_text: str

def create_initial_state(issue_index: int = 0) -> CaseLawState:
    """Create a CaseLawState with default values initialized."""
    return CaseLawState(
        issue_index=issue_index,
        issue=Issue(
            date_event="",
            undisputed_facts="",
            claimant_position="",
            defendant_position="",
            legal_issue="",
            relevant_documents=[]
        ),
        recommendation="",
        suggestion="",
        seen_keywords=set(),
        keywords=[],
        cases=[],
        fetched_case_documents=[],
        case_metadata=[],
        focus_area="",
        issue_guidelines=[],
        micro_verdicts=[],
        supporting_cases=[],
        controlling_precedents=[],
        precedent_analysis="",
        ranked_cases=[],
        output_text=""
    )
 
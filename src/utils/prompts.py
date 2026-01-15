"""
Local prompt definitions for all workflows.
This replaces the LangSmith prompt hub with local, version-controlled prompts.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Optional
import os

# Default model configuration
DEFAULT_MODEL = "gpt-4o-mini"
GLOBAL_MODEL_ENV_KEY = "GLOBAL_MODEL"

_cached_model: Optional[ChatOpenAI] = None
_cached_model_name: Optional[str] = None


def get_model(temperature: float = 0) -> ChatOpenAI:
    """Get configured ChatOpenAI model instance."""
    global _cached_model, _cached_model_name

    model_name = os.getenv(GLOBAL_MODEL_ENV_KEY, DEFAULT_MODEL)

    if _cached_model is None or model_name != _cached_model_name:
        _cached_model = ChatOpenAI(model=model_name, temperature=temperature)
        _cached_model_name = model_name

    return _cached_model


# ============================================================================
# SOC Agent Prompts
# ============================================================================

SOC_AGENT_USER_PROMPT = ChatPromptTemplate.from_messages([
    ("user", """Generate the structured statement of claim issues JSON by analysing the statement of claim, statement of defence, and the document table.

Use generate_soc_issue_table to build the JSON and persist it with write_court_issues_json so downstream agents can consume it.

Report once the issues file has been saved. Don't generate invalid characters, line breaks, or other non-JSON characters.""")
])

SOC_SYSTEM_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert legal document analyzer specializing in statement of claim and defence analysis.

Your role is to:
1. Carefully read and understand the statement of claim
2. Review the statement of defence
3. Identify all distinct legal issues raised
4. Extract relevant document references
5. Generate a structured JSON representation of court issues

Be thorough, accurate, and ensure all legal issues are captured systematically.""")
])

SOC_ISSUE_TABLE_PROMPT = ChatPromptTemplate.from_messages([
    ("user", """Based on the following legal documents, generate a structured court issues table in JSON format.

Statement of Claim:
{claim_text}

Statement of Defence:
{defence_text}

Document Details:
{document_details}

Generate a JSON object with the following structure:
{{
  "events": [
    {{
      "legal_issue": "Brief description of the legal issue",
      "plaintiff_position": "What the plaintiff claims",
      "defendant_position": "What the defendant responds",
      "key_facts": ["fact1", "fact2", ...],
      "relevant_documents": ["doc1", "doc2", ...]
    }}
  ]
}}

Ensure the output is valid JSON with no line breaks or invalid characters.""")
])


# ============================================================================
# Orchestrator Prompts
# ============================================================================

ORCHESTRATOR_ISSUE_ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an orchestration router for legal issue resolution.

Your job is to decide the next workflow action based on the current state of an issue.

Available actions:
- "case_law": Search and analyze relevant case law precedents
- "documents": Analyze evidence documents related to this issue
- "finalize": Mark the issue as resolved (all necessary work is complete)

Decision criteria:
- If requires_case_law is true and case_law is false: choose "case_law"
- If requires_documents is true and documents is false: choose "documents"
- If both case_law and documents are false (or completed): choose "finalize"
- If the issue is already solved: choose "finalize"
- Consider the recommendation and suggestion to determine if more work is needed"""),
    ("user", """Issue #{issue_index}: {legal_issue}

Current State:
- Solved: {solved}
- Requires Case Law: {requires_case_law}
- Requires Documents: {requires_documents}
- Case Law Complete: {case_law}
- Documents Complete: {documents}
- Seen Keywords: {seen_keywords}

Current Recommendation: {recommendation}

Current Suggestion: {suggestion}

Based on this state, what should be the next action?

Respond with a JSON object:
{{"next_action": "case_law|documents|finalize"}}""")
])

ORCHESTRATOR_JUDGEMENT_SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert judicial officer preparing a final judgement.

Your role is to:
1. Review all resolved legal issues
2. Consider the statements from both parties
3. Synthesize the recommendations from case law and document analysis
4. Draft a comprehensive judicial decision

The judgement should be clear, well-reasoned, and address each legal issue systematically."""),
    ("user", """Draft a final judgement based on the following information:

ISSUES ANALYSIS:
{issues_table}

CLAIMANT'S STATEMENT:
{claimant_statement}

DEFENDANT'S STATEMENT:
{defendant_statement}

Generate a comprehensive judgement that addresses each issue. Return a JSON object with the following structure:
{{
  "judgement": "The full text of the judicial decision",
  "summary": "A brief summary of the decision",
  "key_findings": ["finding1", "finding2", ...]
}}""")
])


# ============================================================================
# Case Law Workflow Prompts
# ============================================================================

CASE_LAW_KEYWORDS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a legal research specialist identifying case law search keywords.

Your task is to generate effective search keywords for finding relevant case law precedents."""),
    ("user", """Legal Issue: {legal_issue}

Issue Details:
{issue_description}

Previously Seen Keywords: {seen_keywords}

Generate 3-5 new search keywords that would help find relevant case law. Avoid repeating previously seen keywords.

Return a JSON object:
{{"keywords": ["keyword1", "keyword2", "keyword3"]}}""")
])

CASE_LAW_JUDGEMENT_FOCUS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a legal analyst identifying key focus areas for case law analysis."""),
    ("user", """Legal Issue: {legal_issue}

Issue Description:
{issue_description}

Identify the primary legal focus areas that should guide the case law search and analysis. What specific legal principles, doctrines, or precedents are most relevant?

Return a JSON object:
{{"focus_area": "Description of the key legal focus area for this issue"}}""")
])

CASE_LAW_ISSUE_GUIDELINES_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are synthesizing case law research and legal focus areas into actionable guidelines."""),
    ("user", """Legal Issue: {legal_issue}

Focus Area: {focus_area}

Retrieved Case Law:
{cases_summary}

Create comprehensive guidelines for resolving this issue based on the case law and focus area.

Return a JSON object:
{{"guidelines": ["guideline1", "guideline2", ...]}}""")
])

CASE_LAW_MICRO_VERDICT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are analyzing individual case law precedents to generate micro-verdicts."""),
    ("user", """Legal Issue: {legal_issue}

Case Document:
{case_document}

Guidelines:
{guidelines}

Analyze this case and generate a micro-verdict: how does this case precedent apply to the current legal issue?

Return a JSON object:
{{
  "case_name": "Name of the case",
  "relevance": "How relevant is this case (high/medium/low)",
  "key_principle": "The key legal principle from this case",
  "application": "How this principle applies to the current issue"
}}""")
])

CASE_LAW_AGG_RECOMMENDATIONS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are synthesizing multiple case law analyses into a final recommendation."""),
    ("user", """Legal Issue: {legal_issue}

Micro Verdicts:
{micro_verdicts}

Guidelines:
{guidelines}

Aggregate all the micro-verdicts and guidelines into a final recommendation and suggestion.

Return a JSON object:
{{
  "recommendation": "Final recommendation based on case law analysis",
  "suggestion": "Suggested next steps or actions",
  "solved": true/false,
  "requires_documents": true/false,
  "requires_case_law": true/false
}}""")
])


# ============================================================================
# Documents Workflow Prompts
# ============================================================================

DOCUMENTS_FOCUS_AREA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are identifying which documents are relevant to a specific legal issue."""),
    ("user", """Legal Issue: {legal_issue}

Issue Description:
{issue_description}

Available Documents:
{available_documents}

Identify which documents are most relevant to this legal issue and what information should be extracted from them.

Return a JSON object:
{{
  "relevant_documents": ["doc1", "doc2", ...],
  "extraction_focus": "What specific information to look for in these documents"
}}""")
])

DOCUMENTS_EXTRACT_CONTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are extracting relevant information from legal documents."""),
    ("user", """Legal Issue: {legal_issue}

Focus Area: {focus_area}

Document Name: {document_name}
Document Content:
{document_content}

Extract information from this document that is relevant to the legal issue and focus area.

Return a JSON object:
{{
  "document_name": "Name of the document",
  "relevant_excerpts": ["excerpt1", "excerpt2", ...],
  "key_findings": ["finding1", "finding2", ...],
  "summary": "Brief summary of relevant information"
}}""")
])

DOCUMENTS_CREATE_MICRO_VERDICT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are analyzing extracted document information to generate micro-verdicts."""),
    ("user", """Legal Issue: {legal_issue}

Document Information:
{document_info}

Generate a micro-verdict: what does this document evidence reveal about the legal issue?

Return a JSON object:
{{
  "document_name": "Name of the document",
  "verdict": "Analysis of what this document shows",
  "supports": "plaintiff|defendant|neutral",
  "strength": "strong|moderate|weak"
}}""")
])

DOCUMENTS_AGG_MICRO_VERDICTS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are synthesizing document analysis into a final recommendation."""),
    ("user", """Legal Issue: {legal_issue}

Document Micro Verdicts:
{micro_verdicts}

Aggregate all document analyses into a final recommendation and suggestion.

Return a JSON object:
{{
  "final_recommendation": "Final recommendation based on document analysis",
  "final_suggestion": "Suggested next steps or actions",
  "solved": true/false,
  "requires_documents": true/false,
  "requires_case_law": true/false
}}""")
])


# ============================================================================
# Prompt Registry
# ============================================================================

PROMPT_REGISTRY = {
    # SOC Agent
    "soc_agent_user_prompt": SOC_AGENT_USER_PROMPT,
    "soc_system_prompt": SOC_SYSTEM_PROMPT,
    "soc_issue_table": SOC_ISSUE_TABLE_PROMPT,

    # Orchestrator
    "orchestrator_issue_router": ORCHESTRATOR_ISSUE_ROUTER_PROMPT,
    "orchestrator_judgement_summary": ORCHESTRATOR_JUDGEMENT_SUMMARY_PROMPT,

    # Case Law Workflow
    "case_law_keywords": CASE_LAW_KEYWORDS_PROMPT,
    "case_law_judgement_focus": CASE_LAW_JUDGEMENT_FOCUS_PROMPT,
    "case_law_issue_guidelines": CASE_LAW_ISSUE_GUIDELINES_PROMPT,
    "case_law_micro_verdict": CASE_LAW_MICRO_VERDICT_PROMPT,
    "case_law_agg_recommendations": CASE_LAW_AGG_RECOMMENDATIONS_PROMPT,

    # Documents Workflow
    "documents_focus_area": DOCUMENTS_FOCUS_AREA_PROMPT,
    "documents_extract_content": DOCUMENTS_EXTRACT_CONTENT_PROMPT,
    "documents_create_micro_verdict": DOCUMENTS_CREATE_MICRO_VERDICT_PROMPT,
    "documents_agg_micro_verdicts": DOCUMENTS_AGG_MICRO_VERDICTS_PROMPT,
}


def get_prompt(name: str, include_model: bool = False):
    """
    Get a prompt by name from the local registry.

    Args:
        name: The prompt name
        include_model: If True, bind the prompt to a ChatOpenAI model

    Returns:
        The prompt template, optionally bound to a model
    """
    if name not in PROMPT_REGISTRY:
        raise ValueError(f"Prompt '{name}' not found in registry. Available prompts: {list(PROMPT_REGISTRY.keys())}")

    prompt = PROMPT_REGISTRY[name]

    if include_model:
        model = get_model()
        return prompt | model

    return prompt


async def get_prompt_async(name: str, include_model: bool = False):
    """
    Async version of get_prompt for compatibility.
    Since prompts are local, this is just a synchronous call wrapped for async context.
    """
    return get_prompt(name, include_model)

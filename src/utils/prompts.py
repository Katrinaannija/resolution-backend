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
    ("system", """You are an expert judicial officer preparing a final judgement with proper case law citations.

Your role is to:
1. Review all resolved legal issues and supporting case law
2. Consider the statements from both parties
3. Synthesize the recommendations with proper legal citations
4. Draft a comprehensive judicial decision that cites relevant precedents

CRITICAL: The judgement MUST include proper case citations in UK legal format.
- When referencing a legal principle, cite the case: "As established in Smith v Jones [2024] EWCA Civ 123..."
- Include direct quotes from precedents where appropriate
- Format citations in UK style (e.g., [2024] EWCA Civ 123)

The judgement should read like a professional UK court judgment with proper legal reasoning and citations."""),
    ("user", """Draft a final judgement based on the following information:

ISSUES ANALYSIS:
{issues_table}

CASE LAW CITATIONS (cite these in your judgment):
{case_citations}

CLAIMANT'S STATEMENT:
{claimant_statement}

DEFENDANT'S STATEMENT:
{defendant_statement}

TASK: Generate a comprehensive judgement that:
1. Addresses each issue systematically
2. Cites relevant case law for each legal principle
3. Includes direct quotes from precedents where provided
4. Follows UK judicial writing style

Return a JSON object with the following structure:
{{
  "judgement": "The full text of the judicial decision WITH PROPER CASE CITATIONS (e.g., 'As held in Smith v Jones [2024] EWCA Civ 123, the test for...')",
  "summary": "A brief summary of the decision",
  "key_findings": ["finding1", "finding2", ...]
}}

IMPORTANT: Your judgement text MUST include case names and citations when discussing legal principles.""")
])


# ============================================================================
# Case Law Workflow Prompts
# ============================================================================

CASE_LAW_KEYWORDS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert UK legal research specialist optimizing searches for the UK National Archives case law database (caselaw.nationalarchives.gov.uk).

Your expertise includes:
- UK legal taxonomy and terminology (common law, equity, statute)
- Multi-tier keyword strategy (broad principles → specific doctrines → factual patterns)
- UK court hierarchy and citation formats
- Effective search query construction for legal databases

Your goal is to generate keywords that will find the most relevant UK case law precedents."""),
    ("user", """Legal Issue: {legal_issue}

Issue Context:
- Date/Event: {date_event}
- Undisputed Facts: {undisputed_facts}
- Claimant Position: {claimant_position}
- Defendant Position: {defendant_position}
- Relevant Documents: {relevant_documents}

Previously Seen Keywords: {seen_keywords}

TASK: Generate {num_keywords} NEW search keywords for UK National Archives case law database that target the CORE LEGAL PRINCIPLES at the heart of this issue.

CRITICAL: Your keywords must hit the "sweet spot" - not too generic (e.g., "contract law"), not too narrow (e.g., "breach of section 2.3.1 of agreement"), but targeting the fundamental legal principle that will appear in case law judgments.

STEP-BY-STEP PROCESS:

Step 1: IDENTIFY THE CORE LEGAL PRINCIPLE
Ask yourself:
- What is the fundamental legal question this issue is asking? (e.g., "When does silence constitute acceptance in contract formation?")
- What legal test, doctrine, or rule will determine the outcome? (e.g., "remoteness of damages test", "duty of care in negligent misstatement")
- What would a judge cite to resolve this? (e.g., "principles of contractual interpretation", "implied terms for business efficacy")

Step 2: GENERATE BALANCED KEYWORDS (Use this exact structure for {num_keywords} keywords):
- 2 BROAD LEGAL PRINCIPLES: Core doctrines that judges would cite (e.g., "breach of implied term", "duty of care professional negligence", "remoteness of damage in contract")
- 2 SPECIFIC LEGAL DOCTRINES: Precise UK legal tests or rules (e.g., "Hadley v Baxendale reasonable contemplation", "contra proferentem exclusion clause", "reasonable foreseeability negligence")
- 1 FACTUAL PATTERN: The specific scenario in legal terms (e.g., "late payment commercial contract damages", "defective goods breach of warranty", "negligent advice reliance loss")

EXAMPLES OF GOOD VS BAD KEYWORDS:

Issue: "Whether the defendant breached the contract by delivering goods late, causing the claimant to lose a lucrative resale opportunity"

❌ TOO GENERIC: "contract law", "breach", "damages"
❌ TOO NARROW: "late delivery", "resale contract", "2 week delay"
✅ CORE PRINCIPLES:
  - "breach of contract time of performance" (broad principle)
  - "Hadley v Baxendale consequential loss" (specific doctrine)
  - "late delivery loss of profit reasonable contemplation" (factual pattern with legal element)

Issue: "Whether the solicitor owed a duty of care when advising on a property transaction"

❌ TOO GENERIC: "negligence", "solicitor", "duty of care"
❌ TOO NARROW: "property transaction advice", "solicitor negligence 2020"
✅ CORE PRINCIPLES:
  - "professional negligence solicitor duty of care" (broad principle)
  - "negligent advice reliance reasonable foreseeability" (specific doctrine)
  - "solicitor negligent property advice scope of duty" (factual pattern with legal element)

QUALITY CHECKS:
✓ Would a judge use these terms when citing precedents?
✓ Do these terms appear in the ratio decidendi (legal reasoning) of judgments?
✓ Do they capture the legal principle, not just the facts?
✓ Are they specific enough to find relevant cases but broad enough to find multiple precedents?

AVOID:
- Repeating keywords from "Previously Seen Keywords"
- Generic terms without legal context (e.g., "payment", "delay", "advice")
- Overly factual terms without legal principles (e.g., "3 month delay", "£50,000 loss")
- Case names (unless the case name IS the doctrine, e.g., "Hadley v Baxendale")
- Terms that wouldn't appear in a judgment's legal analysis

Return a JSON object with EXACTLY {num_keywords} keywords:
{{"keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]}}

Each keyword must target the core legal principle and be optimized for finding case law that addresses the fundamental legal question.""")
])

CASE_LAW_JUDGEMENT_FOCUS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a legal analyst identifying key focus areas for case law analysis."""),
    ("user", """Legal Issue: {legal_issue}

Issue Context:
- Date/Event: {date_event}
- Undisputed Facts: {undisputed_facts}
- Claimant Position: {claimant_position}
- Defendant Position: {defendant_position}

Current Analysis State:
- Current Recommendation: {recommendation}
- Current Suggestions: {suggestions}

Identify the primary legal focus areas that should guide the case law search and analysis. What specific legal principles, doctrines, or precedents are most relevant?

Return a JSON object:
{{"focus_area": "Description of the key legal focus area for this issue"}}""")
])

CASE_LAW_ISSUE_GUIDELINES_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a legal analyst extracting key principles and quotes from case law judgments.

Your role is to:
1. Identify the core legal principles established in the judgment
2. Extract direct quotes that support these principles
3. Preserve proper case citations for all extracted content
4. Focus on the ratio decidendi (legal reasoning) not obiter dicta"""),
    ("user", """Focus Area: {focus_area}

Case Citation: {case_citation}
Case Name: {case_name}
Citation: {citation}
Court: {court}
Date: {date}

Retrieved Judgment Snippets:
{court_judgment}

TASK: Extract legal principles and quotes from this case that are relevant to the focus area.

Your output should include:
1. CASE CITATION: Full citation of the case
2. LEGAL PRINCIPLES: Key legal tests, doctrines, or rules established
3. KEY QUOTES: 1-2 direct quotes that establish these principles (with quotation marks)
4. APPLICATION: How these principles apply to similar fact patterns

Format your response as structured text following this template:

CASE: {case_name} {citation}

LEGAL PRINCIPLES ESTABLISHED:
- [Principle 1]
- [Principle 2]

KEY QUOTES:
1. "[Direct quote from judgment]"
2. "[Direct quote from judgment]"

RELEVANCE TO ISSUE:
[Brief explanation of how this case applies to the focus area]

Be precise and cite the case name and citation in your guidelines so this information is preserved for the final judgment.""")
])

CASE_LAW_MICRO_VERDICT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are analyzing case law guidelines to generate micro-verdicts for legal issues."""),
    ("user", """Legal Issue: {legal_issue}

Issue Context:
- Date/Event: {date_event}
- Undisputed Facts: {undisputed_facts}
- Claimant Position: {claimant_position}
- Defendant Position: {defendant_position}
- Relevant Documents: {relevant_documents}

Current Recommendation: {recommendation}

Case Law Guidelines:
{issue_guidelines}

Based on these guidelines, generate a micro-verdict with a recommendation and suggestion for resolving this legal issue.

Return a JSON object:
{{
  "recommendation": "Specific recommendation based on this guideline",
  "suggestion": "Suggested next steps",
  "solved": true/false,
  "documents": true/false,
  "case_law": true/false
}}""")
])

CASE_LAW_AGG_RECOMMENDATIONS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are synthesizing multiple case law analyses into a final recommendation with proper citations.

Your role is to:
1. Aggregate findings from all micro-verdicts
2. Identify the 2-3 most relevant cases that support the recommendation
3. Extract key legal principles and quotes from these cases
4. Format citations properly for inclusion in a legal judgment"""),
    ("user", """Legal Issue: {legal_issue}

Issue Context:
- Date/Event: {date_event}
- Undisputed Facts: {undisputed_facts}
- Claimant Position: {claimant_position}
- Defendant Position: {defendant_position}

Micro Verdicts (each contains case law analysis with citations):
{micro_verdicts}

TASK: Aggregate all micro-verdicts into a final recommendation and identify the supporting cases.

Return a JSON object with the following structure:
{{
  "recommendation": "Final recommendation with inline citations (e.g., 'As established in Smith v Jones [2024] EWCA Civ 123...')",
  "suggestion": "Suggested next steps or actions",
  "solved": true/false,
  "requires_documents": true/false,
  "requires_case_law": true/false,
  "supporting_cases": [
    {{
      "case_name": "Smith v Jones",
      "citation": "[2024] EWCA Civ 123",
      "principle": "The specific legal principle established",
      "quote": "Direct quote from the judgment (if available)",
      "relevance": "Why this case is relevant to the current issue"
    }}
  ]
}}

IMPORTANT:
- Include 2-3 of the MOST RELEVANT cases in "supporting_cases"
- Extract case names and citations from the micro verdicts
- Include direct quotes where available
- The "recommendation" text should reference these cases by name""")
])


# ============================================================================
# Documents Workflow Prompts
# ============================================================================

DOCUMENTS_FOCUS_AREA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are identifying which documents are relevant to a specific legal issue."""),
    ("user", """Legal Issue: {legal_issue}

Issue Context:
- Date/Event: {date_event}
- Undisputed Facts: {undisputed_facts}
- Claimant Position: {claimant_position}
- Defendant Position: {defendant_position}
- Relevant Documents: {relevant_documents}

Current Analysis State:
- Current Recommendation: {recommendation}
- Current Suggestion: {suggestion}

Available Documents:
{all_document_details}

Identify which documents are most relevant to this legal issue and what information should be extracted from them.

Return a JSON object:
{{
  "file_focus": "What specific information to look for in these documents",
  "file_names": ["doc1", "doc2", ...]
}}""")
])

DOCUMENTS_EXTRACT_CONTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are extracting relevant information from legal documents."""),
    ("user", """Focus Area: {focus_area}

Document Name: {filename}
Document Content:
{document_content}

Extract information from this document that is relevant to the focus area.

Provide a clear, structured summary of the relevant information found in this document.""")
])

DOCUMENTS_CREATE_MICRO_VERDICT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are analyzing extracted document information to generate micro-verdicts."""),
    ("user", """Legal Issue: {legal_issue}

Issue Context:
- Date/Event: {date_event}
- Undisputed Facts: {undisputed_facts}
- Claimant Position: {claimant_position}
- Defendant Position: {defendant_position}

Current Recommendation: {recommendation}

Document: {filename}
Extracted Information:
{document_content}

Generate a micro-verdict: what does this document evidence reveal about the legal issue?

Return a JSON object:
{{
  "recommendation": "Recommendation extension based on this document",
  "suggestion": "Suggested next steps based on this evidence",
  "solved": true/false,
  "documents": true/false,
  "case_law": true/false
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

"""
Example usage of the documents workflow.

This workflow takes an issue, existing recommendation, and suggestion,
then researches relevant documents to extend and improve the recommendation.
"""

import os

GLOBAL_MODEL = os.getenv("GLOBAL_MODEL", "gpt-5.1-mini")
# Override this value when iterating with smaller models.
os.environ["GLOBAL_MODEL"] = GLOBAL_MODEL

from src.documents.documents_state import DocumentsState, Issue, create_initial_documents_state
from src.documents_workflow import graph

def run_documents_workflow_example():
    """
    Example of running the documents workflow with sample data.
    """
    # Sample issue
    sample_issue = Issue(
        date_event="2011-04-15",
        undisputed_facts="Company A provided ICT services to Company B under a framework agreement.",
        claimant_position="Company A claims payment for services rendered as per contract.",
        defendant_position="Company B disputes the validity of certain invoices.",
        legal_issue="Whether the disputed invoices are valid and enforceable under the contract terms.",
        relevant_documents=["D - eDesk Agreement.md", "I - Invoice (1).md", "K - Invoice (disputed 1).md"]
    )
    
    # Sample existing recommendation and suggestion (could be from case law analysis)
    sample_recommendation = """
    Based on preliminary analysis, the contract terms appear to support Company A's position.
    However, more document evidence is needed to verify the specific services rendered.
    """
    
    sample_suggestion = """
    Review invoices and supporting documentation to confirm service delivery dates and scope.
    Check email correspondence for any disputes raised during the contract period.
    """
    
    # Create initial state
    initial_state = create_initial_documents_state(
        issue=sample_issue,
        recommendation=sample_recommendation,
        suggestion=sample_suggestion
    )
    
    print("=" * 80)
    print("DOCUMENTS WORKFLOW EXAMPLE")
    print("=" * 80)
    print("\nInitial Issue:")
    print(f"Date: {sample_issue['date_event']}")
    print(f"Legal Issue: {sample_issue['legal_issue']}")
    print(f"\nInitial Recommendation:\n{sample_recommendation}")
    print(f"\nInitial Suggestion:\n{sample_suggestion}")
    print("\n" + "=" * 80)
    print("Starting workflow...\n")
    
    # Run the workflow
    result = graph.invoke(initial_state)
    
    print("\n" + "=" * 80)
    print("WORKFLOW RESULTS")
    print("=" * 80)
    
    print(f"\nFile Instructions Generated: {len(result.get('file_instructions', []))}")
    for idx, instruction in enumerate(result.get('file_instructions', []), 1):
        print(f"\n{idx}. File: {instruction['filename']}")
        print(f"   Goals: {instruction['extraction_goals'][:100]}...")
    
    print(f"\n\nDocuments Processed: {len(result.get('document_infos', []))}")
    
    print(f"\n\nMicro Verdicts Created: {len(result.get('micro_verdicts', []))}")
    
    print("\n" + "-" * 80)
    print("\nFINAL RECOMMENDATION:")
    print("-" * 80)
    print(result.get('final_recommendation', 'No recommendation generated'))
    
    print("\n" + "-" * 80)
    print("\nFINAL SUGGESTION:")
    print("-" * 80)
    print(result.get('final_suggestion', 'No suggestion generated'))
    
    return result

if __name__ == "__main__":
    result = run_documents_workflow_example()


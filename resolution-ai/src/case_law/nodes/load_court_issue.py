import json
from src.case_law.case_law_state import CaseLawState

def load_court_issue(state: CaseLawState) -> CaseLawState:
  with open("dataset/court_issues/court_issues.json", "r") as f:
    data = json.load(f)
  
  issue_index = state["issue_index"]
  event = data["events"][issue_index]
  
  return {
    "issue": {
      "date_event": event["date_event"],
      "undisputed_facts": event["undisputed_facts"],
      "claimant_position": event["claimant_position"],
      "defendant_position": event["defendant_position"],
      "legal_issue": event["legal_issue"],
      "relevant_documents": event["relevant_documents"]
    }
  }
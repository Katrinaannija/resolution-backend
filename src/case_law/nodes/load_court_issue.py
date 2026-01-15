from src.case_law.case_law_state import CaseLawState
from src.utils.json_sanitize import load_json_file

def load_court_issue(state: CaseLawState) -> CaseLawState:
  data = load_json_file("dataset/court_issues/court_issues.json")
  
  issue_index = state["issue_index"]
  event = data["events"][issue_index]
  
  return {
      "issue": {
          "date_event": event.get("date_event", ""),
          "undisputed_facts": event.get("undisputed_facts", ""),
          "claimant_position": event.get("claimant_position", ""),
          "defendant_position": event.get("defendant_position", ""),
          "legal_issue": event.get("legal_issue", ""),
          "relevant_documents": event.get("relevant_documents", []) or [],
      }
  }

from src.case_law.case_law_state import CaseLawState
from src.tools.case_law_search import search_case_law


def search_caselaw(state: CaseLawState) -> CaseLawState:
  keywords = state["keywords"]
  all_cases = []

  for keyword_set in keywords:
    results = search_case_law.invoke({"query": keyword_set, "page": 1, "results_per_page": 3})

    for idx, court_judgment in enumerate(results):
      if idx >= 3:
        break

      all_cases.append({
        "keyword_set": keyword_set,
        'name': court_judgment["name"],
        'citation': court_judgment["citation"],
        'court': court_judgment["court"],
        'date': court_judgment["date"],
        'url': court_judgment["url"]
      })

  return {"cases": all_cases}

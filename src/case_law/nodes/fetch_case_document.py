from src.case_law.case_law_state import CaseLawState
from src.tools.case_law_search import get_case_judgment
from src.tools.snippet_extractor import extract_keyword_snippets


def fetch_case_document(
    state: CaseLawState
) -> CaseLawState:
    cases = state["cases"]
    
    visited_urls = set()
    fetched_documents = []
    
    for case_entry in cases:
      case_url = case_entry["url"]
      keyword_set = case_entry["keyword_set"]
      
      if case_url in visited_urls:
        continue
      
      visited_urls.add(case_url)
      judgment = get_case_judgment.invoke({"case_uri": case_url})
      
      if judgment is None:
        continue

      snippets = extract_keyword_snippets(
          judgment_text=judgment,
          keyword_set=keyword_set,
          words_before=500,
          words_after=500,
          max_snippets=20
      )
      
      fetched_documents.append(snippets)

    return {"fetched_case_documents": fetched_documents}


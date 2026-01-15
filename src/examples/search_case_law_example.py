"""
Example script demonstrating how to use the case law search tool.
"""

import os

GLOBAL_MODEL = os.getenv("GLOBAL_MODEL", "gpt-5.1-mini")
# Override this value when iterating with smaller models.
os.environ["GLOBAL_MODEL"] = GLOBAL_MODEL

from src.tools.case_law_search import (
    search_case_law, 
    get_case_law_details,
    get_case_judgment,
    get_case_metadata
)


def main():
    # Example 1: Search for cases related to contract breach
    print("=" * 80)
    print("Example 1: Searching for 'contract breach'")
    print("=" * 80)
    result = search_case_law.invoke({"query": "contract breach", "results_per_page": 5})
    print(result)
    print("\n\n")
    
    # Example 2: Get metadata only (without full judgment text)
    print("=" * 80)
    print("Example 2: Getting case metadata only")
    print("=" * 80)
    case_uri = "/ewhc/ch/2025/3107"
    result = get_case_metadata.invoke({"case_uri": case_uri})
    print(result)
    print("\n\n")
    
    # Example 3: Get full judgment text
    print("=" * 80)
    print("Example 3: Getting full judgment text")
    print("=" * 80)
    result = get_case_judgment.invoke({"case_uri": case_uri})
    print(result[:50000])
    print("\n\n")
    
    # Example 4: Get case details (summary with truncated judgment)
    print("=" * 80)
    print("Example 4: Getting case details (original function)")
    print("=" * 80)
    result = get_case_law_details.invoke({"case_uri": case_uri})
    print(result[:1500])
    print("\n...truncated for display...")


if __name__ == "__main__":
    main()


import os

GLOBAL_MODEL = os.getenv("GLOBAL_MODEL", "gpt-5.1-mini")
# Override this value when iterating with smaller models.
os.environ["GLOBAL_MODEL"] = GLOBAL_MODEL

from src.case_law_workflow import graph

result = graph.invoke({"issue_index": 0})

print(result["output_text"])


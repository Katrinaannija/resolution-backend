import json
import re
from typing import Any

from langchain_core.messages import BaseMessage

from src.utils.prompt_output import coerce_prompt_output
from langchain_core.tools import tool

from src.utils.pull_prompt import pull_prompt


def make_generate_soc_issue_table():

  _CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

  def _strip_control_chars(text: str) -> str:
      return _CONTROL_CHARS_RE.sub("", text)

  def _extract_json_block(text: str) -> str:
      start = text.find("{")
      end = text.rfind("}")
      if start == -1 or end == -1 or end <= start:
          return text
      return text[start : end + 1]

  def _parse_soc_issue_output(text: str) -> dict:
      candidates = [text]
      cleaned = _strip_control_chars(text)
      if cleaned != text:
          candidates.append(cleaned)
      candidates.append(_extract_json_block(cleaned))
      for candidate in candidates:
          candidate = candidate.strip()
          if not candidate:
              continue
          try:
              parsed = json.loads(candidate)
          except json.JSONDecodeError:
              continue
          return parsed if isinstance(parsed, dict) else {"events": parsed}
      return {"events": [], "raw_output": cleaned}

  def _normalize_json_output(output: Any) -> str:
      if isinstance(output, BaseMessage):
          output = output.content
      if isinstance(output, (dict, list)):
          return json.dumps(output, indent=2)
      if isinstance(output, str):
          parsed = _parse_soc_issue_output(output)
          return json.dumps(parsed, indent=2)
      parsed = coerce_prompt_output(output)
      return json.dumps(parsed, indent=2)

  @tool
  def generate_soc_issue_table(
      claimant_statement: str,
      defendant_statement: str,
      table_of_documents: str,
  ) -> str:
      """Generates statement of claim issues table from provided document contents.
      
      Args:
          claimant_statement: The full text content of the claimant's statement
          defendant_statement: The full text content of the defendant's statement  
          table_of_documents: The document details/table listing all available documents
          
      Returns:
          JSON string containing the generated court issues table
      """
      soc_issue_table_prompt = pull_prompt("soc_issue_table", include_model=True)
      
      output = soc_issue_table_prompt.invoke(
          {
              "claim_text": claimant_statement,
              "defence_text": defendant_statement,
              "document_details": table_of_documents,
          }
      )

      return _normalize_json_output(output)

  return generate_soc_issue_table

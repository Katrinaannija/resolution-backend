import json
from langchain_core.tools import tool

from src.utils.pull_prompt import pull_prompt


def make_generate_soc_issue_table():

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
      
      output_json = json.dumps(output, indent=2)
      
      return output_json

  return generate_soc_issue_table

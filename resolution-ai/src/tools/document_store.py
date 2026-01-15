from pathlib import Path
from langchain.tools import tool

docs_dir = Path(__file__).parent.parent.parent

documents_path = docs_dir / "dataset" / "documents"
all_doc_details_path = docs_dir / "dataset" / "document_details" / "document_details.md"

court_issues_dir = docs_dir / "dataset" / "court_issues"
court_issues_file_path = docs_dir / "dataset" / "court_issues" / "court_issues.json"


@tool
def retrieve_document(filename: str) -> str:
    """Retrieve contents of a document from the dataset folder by filename."""
    
    file_path = documents_path / filename
    
    if not file_path.exists():
        return f"Error: File '{filename}' not found in dataset"
    
    return file_path.read_text()

@tool
def list_documents() -> str:
    """List all documents available in the dataset folder."""
    files = [f.name for f in documents_path.iterdir() if f.is_file()]
    return "\n".join(sorted(files))

@tool
def get_all_document_details() -> str:
  """Retrieve detailed information about all documents available"""
  return all_doc_details_path.read_text()

@tool
def write_court_issues_json(content: str) -> str:
  """Saves court issues document to disk as json file"""

  court_issues_dir.mkdir(parents=True, exist_ok=True)
  if court_issues_file_path.write_text(content) == 1:
    return "Failed to save the file"
  
  return f"Court issues written succesfully to {court_issues_file_path}"
  
  
  


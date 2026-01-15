import requests
from langchain_core.tools import tool
from bs4 import BeautifulSoup

@tool
def search_case_law(query: str, page: int = 1, results_per_page: int = 10) -> list:
    """
    Search UK National Archives case law database by keywords.
    
    Args:
        query: Search keywords or terms (e.g., "contract breach", "negligence")
        page: Page number for pagination (default: 1)
        results_per_page: Number of results per page (default: 10, max: 50)
    
    Returns:
        Dictionary containing:
        - text: Formatted string with search results
        - cases: List of dicts with 'url' and 'result' (metadata) for each case
    """
    base_url = "https://caselaw.nationalarchives.gov.uk/search"
    
    params = {
        "query": query,
        "page": page,
        "per_page": results_per_page,
        "order": "relevance"  # Can also be "date"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ResolutionAI/1.0)",
        "Accept": "text/html"
    }
    
    response = requests.get(base_url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    return _parse_html_results(response.text, query)


def _parse_html_results(html: str, query: str) -> list:
    soup = BeautifulSoup(html, 'html.parser')

    results = []
    
    # Find the results table
    results_table = soup.find('table')
    if not results_table:
        return []
    
    # Get all result rows (skip header row)
    result_rows = results_table.find_all('tr')[1:]  # Skip header row
    
    for row in result_rows:
      cells = row.find_all('td')
      if len(cells) < 3:
          continue
          
      # First cell contains case info
      case_cell = cells[0]
      
      # Find the main div container
      main_div = case_cell.find('div')
      if not main_div:
          continue
      
      # Extract case name and link from the title div
      title_div = main_div.find('div', class_='judgments-table__title')
      if not title_div:
          continue
          
      link_elem = title_div.find('a')
      if not link_elem:
          continue
          
      case_name = link_elem.get_text(strip=True)
      href = link_elem.get('href', '')
      # Remove query parameter from URL for cleaner display
      if '?' in href:
          href = href.split('?')[0]
      url = f"https://caselaw.nationalarchives.gov.uk{href}" if href.startswith('/') else href
      
      # Extract court/tribunal name from the subtitle div
      subtitle_div = main_div.find('div', class_='judgments-table__subtitle')
      court = subtitle_div.get_text(strip=True) if subtitle_div else "N/A"
      
      # Second cell contains citation
      citation = cells[1].get_text(strip=True) if len(cells) > 1 else "N/A"
      
      # Third cell contains date
      date = cells[2].get_text(strip=True) if len(cells) > 2 else "N/A"
      
      results.append({
        'name': case_name,
        'citation': citation,
        'court': court,
        'date': date,
        'url': url
      })
    
    return results
    

@tool
def get_case_law_details(case_uri: str) -> str:
    """
    Retrieve full details of a specific case by its URI.
    
    Args:
        case_uri: The URI path of the case (e.g., "/ewhc/ch/2025/3107")
    
    Returns:
        Full text and metadata of the judgment/decision.
    """
    
    # Ensure URI starts with /
    if not case_uri.startswith('/'):
        case_uri = f"/{case_uri}"
    
    url = f"https://caselaw.nationalarchives.gov.uk{case_uri}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ResolutionAI/1.0)",
        "Accept": "text/html"
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract case name
    case_name = soup.find('h1')
    case_name_text = case_name.get_text(strip=True) if case_name else "Unknown Case"
    
    # Extract citation
    citation = soup.find('span', class_='neutral-citation')
    citation_text = citation.get_text(strip=True) if citation else "N/A"
    
    # Extract judgment text
    judgment_body = soup.find('div', class_='judgment-body') or soup.find('main')
    judgment_text = judgment_body.get_text(strip=True, separator='\n\n') if judgment_body else "Unable to extract judgment text"
    
    output = [
        f"Case: {case_name_text}",
        f"Citation: {citation_text}",
        f"URL: {url}",
        "=" * 80,
        "",
        judgment_text[:5000] + "..." if len(judgment_text) > 5000 else judgment_text
    ]
    
    return "\n".join(output)
            


@tool
def get_case_judgment(case_uri: str) -> str:
    """
    Retrieve the full judgment text of a specific case.
    
    Args:
        case_uri: The URI path of the case (e.g., "/ewhc/ch/2025/3107") or full URL
    Returns:
        Complete judgment text with basic formatting preserved.
    """
    if case_uri.startswith('http'):
        url = case_uri
    else:
        # Ensure URI starts with /
        if not case_uri.startswith('/'):
            case_uri = f"/{case_uri}"
        url = f"https://caselaw.nationalarchives.gov.uk{case_uri}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ResolutionAI/1.0)",
        "Accept": "text/html"
    }
    
    try:
      response = requests.get(url, headers=headers, timeout=30)
      response.raise_for_status()   # optional: raises for 4xx/5xx
    except requests.exceptions.Timeout:
      print("The request timed out.")
      return None
    except requests.exceptions.RequestException as e:
      print(f"Request failed: {e}") 
      return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract case name
    case_name = soup.find('h1')
    case_name_text = case_name.get_text(strip=True) if case_name else "Unknown Case"
    
    # Extract citation
    citation_elem = soup.find('span', class_='ncn-nowrap')
    citation_text = citation_elem.get_text(strip=True) if citation_elem else "N/A"
    
    # Extract court from header paragraphs  
    court_text = "N/A"
    # Find all paragraphs in the first section
    all_paras = soup.find_all('p', limit=20)
    court_parts = []
    for para in all_paras:
        text = para.get_text(strip=True)
        # Look for court indicators in the text
        if ('COURT' in text or 'TRIBUNAL' in text) and len(text) < 150:
            court_parts.append(text)
        # Stop after we've found some court info and hit "Before" or "Between"
        if court_parts and ('Before' in text or 'Between' in text):
            break
    
    if court_parts:
        court_text = ' - '.join(court_parts[:3])  # Take max first 3 lines
    
    # Extract date
    date_text = "N/A"
    date_div = soup.find('div', class_='judgment-header__date')
    if date_div:
        date_text = date_div.get_text(strip=True).replace('Date:', '').strip()
    
    # Extract judgment text - preserve paragraph structure
    judgment_body = soup.find('section', class_='judgment-body')
    if not judgment_body:
        judgment_body = soup.find('div', class_='judgment-body')
    
    if judgment_body:
        # Get text with paragraph breaks preserved
        paragraphs = []
        for para in judgment_body.find_all(['p', 'div', 'h2', 'h3', 'h4']):
            text = para.get_text(strip=True)
            if text:
                paragraphs.append(text)
        
        judgment_text = '\n\n'.join(paragraphs)
    else:
        judgment_text = "Unable to extract judgment text"
    
    output_parts = [
        f"Case: {case_name_text}",
        f"Citation: {citation_text}",
        f"Court: {court_text}",
        f"Date: {date_text}",
        f"URL: {url}",
        "=" * 80,
        "",
        judgment_text
    ]
            
    return "\n".join(output_parts)
        


@tool
def get_case_metadata(case_uri: str) -> str:
    """
    Retrieve metadata about a specific case without the full judgment text.
    
    Args:
        case_uri: The URI path of the case (e.g., "/ewhc/ch/2025/3107")
    
    Returns:
        Case metadata including name, citation, court, date, judges, and parties.
    """
    # Ensure URI starts with /
    if not case_uri.startswith('/'):
        case_uri = f"/{case_uri}"
    
    url = f"https://caselaw.nationalarchives.gov.uk{case_uri}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ResolutionAI/1.0)",
        "Accept": "text/html"
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract metadata
    metadata = {}
    
    # Case name
    case_name = soup.find('h1')
    metadata['case_name'] = case_name.get_text(strip=True) if case_name else "Unknown"
    
    # Citation
    citation_elem = soup.find('span', class_='ncn-nowrap')
    metadata['citation'] = citation_elem.get_text(strip=True) if citation_elem else "N/A"
    
    # Case number
    case_num_div = soup.find('div', class_='judgment-header__case-number')
    metadata['case_number'] = case_num_div.get_text(strip=True).replace('Case No:', '').strip() if case_num_div else "N/A"
    
    # Court - extract from paragraphs
    metadata['court'] = "N/A"
    all_paras = soup.find_all('p', limit=20)
    court_parts = []
    for para in all_paras:
        text = para.get_text(strip=True)
        # Look for court indicators in the text
        if ('COURT' in text or 'TRIBUNAL' in text) and len(text) < 150:
            court_parts.append(text)
        # Stop after we've found some court info and hit "Before" or "Between"
        if court_parts and ('Before' in text or 'Between' in text):
            break
    
    if court_parts:
        metadata['court'] = ' - '.join(court_parts[:3])  # Take max first 3 lines
    
    # Date
    date_div = soup.find('div', class_='judgment-header__date')
    metadata['date'] = date_div.get_text(strip=True).replace('Date:', '').strip() if date_div else "N/A"
    
    # Judge - look for "Before:" section
    metadata['judges'] = []
    all_paras = soup.find_all('p', limit=30)
    found_before = False
    for para in all_paras:
        text = para.get_text(strip=True)
        if 'Before' in text and ':' in text:
            found_before = True
            continue
        if found_before and text and 'Between' not in text:
            metadata['judges'].append(text)
            break
    
    if not metadata['judges']:
        metadata['judges'] = ["N/A"]
    
    # Parties - extract from table or subsequent paragraphs
    metadata['parties'] = []
    # Look for the parties table
    parties_table = soup.find('table', class_='pr-two-column')
    if parties_table:
        party_cells = parties_table.find_all('p')
        for cell in party_cells:
            text = cell.get_text(strip=True)
            if text and text not in ['-', 'and', '-and-', '']:
                metadata['parties'].append(text)
    
    if not metadata['parties']:
        metadata['parties'] = ["N/A"]
    
    # Format output
    output = [
        f"Case Name: {metadata['case_name']}",
        f"Citation: {metadata['citation']}",
        f"Case Number: {metadata['case_number']}",
        f"Court: {metadata['court']}",
        f"Date: {metadata['date']}",
        f"URL: {url}",
        "",
        "Judge(s):",
    ]
    
    for judge in metadata['judges']:
        output.append(f"  - {judge}")
    
    if metadata['parties'] != ["N/A"]:
        output.append("")
        output.append("Parties:")
        for i, party in enumerate(metadata['parties'], 1):
            output.append(f"  {i}. {party}")
    
    return "\n".join(output)
        


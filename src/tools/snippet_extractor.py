import re
from typing import List, Tuple


def parse_keywords(keyword_set: str) -> List[str]:
    """
    Parse keyword set into individual search terms.
    Handles phrases in quotes as single terms.
    
    Args:
        keyword_set: Search query string (e.g., '"environmental matters" subsidiary')
    
    Returns:
        List of search terms (phrases and individual words)
    """
    terms = []
    
    # Extract phrases in quotes
    phrase_pattern = r'"([^"]+)"'
    phrases = re.findall(phrase_pattern, keyword_set)
    terms.extend(phrases)
    
    # Remove quoted phrases and get remaining words
    remaining = re.sub(phrase_pattern, '', keyword_set)
    words = remaining.split()
    terms.extend(words)
    
    return [term.strip() for term in terms if term.strip()]


def find_keyword_positions(text: str, keywords: List[str]) -> List[Tuple[int, int, str]]:
    """
    Find all positions where keywords appear in text.
    
    Args:
        text: The judgment text to search
        keywords: List of keyword terms (phrases or words)
    
    Returns:
        List of tuples (start_pos, end_pos, matched_keyword)
    """
    positions = []
    text_lower = text.lower()
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        start = 0
        
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break
            
            positions.append((pos, pos + len(keyword), keyword))
            start = pos + 1
    
    # Sort by position
    positions.sort(key=lambda x: x[0])
    return positions


def extract_snippet(text: str, position: int, words_before: int, words_after: int) -> str:
    """
    Extract a snippet of text around a specific position.
    
    Args:
        text: The full text
        position: The position to center the snippet around
        words_before: Number of words to include before the position
        words_after: Number of words to include after the position
    
    Returns:
        The extracted snippet
    """
    words = text.split()
    
    # Find which word index contains the position
    char_count = 0
    center_word_idx = 0
    
    for i, word in enumerate(words):
        char_count += len(word) + 1  # +1 for space
        if char_count >= position:
            center_word_idx = i
            break
    
    # Calculate start and end word indices
    start_idx = max(0, center_word_idx - words_before)
    end_idx = min(len(words), center_word_idx + words_after + 1)
    
    # Extract snippet
    snippet_words = words[start_idx:end_idx]
    snippet = ' '.join(snippet_words)
    
    # Add ellipsis if truncated
    if start_idx > 0:
        snippet = '... ' + snippet
    if end_idx < len(words):
        snippet = snippet + ' ...'
    
    return snippet


def merge_overlapping_ranges(ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Merge overlapping or adjacent snippet ranges.
    
    Args:
        ranges: List of (start, end) tuples
    
    Returns:
        List of merged (start, end) tuples
    """
    if not ranges:
        return []
    
    # Sort by start position
    ranges = sorted(ranges)
    merged = [ranges[0]]
    
    for current in ranges[1:]:
        last = merged[-1]
        # If current overlaps with last, merge them
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    
    return merged


def extract_keyword_snippets(
    judgment_text: str,
    keyword_set: str,
    words_before: int =250,
    words_after: int = 250,
    max_snippets: int = 10
) -> str:
    """
    Extract snippets from judgment text where keywords are present.
    
    Args:
        judgment_text: The full judgment text
        keyword_set: The search query with keywords (e.g., '"environmental matters" subsidiary')
        words_before: Number of words to include before each keyword match (default: 500)
        words_after: Number of words to include after each keyword match (default: 500)
        max_snippets: Maximum number of snippets to extract (default: 10)
    
    Returns:
        Concatenated snippets separated by markers
    """
    keywords = parse_keywords(keyword_set)


    body = judgment_text
    
    positions = find_keyword_positions(body, keywords)
    
    if not positions:
        return body  # No keywords found, return full text
    
    words = body.split()
    total_words = len(words)
    
    # Pre-calculate word positions (start character index for each word)
    word_positions = []
    char_pos = 0
    for word in words:
        word_positions.append(char_pos)
        char_pos += len(word) + 1  # +1 for space
    
    # Select non-overlapping snippet ranges based on word indices
    selected_word_ranges = []
    used_word_ranges = []
    
    for pos, _, keyword in positions:
        if len(selected_word_ranges) >= max_snippets:
            break
        
        # Find which word contains this character position
        center_word_idx = 0
        for i, word_start in enumerate(word_positions):
            if word_start > pos:
                center_word_idx = max(0, i - 1)
                break
            center_word_idx = i
        
        # Calculate word range for this snippet
        start_word_idx = max(0, center_word_idx - words_before)
        end_word_idx = min(total_words, center_word_idx + words_after + 1)
        
        # Check if this overlaps with any already selected range
        overlaps = False
        for used_start, used_end in used_word_ranges:
            # Check for overlap
            if start_word_idx < used_end and end_word_idx > used_start:
                overlaps = True
                break
        
        # Only add if it doesn't overlap
        if not overlaps:
            selected_word_ranges.append((start_word_idx, end_word_idx))
            used_word_ranges.append((start_word_idx, end_word_idx))
    
    # Extract snippets using word ranges, preserving original text structure
    snippets = []
    for i, (start_word_idx, end_word_idx) in enumerate(selected_word_ranges, 1):
        # Get character positions for the word range
        start_char = word_positions[start_word_idx]
        if end_word_idx < total_words:
            # End at the start of the next word
            end_char = word_positions[end_word_idx]
        else:
            # End at the end of text
            end_char = len(body)
        
        # Extract text using character positions to preserve formatting
        snippet = body[start_char:end_char].strip()
        
        # Add ellipsis if truncated
        if start_word_idx > 0:
            snippet = '... ' + snippet
        if end_word_idx < total_words:
            snippet = snippet + ' ...'
        
        snippets.append(f"[SNIPPET {i}]\n{snippet}")
    
    # Return concatenated snippets
    if not snippets:
        return body  # Return full text if no snippets extracted
    
    result = "\n\n".join(snippets)
    
    return result


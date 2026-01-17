"""Helper functions for displaying search results."""

import re
from typing import List, Dict, Any


def extract_relevant_lines(code: str, query: str, max_lines: int = 5) -> List[str]:
    """Extract the most relevant lines from code based on query.
    
    Args:
        code: Full code content
        query: Search query
        max_lines: Maximum number of lines to return
        
    Returns:
        List of relevant code lines
    """
    lines = code.split('\n')
    
    # Extract keywords from query
    keywords = [word.lower() for word in re.findall(r'\w+', query)]
    
    # Score each line based on keyword matches
    scored_lines = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
            
        line_lower = line.lower()
        score = 0
        
        # Count keyword matches
        for keyword in keywords:
            if keyword in line_lower:
                score += 10
        
        # Bonus for function/class definitions
        if any(pattern in line for pattern in ['def ', 'class ', 'function ', 'public ', 'private ']):
            score += 5
            
        # Bonus for comments/docstrings
        if any(pattern in line for pattern in ['"""', "'''", '//', '/*', '*']):
            score += 2
            
        scored_lines.append((score, i, line))
    
    # Sort by score (descending) and line number (ascending for ties)
    scored_lines.sort(key=lambda x: (-x[0], x[1]))
    
    # Get top lines
    top_lines = scored_lines[:max_lines]
    
    # Sort by line number for display
    top_lines.sort(key=lambda x: x[1])
    
    # Return just the line content
    return [line for _, _, line in top_lines]


def format_code_preview(code: str, query: str, max_lines: int = 5) -> str:
    """Format code preview with relevant lines highlighted.
    
    Args:
        code: Full code content
        query: Search query
        max_lines: Maximum lines to show
        
    Returns:
        Formatted code preview string
    """
    relevant_lines = extract_relevant_lines(code, query, max_lines)
    
    if not relevant_lines:
        # Fallback to first few lines
        lines = [l for l in code.split('\n')[:max_lines] if l.strip()]
        return '\n'.join(f"      {line[:75]}" for line in lines)
    
    # Format with line content
    formatted = []
    for line in relevant_lines:
        # Limit line length
        display_line = line[:75] + "..." if len(line) > 75 else line
        formatted.append(f"      {display_line}")
    
    return '\n'.join(formatted)

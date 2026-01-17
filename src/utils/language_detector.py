"""Automatic programming language detection from code snippets."""

import re
from typing import Optional


class LanguageDetector:
    """Detect programming language from code content."""
    
    @staticmethod
    def detect(code: str) -> Optional[str]:
        """Detect programming language from code.
        
        Args:
            code: Source code snippet
            
        Returns:
            Detected language: 'python', 'javascript', 'java', 'go', or None
        """
        code = code.strip()
        
        if not code:
            return None
        
        # Score each language
        scores = {
            'python': LanguageDetector._score_python(code),
            'javascript': LanguageDetector._score_javascript(code),
            'java': LanguageDetector._score_java(code),
            'go': LanguageDetector._score_go(code)
        }
        
        # Get language with highest score
        max_score = max(scores.values())
        
        if max_score == 0:
            return None
        
        for lang, score in scores.items():
            if score == max_score:
                return lang
        
        return None
    
    @staticmethod
    def _score_python(code: str) -> int:
        """Score likelihood of Python code."""
        score = 0
        
        # Python-specific keywords
        if re.search(r'\bdef\s+\w+\s*\(', code):
            score += 10
        if re.search(r'\bclass\s+\w+', code):
            score += 10
        if re.search(r'\bimport\s+\w+', code):
            score += 5
        if re.search(r'\bfrom\s+\w+\s+import', code):
            score += 5
        if re.search(r':\s*$', code, re.MULTILINE):  # Colon at end of line
            score += 3
        if 'self' in code:
            score += 3
        if re.search(r'""".*?"""', code, re.DOTALL):  # Docstrings
            score += 5
        if re.search(r"'''.*?'''", code, re.DOTALL):
            score += 5
        
        # Python indentation (no braces)
        if '{' not in code and '}' not in code:
            score += 2
        
        return score
    
    @staticmethod
    def _score_javascript(code: str) -> int:
        """Score likelihood of JavaScript/TypeScript code."""
        score = 0
        
        # JavaScript-specific keywords
        if re.search(r'\bfunction\s+\w+\s*\(', code):
            score += 10
        if re.search(r'\bconst\s+\w+', code):
            score += 8
        if re.search(r'\blet\s+\w+', code):
            score += 8
        if re.search(r'\bvar\s+\w+', code):
            score += 5
        if '=>' in code:  # Arrow functions
            score += 10
        if re.search(r'\bconsole\.log\(', code):
            score += 5
        if re.search(r'\basync\s+function', code):
            score += 5
        if re.search(r'\bawait\s+', code):
            score += 3
        
        # Braces
        if '{' in code and '}' in code:
            score += 2
        
        # Semicolons
        if ';' in code:
            score += 2
        
        return score
    
    @staticmethod
    def _score_java(code: str) -> int:
        """Score likelihood of Java code."""
        score = 0
        
        # Java-specific keywords
        if re.search(r'\bpublic\s+class\s+\w+', code):
            score += 15
        if re.search(r'\bprivate\s+\w+', code):
            score += 5
        if re.search(r'\bprotected\s+\w+', code):
            score += 5
        if re.search(r'\bpublic\s+static\s+void\s+main', code):
            score += 15
        if re.search(r'\bSystem\.out\.println\(', code):
            score += 10
        if re.search(r'\bextends\s+\w+', code):
            score += 5
        if re.search(r'\bimplements\s+\w+', code):
            score += 5
        if re.search(r'\bnew\s+\w+\(', code):
            score += 3
        
        # Type declarations
        if re.search(r'\b(String|int|boolean|void|double|float)\s+\w+', code):
            score += 5
        
        # Braces and semicolons
        if '{' in code and '}' in code and ';' in code:
            score += 2
        
        return score
    
    @staticmethod
    def _score_go(code: str) -> int:
        """Score likelihood of Go code."""
        score = 0
        
        # Go-specific keywords
        if re.search(r'\bfunc\s+\w+\s*\(', code):
            score += 15
        if re.search(r'\bpackage\s+\w+', code):
            score += 10
        if re.search(r'\btype\s+\w+\s+struct', code):
            score += 10
        if ':=' in code:  # Short variable declaration
            score += 10
        if re.search(r'\bfmt\.Print', code):
            score += 5
        if re.search(r'\bfunc\s+\(\w+\s+\*?\w+\)', code):  # Method receivers
            score += 8
        if re.search(r'\bdefer\s+', code):
            score += 5
        if re.search(r'\bgo\s+\w+\(', code):  # Goroutines
            score += 5
        
        # Braces
        if '{' in code and '}' in code:
            score += 2
        
        return score

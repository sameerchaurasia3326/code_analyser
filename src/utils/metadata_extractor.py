"""Metadata extraction utilities for code analysis."""

import re
import ast
from typing import List, Dict, Any, Optional


class MetadataExtractor:
    """Extract rich metadata from code."""
    
    @staticmethod
    def extract_python_imports(code: str) -> List[str]:
        """Extract import statements from Python code."""
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            pass
        return list(set(imports))
    
    @staticmethod
    def extract_javascript_imports(code: str) -> List[str]:
        """Extract import/require statements from JavaScript."""
        imports = []
        
        # require('module')
        for match in re.finditer(r'require\(["\']([^"\']+)["\']\)', code):
            imports.append(match.group(1))
        
        # import ... from 'module'
        for match in re.finditer(r'import\s+.*?from\s+["\']([^"\']+)["\']', code):
            imports.append(match.group(1))
        
        # import 'module'
        for match in re.finditer(r'import\s+["\']([^"\']+)["\']', code):
            imports.append(match.group(1))
        
        return list(set(imports))
    
    @staticmethod
    def extract_java_imports(code: str) -> List[str]:
        """Extract import statements from Java."""
        imports = []
        for match in re.finditer(r'import\s+([\w.]+);', code):
            imports.append(match.group(1))
        return list(set(imports))
    
    @staticmethod
    def extract_go_imports(code: str) -> List[str]:
        """Extract import statements from Go."""
        imports = []
        
        # Single import
        for match in re.finditer(r'import\s+"([^"]+)"', code):
            imports.append(match.group(1))
        
        # Multi-line import
        import_block = re.search(r'import\s*\((.*?)\)', code, re.DOTALL)
        if import_block:
            for match in re.finditer(r'"([^"]+)"', import_block.group(1)):
                imports.append(match.group(1))
        
        return list(set(imports))
    
    @staticmethod
    def calculate_complexity(code: str) -> int:
        """Calculate cyclomatic complexity (simplified).
        
        Counts decision points: if, for, while, case, catch, &&, ||
        """
        complexity = 1  # Base complexity
        
        # Count decision keywords
        keywords = ['if', 'for', 'while', 'case', 'catch', 'except', '&&', '||', 'and', 'or']
        for keyword in keywords:
            complexity += code.lower().count(keyword)
        
        return min(complexity, 50)  # Cap at 50
    
    @staticmethod
    def extract_parameters(signature: str, language: str) -> List[str]:
        """Extract parameter names from function signature."""
        if not signature:
            return []
        
        params = []
        
        # Extract content between parentheses
        match = re.search(r'\(([^)]*)\)', signature)
        if not match:
            return []
        
        params_str = match.group(1).strip()
        if not params_str:
            return []
        
        # Split by comma
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue
            
            # Extract just the parameter name
            if language == 'python':
                # Handle: name, name: type, name = default
                param = param.split(':')[0].split('=')[0].strip()
            elif language in ['javascript', 'typescript']:
                # Handle: name, name: type, name = default
                param = param.split(':')[0].split('=')[0].strip()
            elif language == 'java':
                # Handle: Type name
                parts = param.split()
                param = parts[-1] if parts else param
            elif language == 'go':
                # Handle: name Type
                parts = param.split()
                param = parts[0] if parts else param
            
            if param and param not in ['self', 'this', 'cls']:
                params.append(param)
        
        return params
    
    @staticmethod
    def has_docstring(code: str, language: str) -> bool:
        """Check if code has documentation."""
        if language == 'python':
            return '"""' in code or "'''" in code
        elif language in ['javascript', 'typescript']:
            return '/**' in code or '//' in code
        elif language == 'java':
            return '/**' in code or '//' in code
        elif language == 'go':
            return '//' in code or '/*' in code
        return False
    
    @staticmethod
    def extract_class_name(file_content: str, method_line: int, language: str) -> Optional[str]:
        """Extract the class name that contains a method."""
        lines = file_content.split('\n')
        
        # Search backwards from method line
        for i in range(method_line - 1, max(0, method_line - 50), -1):
            line = lines[i].strip()
            
            if language == 'python':
                match = re.match(r'class\s+(\w+)', line)
                if match:
                    return match.group(1)
            elif language in ['javascript', 'typescript']:
                match = re.match(r'class\s+(\w+)', line)
                if match:
                    return match.group(1)
            elif language == 'java':
                match = re.match(r'(?:public|private|protected)?\s*class\s+(\w+)', line)
                if match:
                    return match.group(1)
        
        return None

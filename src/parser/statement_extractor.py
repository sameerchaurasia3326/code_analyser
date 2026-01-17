"""Statement-level code extraction for precise line-level search."""

import ast
import re
from typing import List, Dict, Any
from src.models.code_unit import CodeUnit, CodeUnitType
from src.utils.logger import setup_logger

logger = setup_logger("statement_extractor")


class StatementExtractor:
    """Extract individual statements from code for fine-grained search."""
    
    @staticmethod
    def extract_python_statements(code: str, file_path: str, parent_name: str = None) -> List[CodeUnit]:
        """Extract statements from Python code.
        
        Args:
            code: Python source code
            file_path: Path to source file
            parent_name: Name of parent function/class
            
        Returns:
            List of statement-level code units
        """
        statements = []
        
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
            
            for node in ast.walk(tree):
                # Extract interesting statements
                statement_info = StatementExtractor._analyze_node(node, lines)
                
                if statement_info:
                    stmt_type, description, start_line, end_line = statement_info
                    
                    # Get the actual code
                    stmt_code = '\n'.join(lines[start_line-1:end_line])
                    
                    statements.append(CodeUnit(
                        type=CodeUnitType.STATEMENT,
                        name=f"{stmt_type}: {description}",
                        content=stmt_code,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        language='python',
                        signature=description,
                        metadata={
                            'statement_type': stmt_type,
                            'parent': parent_name,
                            'description': description
                        }
                    ))
        
        except Exception as e:
            logger.error(f"Error extracting statements: {e}")
        
        return statements
    
    @staticmethod
    def _analyze_node(node: ast.AST, lines: List[str]) -> tuple:
        """Analyze AST node and extract statement info.
        
        Returns:
            (type, description, start_line, end_line) or None
        """
        # For loops
        if isinstance(node, ast.For):
            target = ast.unparse(node.target) if hasattr(ast, 'unparse') else 'item'
            iter_expr = ast.unparse(node.iter) if hasattr(ast, 'unparse') else 'iterable'
            return ('loop', f'for {target} in {iter_expr}', node.lineno, node.end_lineno or node.lineno)
        
        # While loops
        elif isinstance(node, ast.While):
            condition = ast.unparse(node.test) if hasattr(ast, 'unparse') else 'condition'
            return ('loop', f'while {condition}', node.lineno, node.end_lineno or node.lineno)
        
        # If statements
        elif isinstance(node, ast.If):
            condition = ast.unparse(node.test) if hasattr(ast, 'unparse') else 'condition'
            return ('conditional', f'if {condition}', node.lineno, node.lineno)
        
        # Assignments (especially interesting ones)
        elif isinstance(node, ast.Assign):
            # Get target and value
            if hasattr(ast, 'unparse'):
                targets = ', '.join(ast.unparse(t) for t in node.targets)
                value = ast.unparse(node.value)
                
                # Check for tuple unpacking (like a, b = b, a+b)
                if isinstance(node.value, ast.Tuple) and isinstance(node.targets[0], ast.Tuple):
                    return ('assignment', f'{targets} = {value}', node.lineno, node.lineno)
                
                # Check for list/dict operations
                if any(keyword in value.lower() for keyword in ['append', 'extend', 'update', 'pop']):
                    return ('operation', f'{targets} = {value}', node.lineno, node.lineno)
        
        # Return statements
        elif isinstance(node, ast.Return):
            if node.value and hasattr(ast, 'unparse'):
                value = ast.unparse(node.value)
                return ('return', f'return {value}', node.lineno, node.lineno)
        
        # Function calls (important ones)
        elif isinstance(node, ast.Call):
            if hasattr(ast, 'unparse'):
                call_str = ast.unparse(node)
                # Only track certain function calls
                if any(keyword in call_str.lower() for keyword in ['print', 'log', 'raise', 'assert']):
                    return ('call', call_str, node.lineno, node.lineno)
        
        return None
    
    @staticmethod
    def extract_javascript_statements(code: str, file_path: str, parent_name: str = None) -> List[CodeUnit]:
        """Extract statements from JavaScript code using regex.
        
        Args:
            code: JavaScript source code
            file_path: Path to source file
            parent_name: Name of parent function
            
        Returns:
            List of statement-level code units
        """
        statements = []
        lines = code.split('\n')
        
        # Pattern for variable swapping: [a, b] = [b, a+b]
        swap_pattern = r'\[([^\]]+)\]\s*=\s*\[([^\]]+)\]'
        
        # Pattern for loops
        for_pattern = r'for\s*\(([^)]+)\)'
        while_pattern = r'while\s*\(([^)]+)\)'
        
        # Pattern for conditionals
        if_pattern = r'if\s*\(([^)]+)\)'
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Destructuring assignment / swap
            if match := re.search(swap_pattern, line):
                statements.append(CodeUnit(
                    type=CodeUnitType.STATEMENT,
                    name=f"assignment: {match.group(0)}",
                    content=line_stripped,
                    file_path=file_path,
                    start_line=i,
                    end_line=i,
                    language='javascript',
                    signature=match.group(0),
                    metadata={
                        'statement_type': 'assignment',
                        'parent': parent_name,
                        'description': f'swap values: {match.group(1)}'
                    }
                ))
            
            # For loops
            elif match := re.search(for_pattern, line):
                statements.append(CodeUnit(
                    type=CodeUnitType.STATEMENT,
                    name=f"loop: for {match.group(1)}",
                    content=line_stripped,
                    file_path=file_path,
                    start_line=i,
                    end_line=i,
                    language='javascript',
                    signature=f"for ({match.group(1)})",
                    metadata={
                        'statement_type': 'loop',
                        'parent': parent_name
                    }
                ))
            
            # While loops
            elif match := re.search(while_pattern, line):
                statements.append(CodeUnit(
                    type=CodeUnitType.STATEMENT,
                    name=f"loop: while {match.group(1)}",
                    content=line_stripped,
                    file_path=file_path,
                    start_line=i,
                    end_line=i,
                    language='javascript',
                    signature=f"while ({match.group(1)})",
                    metadata={
                        'statement_type': 'loop',
                        'parent': parent_name
                    }
                ))
            
            # If statements
            elif match := re.search(if_pattern, line):
                statements.append(CodeUnit(
                    type=CodeUnitType.STATEMENT,
                    name=f"conditional: if {match.group(1)}",
                    content=line_stripped,
                    file_path=file_path,
                    start_line=i,
                    end_line=i,
                    language='javascript',
                    signature=f"if ({match.group(1)})",
                    metadata={
                        'statement_type': 'conditional',
                        'parent': parent_name
                    }
                ))
        
        return statements
    
    @staticmethod
    def extract_java_statements(code: str, file_path: str, parent_name: str = None) -> List[CodeUnit]:
        """Extract statements from Java code."""
        statements = []
        lines = code.split('\n')
        
        for_pattern = r'for\s*\(([^)]+)\)'
        while_pattern = r'while\s*\(([^)]+)\)'
        if_pattern = r'if\s*\(([^)]+)\)'
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            if match := re.search(for_pattern, line):
                statements.append(CodeUnit(
                    type=CodeUnitType.STATEMENT,
                    name=f"loop: for {match.group(1)}",
                    content=line_stripped,
                    file_path=file_path,
                    start_line=i,
                    end_line=i,
                    language='java',
                    signature=f"for ({match.group(1)})",
                    metadata={'statement_type': 'loop', 'parent': parent_name}
                ))
        
        return statements
    
    @staticmethod
    def extract_go_statements(code: str, file_path: str, parent_name: str = None) -> List[CodeUnit]:
        """Extract statements from Go code."""
        statements = []
        lines = code.split('\n')
        
        for_pattern = r'for\s+([^{]+)\s*\{'
        if_pattern = r'if\s+([^{]+)\s*\{'
        var_pattern = r'(\w+)\s*:=\s*([^/\n]+)'
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            if match := re.search(for_pattern, line):
                statements.append(CodeUnit(
                    type=CodeUnitType.STATEMENT,
                    name=f"loop: for {match.group(1).strip()}",
                    content=line_stripped,
                    file_path=file_path,
                    start_line=i,
                    end_line=i,
                    language='go',
                    signature=f"for {match.group(1).strip()}",
                    metadata={'statement_type': 'loop', 'parent': parent_name}
                ))
        
        return statements

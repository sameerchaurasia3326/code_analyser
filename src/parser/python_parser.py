"""Python code parser using AST."""

import ast
from typing import List
from pathlib import Path

from src.models.code_unit import CodeUnit, CodeUnitType
from src.parser.base_parser import BaseParser
from src.utils.logger import setup_logger

logger = setup_logger("parser.python")


class PythonParser(BaseParser):
    """Parser for Python source code files."""

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.py', '.pyw']

    def parse_file(self, file_path: str) -> List[CodeUnit]:
        """Parse a Python file and extract code units.

        Args:
            file_path: Path to the Python file

        Returns:
            List of extracted code units
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            tree = ast.parse(source_code)
            code_units = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    code_units.append(self._extract_function(node, file_path, source_code))
                elif isinstance(node, ast.ClassDef):
                    code_units.append(self._extract_class(node, file_path, source_code))

            # Extract statements if enabled
            from src.config import settings
            if settings.enable_statement_chunking:
                from src.parser.statement_extractor import StatementExtractor
                statements = StatementExtractor.extract_python_statements(
                    source_code, file_path
                )
                code_units.extend(statements[:settings.max_statements_per_function])
            
            # Detect concepts for all code units
            from src.models.code_concepts import ConceptDetector
            from src.utils.metadata_extractor import MetadataExtractor
            
            # Extract file-level imports
            file_imports = MetadataExtractor.extract_python_imports(source_code)
            
            for unit in code_units:
                concepts = ConceptDetector.detect_concepts(unit.content, 'python')
                if concepts:
                    if unit.metadata is None:
                        unit.metadata = {}
                    unit.metadata['concepts'] = ','.join([c.value for c in concepts])
                
                # Add rich metadata
                if unit.metadata is None:
                    unit.metadata = {}
                
                unit.metadata['imports'] = ','.join(file_imports[:10])  # Limit to 10
                unit.metadata['complexity'] = MetadataExtractor.calculate_complexity(unit.content)
                unit.metadata['has_docs'] = MetadataExtractor.has_docstring(unit.content, 'python')
                unit.metadata['param_count'] = len(MetadataExtractor.extract_parameters(unit.signature or '', 'python'))

            logger.info(f"Parsed {len(code_units)} code units from {file_path}")
            return code_units

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return []

    def _extract_function(
        self, node: ast.FunctionDef, file_path: str, source_code: str
    ) -> CodeUnit:
        """Extract function as a code unit.

        Args:
            node: AST function node
            file_path: Path to source file
            source_code: Full source code

        Returns:
            CodeUnit representing the function
        """
        # Get function source code
        lines = source_code.split("\n")
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        content = "\n".join(lines[start_line - 1 : end_line])

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Build signature
        args = [arg.arg for arg in node.args.args]
        signature = f"def {node.name}({', '.join(args)})"

        # Determine if it's a method (inside a class)
        unit_type = CodeUnitType.METHOD if self._is_method(node) else CodeUnitType.FUNCTION

        return CodeUnit(
            type=unit_type,
            name=node.name,
            content=content,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            language="python",
            docstring=docstring,
            signature=signature,
            metadata={"args": args, "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]},
        )

    def _extract_class(self, node: ast.ClassDef, file_path: str, source_code: str) -> CodeUnit:
        """Extract class as a code unit.

        Args:
            node: AST class node
            file_path: Path to source file
            source_code: Full source code

        Returns:
            CodeUnit representing the class
        """
        # Get class source code
        lines = source_code.split("\n")
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        content = "\n".join(lines[start_line - 1 : end_line])

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Get base classes
        bases = [base.id for base in node.bases if isinstance(base, ast.Name)]

        # Get method names
        methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]

        return CodeUnit(
            type=CodeUnitType.CLASS,
            name=node.name,
            content=content,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            language="python",
            docstring=docstring,
            signature=f"class {node.name}",
            metadata={"bases": bases, "methods": methods},
        )

    def _is_method(self, node: ast.FunctionDef) -> bool:
        """Check if a function node is a method (inside a class).

        Args:
            node: AST function node

        Returns:
            True if the function is a method
        """
        # Check if the function has 'self' or 'cls' as first argument
        if node.args.args:
            first_arg = node.args.args[0].arg
            return first_arg in ("self", "cls")
        return False

"""Go parser using regex patterns."""

import re
from typing import List

from src.models.code_unit import CodeUnit, CodeUnitType
from src.parser.base_parser import BaseParser
from src.utils.logger import setup_logger

logger = setup_logger("parser.go")


class GoParser(BaseParser):
    """Parser for Go files."""

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.go']

    def parse_file(self, file_path: str) -> List[CodeUnit]:
        """Parse a Go file.

        Args:
            file_path: Path to the file

        Returns:
            List of code units
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            code_units = []
            lines = content.split('\n')

            # Extract functions
            code_units.extend(self._extract_functions(content, lines, file_path))

            # Extract structs (Go's version of classes)
            code_units.extend(self._extract_structs(content, lines, file_path))
            
            # Detect concepts for all code units
            from src.models.code_concepts import ConceptDetector
            for unit in code_units:
                concepts = ConceptDetector.detect_concepts(unit.content, 'go')
                if concepts:
                    if unit.metadata is None:
                        unit.metadata = {}
                    unit.metadata['concepts'] = ','.join([c.value for c in concepts])

            logger.info(f"Parsed {len(code_units)} code units from {file_path}")
            return code_units

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return []

    def _extract_functions(self, content: str, lines: List[str], file_path: str) -> List[CodeUnit]:
        """Extract function declarations."""
        code_units = []

        # Pattern for function declarations: func name(...) ... { ... }
        # Also handles methods: func (receiver Type) name(...) ... { ... }
        func_pattern = r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(([^)]*)\)(?:\s*\([^)]*\)|\s+\w+)?\s*\{'

        for match in re.finditer(func_pattern, content):
            name = match.group(1)
            params = match.group(2).strip()
            start_pos = match.start()

            start_line = content[:start_pos].count('\n') + 1
            end_line = self._find_closing_brace(lines, start_line - 1)

            func_content = '\n'.join(lines[start_line - 1:end_line])
            docstring = self._extract_godoc(lines, start_line - 1)

            code_units.append(CodeUnit(
                type=CodeUnitType.FUNCTION,
                name=name,
                content=func_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language='go',
                docstring=docstring,
                signature=f"func {name}({params})",
                metadata={'params': params}
            ))

        return code_units

    def _extract_structs(self, content: str, lines: List[str], file_path: str) -> List[CodeUnit]:
        """Extract struct declarations."""
        code_units = []

        # Pattern for struct declarations
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{'

        for match in re.finditer(struct_pattern, content):
            name = match.group(1)
            start_pos = match.start()

            start_line = content[:start_pos].count('\n') + 1
            end_line = self._find_closing_brace(lines, start_line - 1)

            struct_content = '\n'.join(lines[start_line - 1:end_line])
            docstring = self._extract_godoc(lines, start_line - 1)

            code_units.append(CodeUnit(
                type=CodeUnitType.CLASS,  # Using CLASS type for structs
                name=name,
                content=struct_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language='go',
                docstring=docstring,
                signature=f"type {name} struct",
                metadata={}
            ))

        return code_units

    def _find_closing_brace(self, lines: List[str], start_line: int) -> int:
        """Find the closing brace for a code block."""
        brace_count = 0
        in_block = False

        for i in range(start_line, len(lines)):
            line = lines[i]
            for char in line:
                if char == '{':
                    brace_count += 1
                    in_block = True
                elif char == '}':
                    brace_count -= 1
                    if in_block and brace_count == 0:
                        return i + 1

        return len(lines)

    def _extract_godoc(self, lines: List[str], func_line: int) -> str:
        """Extract GoDoc comment before a function/struct."""
        if func_line == 0:
            return None

        doc_lines = []
        for i in range(func_line - 1, max(func_line - 20, -1), -1):
            line = lines[i].strip()
            if line.startswith('//'):
                doc_lines.insert(0, line[2:].strip())
            elif not line:
                continue
            else:
                break

        return '\n'.join(doc_lines) if doc_lines else None

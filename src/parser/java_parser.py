"""Java parser using regex patterns."""

import re
from typing import List

from src.models.code_unit import CodeUnit, CodeUnitType
from src.parser.base_parser import BaseParser
from src.utils.logger import setup_logger

logger = setup_logger("parser.java")


class JavaParser(BaseParser):
    """Parser for Java files."""

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.java']

    def parse_file(self, file_path: str) -> List[CodeUnit]:
        """Parse a Java file.

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

            # Extract classes
            code_units.extend(self._extract_classes(content, lines, file_path))

            # Extract methods
            code_units.extend(self._extract_methods(content, lines, file_path))
            
            # Detect concepts for all code units
            from src.models.code_concepts import ConceptDetector
            for unit in code_units:
                concepts = ConceptDetector.detect_concepts(unit.content, 'java')
                if concepts:
                    if unit.metadata is None:
                        unit.metadata = {}
                    unit.metadata['concepts'] = ','.join([c.value for c in concepts])

            logger.info(f"Parsed {len(code_units)} code units from {file_path}")
            return code_units

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return []

    def _extract_classes(self, content: str, lines: List[str], file_path: str) -> List[CodeUnit]:
        """Extract class declarations."""
        code_units = []

        # Pattern for class declarations
        class_pattern = r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*\{'

        for match in re.finditer(class_pattern, content):
            name = match.group(1)
            extends = match.group(2)
            implements = match.group(3)
            start_pos = match.start()

            start_line = content[:start_pos].count('\n') + 1
            end_line = self._find_closing_brace(lines, start_line - 1)

            class_content = '\n'.join(lines[start_line - 1:end_line])
            docstring = self._extract_javadoc(lines, start_line - 1)

            code_units.append(CodeUnit(
                type=CodeUnitType.CLASS,
                name=name,
                content=class_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language='java',
                docstring=docstring,
                signature=f"class {name}",
                metadata={'extends': extends, 'implements': implements}
            ))

        return code_units

    def _extract_methods(self, content: str, lines: List[str], file_path: str) -> List[CodeUnit]:
        """Extract method declarations."""
        code_units = []

        # Pattern for method declarations
        method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[^{]+)?\s*\{'

        for match in re.finditer(method_pattern, content):
            name = match.group(1)
            params = match.group(2).strip()
            start_pos = match.start()

            # Skip constructors and common keywords
            if name in ['if', 'while', 'for', 'switch', 'catch']:
                continue

            start_line = content[:start_pos].count('\n') + 1
            end_line = self._find_closing_brace(lines, start_line - 1)

            method_content = '\n'.join(lines[start_line - 1:end_line])
            docstring = self._extract_javadoc(lines, start_line - 1)

            code_units.append(CodeUnit(
                type=CodeUnitType.METHOD,
                name=name,
                content=method_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language='java',
                docstring=docstring,
                signature=f"{name}({params})",
                metadata={'params': params}
            ))

        return code_units

    def _find_closing_brace(self, lines: List[str], start_line: int) -> int:
        """Find the closing brace for a code block."""
        brace_count = 0
        in_block = False

        for i in range(start_line, len(lines)):
            line = lines[i]
            # Skip string literals
            in_string = False
            for char in line:
                if char == '"' and (i == 0 or line[i-1] != '\\'):
                    in_string = not in_string
                if not in_string:
                    if char == '{':
                        brace_count += 1
                        in_block = True
                    elif char == '}':
                        brace_count -= 1
                        if in_block and brace_count == 0:
                            return i + 1

        return len(lines)

    def _extract_javadoc(self, lines: List[str], func_line: int) -> str:
        """Extract Javadoc comment before a method/class."""
        if func_line == 0:
            return None

        doc_lines = []
        for i in range(func_line - 1, max(func_line - 30, -1), -1):
            line = lines[i].strip()
            if line.startswith('*/'):
                doc_lines.insert(0, line)
                for j in range(i - 1, max(func_line - 30, -1), -1):
                    doc_line = lines[j].strip()
                    doc_lines.insert(0, doc_line)
                    if doc_line.startswith('/**'):
                        return '\n'.join(doc_lines)
                break
            elif not line or line.startswith('//') or line.startswith('@'):
                continue
            else:
                break

        return None

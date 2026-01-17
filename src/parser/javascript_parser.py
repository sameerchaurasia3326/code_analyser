"""JavaScript/TypeScript parser using regex patterns."""

import re
from typing import List
from pathlib import Path

from src.models.code_unit import CodeUnit, CodeUnitType
from src.parser.base_parser import BaseParser
from src.utils.logger import setup_logger

logger = setup_logger("parser.javascript")


class JavaScriptParser(BaseParser):
    """Parser for JavaScript and TypeScript files."""

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.js', '.jsx', '.ts', '.tsx', '.mjs']

    def parse_file(self, file_path: str) -> List[CodeUnit]:
        """Parse a JavaScript/TypeScript file.

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

            # Extract classes
            code_units.extend(self._extract_classes(content, lines, file_path))

            # Extract methods
            code_units.extend(self._extract_methods(content, lines, file_path))
            
            # Detect concepts for all code units
            from src.models.code_concepts import ConceptDetector
            from src.utils.metadata_extractor import MetadataExtractor
            
            # Extract file-level imports
            file_imports = MetadataExtractor.extract_javascript_imports(content)
            
            for unit in code_units:
                concepts = ConceptDetector.detect_concepts(unit.content, 'javascript')
                if concepts:
                    if unit.metadata is None:
                        unit.metadata = {}
                    unit.metadata['concepts'] = ','.join([c.value for c in concepts])
                
                # Add rich metadata
                if unit.metadata is None:
                    unit.metadata = {}
                
                unit.metadata['imports'] = ','.join(file_imports[:10])
                unit.metadata['complexity'] = MetadataExtractor.calculate_complexity(unit.content)
                unit.metadata['has_docs'] = MetadataExtractor.has_docstring(unit.content, 'javascript')
                unit.metadata['param_count'] = len(MetadataExtractor.extract_parameters(unit.signature or '', 'javascript'))

            logger.info(f"Parsed {len(code_units)} code units from {file_path}")
            return code_units

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return []

    def _extract_functions(self, content: str, lines: List[str], file_path: str) -> List[CodeUnit]:
        """Extract function declarations."""
        code_units = []

        # Pattern 1: function name(...) { ... }
        func_pattern = r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*\{'
        
        # Pattern 2: const/let/var name = (...) => { ... }
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>\s*[{\(]'
        
        # Pattern 3: const name = async (...) => ...
        arrow_async_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*async\s*\(([^)]*)\)\s*=>'

        for pattern in [func_pattern, arrow_pattern, arrow_async_pattern]:
            for match in re.finditer(pattern, content):
                name = match.group(1)
                params = match.group(2).strip() if match.group(2) else ''
                start_pos = match.start()

                # Find line number
                start_line = content[:start_pos].count('\n') + 1

                # Find end of function (simple brace matching)
                end_line = self._find_closing_brace(lines, start_line - 1)

                # Extract function body
                func_content = '\n'.join(lines[start_line - 1:end_line])

                # Extract JSDoc comment if present
                docstring = self._extract_jsdoc(lines, start_line - 1)

                code_units.append(CodeUnit(
                    type=CodeUnitType.FUNCTION,
                    name=name,
                    content=func_content,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    language='javascript',
                    docstring=docstring,
                    signature=f"function {name}({params})",
                    metadata={'params': params}
                ))

        return code_units
    
    def _extract_methods(self, content: str, lines: List[str], file_path: str) -> List[CodeUnit]:
        """Extract class methods."""
        code_units = []
        
        # Pattern for class methods: methodName(...) { ... }
        # Matches: async methodName(...), static methodName(...), methodName(...)
        method_pattern = r'(?:async\s+|static\s+)?(\w+)\s*\(([^)]*)\)\s*\{'
        
        # Only extract if inside a class (simple heuristic: check if preceded by class keyword)
        class_regions = []
        for match in re.finditer(r'class\s+\w+', content):
            class_start = match.start()
            class_regions.append(class_start)
        
        for match in re.finditer(method_pattern, content):
            name = match.group(1)
            params = match.group(2).strip() if match.group(2) else ''
            start_pos = match.start()
            
            # Skip if it's a known function keyword or constructor
            if name in ['function', 'if', 'for', 'while', 'switch', 'catch']:
                continue
            
            # Check if inside a class (rough check)
            in_class = any(start_pos > class_start for class_start in class_regions)
            if not in_class:
                continue
            
            # Find line number
            start_line = content[:start_pos].count('\n') + 1
            
            # Find end of method
            end_line = self._find_closing_brace(lines, start_line - 1)
            
            # Extract method body
            method_content = '\n'.join(lines[start_line - 1:end_line])
            
            # Extract JSDoc
            docstring = self._extract_jsdoc(lines, start_line - 1)
            
            code_units.append(CodeUnit(
                type=CodeUnitType.METHOD,
                name=name,
                content=method_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language='javascript',
                docstring=docstring,
                signature=f"{name}({params})",
                metadata={'params': params}
            ))
        
        return code_units

    def _extract_classes(self, content: str, lines: List[str], file_path: str) -> List[CodeUnit]:
        """Extract class declarations."""
        code_units = []

        # Pattern for class declarations
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'

        for match in re.finditer(class_pattern, content):
            name = match.group(1)
            extends = match.group(2) if match.group(2) else None
            start_pos = match.start()

            # Find line number
            start_line = content[:start_pos].count('\n') + 1

            # Find end of class
            end_line = self._find_closing_brace(lines, start_line - 1)

            # Extract class body
            class_content = '\n'.join(lines[start_line - 1:end_line])

            # Extract JSDoc comment
            docstring = self._extract_jsdoc(lines, start_line - 1)

            code_units.append(CodeUnit(
                type=CodeUnitType.CLASS,
                name=name,
                content=class_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language='javascript',
                docstring=docstring,
                signature=f"class {name}" + (f" extends {extends}" if extends else ""),
                metadata={'extends': extends}
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

    def _extract_jsdoc(self, lines: List[str], func_line: int) -> str:
        """Extract JSDoc comment before a function."""
        if func_line == 0:
            return None

        # Look backwards for JSDoc comment
        doc_lines = []
        for i in range(func_line - 1, max(func_line - 20, -1), -1):
            line = lines[i].strip()
            if line.startswith('*/'):
                doc_lines.insert(0, line)
                for j in range(i - 1, max(func_line - 20, -1), -1):
                    doc_line = lines[j].strip()
                    doc_lines.insert(0, doc_line)
                    if doc_line.startswith('/**'):
                        return '\n'.join(doc_lines)
                break
            elif not line or line.startswith('//'):
                continue
            else:
                break

        return None

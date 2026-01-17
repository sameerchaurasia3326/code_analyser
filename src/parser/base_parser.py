"""Base parser interface for all language parsers."""

from abc import ABC, abstractmethod
from typing import List
from src.models.code_unit import CodeUnit


class BaseParser(ABC):
    """Abstract base class for language-specific parsers."""

    @abstractmethod
    def parse_file(self, file_path: str) -> List[CodeUnit]:
        """Parse a source code file and extract code units.

        Args:
            file_path: Path to the source file

        Returns:
            List of extracted code units
        """
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get list of file extensions supported by this parser.

        Returns:
            List of file extensions (e.g., ['.py', '.pyw'])
        """
        pass

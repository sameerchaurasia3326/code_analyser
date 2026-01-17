"""Data models for code units."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CodeUnitType(str, Enum):
    """Type of code unit."""

    FUNCTION = "function"
    CLASS = "class"
    STATEMENT = "statement"  # New: for individual statements
    METHOD = "method"
    MODULE = "module"
    VARIABLE = "variable"


class CodeUnit(BaseModel):
    """Represents a semantic unit of code."""

    id: Optional[str] = Field(None, description="Unique identifier")
    type: CodeUnitType = Field(..., description="Type of code unit")
    name: str = Field(..., description="Name of the code unit")
    content: str = Field(..., description="Full source code content")
    file_path: str = Field(..., description="Path to the source file")
    start_line: int = Field(..., description="Starting line number")
    end_line: int = Field(..., description="Ending line number")
    language: str = Field(..., description="Programming language")
    docstring: Optional[str] = Field(None, description="Documentation string")
    signature: Optional[str] = Field(None, description="Function/method signature")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config."""

        use_enum_values = True

    def to_searchable_text(self) -> str:
        """Convert code unit to searchable text representation.

        Returns:
            Formatted text combining name, signature, docstring, and code
        """
        parts = [f"Name: {self.name}"]

        if self.signature:
            parts.append(f"Signature: {self.signature}")

        if self.docstring:
            parts.append(f"Documentation: {self.docstring}")

        parts.append(f"Code:\n{self.content}")

        return "\n\n".join(parts)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.type.upper()}: {self.name} ({self.file_path}:{self.start_line}-{self.end_line})"

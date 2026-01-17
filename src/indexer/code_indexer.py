"""Code indexer for processing codebases."""

from pathlib import Path
from typing import List, Dict, Any
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.parser.python_parser import PythonParser
from src.parser.javascript_parser import JavaScriptParser
from src.parser.java_parser import JavaParser
from src.parser.go_parser import GoParser
from src.embeddings.embedding_service import EmbeddingService
from src.embeddings.vector_store import VectorStore
from src.models.code_unit import CodeUnit
from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("indexer")


class CodeIndexer:
    """Main indexer for processing and indexing codebases."""

    def __init__(self):
        """Initialize the code indexer."""
        # Initialize all parsers
        self.parsers = {
            'python': PythonParser(),
            'javascript': JavaScriptParser(),
            'java': JavaParser(),
            'go': GoParser(),
        }

        # Build extension to parser mapping
        self.extension_map = {}
        for parser_name, parser in self.parsers.items():
            for ext in parser.get_supported_extensions():
                self.extension_map[ext] = parser

        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        logger.info(f"Initialized CodeIndexer with support for: {', '.join(self.parsers.keys())}")

    def index_directory(self, directory_path: str) -> Dict[str, Any]:
        """Index all supported code files in a directory.

        Args:
            directory_path: Path to directory to index

        Returns:
            Statistics about the indexing process
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")

        # Find all supported files
        supported_files = []
        for ext in self.extension_map.keys():
            supported_files.extend(list(directory.rglob(f"*{ext}")))

        logger.info(f"Found {len(supported_files)} supported files in {directory_path}")

        all_code_units = []

        # Parse files with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("[cyan]Parsing files...", total=len(supported_files))

            for file_path in supported_files:
                # Skip __pycache__, venv, node_modules directories
                path_str = str(file_path)
                if any(skip in path_str for skip in ["__pycache__", "venv", "node_modules", ".git"]):
                    progress.advance(task)
                    continue

                # Get appropriate parser based on file extension
                file_ext = file_path.suffix
                parser = self.extension_map.get(file_ext)

                if parser:
                    code_units = parser.parse_file(str(file_path))
                    all_code_units.extend(code_units)

                progress.advance(task)

        logger.info(f"Extracted {len(all_code_units)} code units")

        if not all_code_units:
            logger.warning("No code units found to index")
            return {"total_files": len(supported_files), "total_code_units": 0}

        # Generate embeddings
        logger.info("Generating embeddings...")
        texts = [cu.to_searchable_text() for cu in all_code_units]
        embeddings = self.embedding_service.generate_embeddings_batch(texts)

        # Store in vector database
        logger.info("Storing in vector database...")
        self.vector_store.add_code_units(all_code_units, embeddings)

        stats = {
            "total_files": len(supported_files),
            "total_code_units": len(all_code_units),
            "directory": directory_path,
        }

        logger.info(f"Indexing complete: {stats}")
        return stats

    def index_file(self, file_path: str) -> Dict[str, Any]:
        """Index a single code file.

        Args:
            file_path: Path to file to index

        Returns:
            Statistics about the indexing process
        """
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        # Get appropriate parser based on file extension
        file_ext = path.suffix
        parser = self.extension_map.get(file_ext)

        if not parser:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported: {list(self.extension_map.keys())}")

        # Parse file
        code_units = parser.parse_file(file_path)

        if not code_units:
            logger.warning(f"No code units found in {file_path}")
            return {"total_code_units": 0}

        # Generate embeddings
        texts = [cu.to_searchable_text() for cu in code_units]
        embeddings = self.embedding_service.generate_embeddings_batch(texts)

        # Store in vector database
        self.vector_store.add_code_units(code_units, embeddings)

        stats = {
            "file_path": file_path,
            "total_code_units": len(code_units),
        }

        logger.info(f"Indexed file: {stats}")
        return stats

    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics.

        Returns:
            Statistics dictionary
        """
        return self.vector_store.get_stats()

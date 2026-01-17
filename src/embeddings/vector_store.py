"""Vector store using ChromaDB."""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from src.models.code_unit import CodeUnit
from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("embeddings.vector_store")


class VectorStore:
    """ChromaDB-based vector store for code embeddings."""

    def __init__(self):
        """Initialize the vector store."""
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"description": "Code embeddings for semantic search"},
        )
        logger.info(f"Initialized ChromaDB collection: {settings.chroma_collection_name}")

    def add_code_units(
        self, code_units: List[CodeUnit], embeddings: List[List[float]]
    ) -> None:
        """Add code units with their embeddings to the vector store.

        Args:
            code_units: List of code units
            embeddings: Corresponding embedding vectors
        """
        if len(code_units) != len(embeddings):
            raise ValueError("Number of code units must match number of embeddings")

        # Generate unique IDs including name and type to avoid duplicates
        ids = [
            f"{cu.file_path}:{cu.type}:{cu.name}:{cu.start_line}-{cu.end_line}" 
            for cu in code_units
        ]
        documents = [cu.to_searchable_text() for cu in code_units]
        metadatas = [
            {
                "type": cu.type,
                "name": cu.name,
                "file_path": cu.file_path,
                "start_line": cu.start_line,
                "end_line": cu.end_line,
                "language": cu.language,
                "signature": cu.signature or "",
                "docstring": cu.docstring or "",
                # Convert concepts list to comma-separated string
                "concepts": cu.metadata.get("concepts", "") if cu.metadata else "",
                # Rich metadata
                "imports": cu.metadata.get("imports", "") if cu.metadata else "",
                "complexity": cu.metadata.get("complexity", 0) if cu.metadata else 0,
                "has_docs": cu.metadata.get("has_docs", False) if cu.metadata else False,
                "param_count": cu.metadata.get("param_count", 0) if cu.metadata else 0,
            }
            for cu in code_units
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(code_units)} code units to vector store")

    def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar code units.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            filter_dict: Optional metadata filters

        Returns:
            List of search results with metadata
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=filter_dict,
        )

        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append(
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None,
                    }
                )

        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results

    def delete_by_file(self, file_path: str) -> None:
        """Delete all code units from a specific file.

        Args:
            file_path: Path to the file
        """
        self.collection.delete(where={"file_path": file_path})
        logger.info(f"Deleted code units from {file_path}")

    def clear(self) -> None:
        """Clear all data from the collection."""
        self.client.delete_collection(settings.chroma_collection_name)
        self.collection = self.client.create_collection(
            name=settings.chroma_collection_name,
            metadata={"description": "Code embeddings for semantic search"},
        )
        logger.info("Cleared vector store")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.

        Returns:
            Dictionary with statistics
        """
        count = self.collection.count()
        return {
            "total_code_units": count,
            "collection_name": settings.chroma_collection_name,
            "persist_directory": settings.chroma_persist_directory,
        }

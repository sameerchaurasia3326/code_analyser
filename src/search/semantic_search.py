"""Semantic search engine."""

from typing import List, Dict, Any, Optional

from src.embeddings.embedding_service import EmbeddingService
from src.embeddings.vector_store import VectorStore
from src.config import settings
from src.utils.logger import setup_logger

from src.generation.generation_service import GenerationService
from src.search.query_intent import QueryIntent
from src.search.query_analyzer import QueryAnalyzer
from src.search.concept_scorer import ConceptScorer
from src.search.result_aggregator import ResultAggregator


logger = setup_logger("search")


class SemanticSearch:
    """Semantic search engine for code."""

    def __init__(self):
        """Initialize the search engine."""
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.result_aggregator = ResultAggregator()
        self.generation_service = GenerationService()
        self.query_analyzer = QueryAnalyzer()
        # QueryIntent is static, no need to instantiate
        self.concept_scorer = ConceptScorer()
        
        logger.info("Initialized SemanticSearch")

    def search(
        self,
        query: str,
        limit: int = None,
        file_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for code using natural language query.

        Args:
            query: Natural language search query
            limit: Maximum number of results (default from settings)
            file_filter: Optional filter by file path
            type_filter: Optional filter by code unit type

        Returns:
            List of search results
        """
        if not query:
            raise ValueError("Query cannot be empty")

        if limit is None:
            limit = settings.default_search_limit

        logger.info(f"Searching for: '{query}' (limit={limit})")
        
        # Detect query intent and adjust parameters
        from src.search.query_intent import QueryIntent
        search_params = QueryIntent.adjust_search_params(query, default_limit=limit)
        
        # Use adjusted limit and filters
        adjusted_limit = search_params['limit']
        
        # Build filter dictionary from initial parameters
        filter_dict = {}
        if file_filter:
            filter_dict["file_path"] = file_filter
        if type_filter:
            filter_dict["type"] = type_filter
            
        # Merge with filters from query intent, if any
        if search_params.get('filter_dict'):
            filter_dict.update(search_params['filter_dict'])

        # Generate query embedding
        query_embedding = self.embedding_service.generate_query_embedding(query)

        # Search vector store with adjusted parameters
        results = self.vector_store.search(
            query_embedding=query_embedding,
            limit=adjusted_limit,
            filter_dict=filter_dict if filter_dict else None,
        )

        # Detect concepts from query
        from src.search.query_analyzer import QueryAnalyzer
        from src.search.concept_scorer import ConceptScorer
        
        query_concepts = QueryAnalyzer.detect_concepts(query)
        
        # Boost scores with concept matching
        for result in results:
            # Get semantic similarity (1 - distance / 2) for L2 distance
            semantic_score = 1 - (result.get("distance", 0) / 2) if result.get("distance") is not None else 1.0
            
            # Get concepts from result metadata
            result_concepts = result.get("metadata", {}).get("concepts", [])
            
            # Calculate concept score
            concept_score = ConceptScorer.calculate_concept_score(query_concepts, result_concepts)
            
            # Check if has docstring
            has_docstring = bool(result.get("metadata", {}).get("docstring"))
            
            # Calculate boosted score
            boosted_score = ConceptScorer.boost_score_with_concepts(
                semantic_score=semantic_score,
                concept_score=concept_score,
                has_docstring=has_docstring
            )
            
            # Store both scores
            result["semantic_score"] = semantic_score
            result["concept_score"] = concept_score
            result["final_score"] = boosted_score
            
            # Update distance to reflect boosted score
            result["distance"] = 1 - boosted_score
        
        # Re-sort by final score (descending)
        results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        # Post-retrieval aggregation
        from src.search.result_aggregator import ResultAggregator
        
        # Aggregate and deduplicate results
        aggregated_results = ResultAggregator.aggregate_results(results, max_results=limit)
        
        # Merge context for better understanding
        final_results = ResultAggregator.merge_context(aggregated_results)

        logger.info(f"Found {len(final_results)} results after aggregation")
        return final_results

    def find_similar(
        self, file_path: str, code_name: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find code similar to a specific function or class.

        Args:
            file_path: Path to file containing the code
            code_name: Name of the function or class
            limit: Maximum number of results

        Returns:
            List of similar code units
        """
        logger.info(f"Finding code similar to {code_name} in {file_path}")

        # Search for the original code unit
        results = self.vector_store.search(
            query_embedding=[0.0] * settings.embedding_dimension,  # Dummy embedding
            limit=1000,  # Get many results to filter
        )

        # Find the specific code unit
        target_unit = None
        for result in results:
            if (
                result["metadata"]["file_path"] == file_path
                and result["metadata"]["name"] == code_name
            ):
                target_unit = result
                break

        if not target_unit:
            logger.warning(f"Code unit not found: {code_name} in {file_path}")
            return []

        # Use the document text to find similar code
        similar_results = self.search(target_unit["document"], limit=limit + 1)

        # Remove the original code unit from results
        similar_results = [
            r for r in similar_results
            if not (
                r["metadata"]["file_path"] == file_path
                and r["metadata"]["name"] == code_name
            )
        ][:limit]

        return similar_results

    def summarize_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate a summary of search results.
        
        Args:
            query: Original search query
            results: List of search results
            
        Returns:
            Generated summary text
        """
        return self.generation_service.generate_summary(query, results)

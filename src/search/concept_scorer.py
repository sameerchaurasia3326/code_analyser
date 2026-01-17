"""Concept-based scoring for cross-language code similarity."""

from typing import List
from src.models.code_concepts import CodeConcept


class ConceptScorer:
    """Score code similarity based on programming concepts."""
    
    @staticmethod
    def calculate_concept_score(
        query_concepts: List[CodeConcept],
        result_concepts: str  # Now a comma-separated string from ChromaDB
    ) -> float:
        """Calculate concept similarity score.
        
        Args:
            query_concepts: Concepts detected from query
            result_concepts: Concepts from code result (comma-separated string)
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not query_concepts or not result_concepts:
            return 0.0
        
        # Parse comma-separated string to list
        result_concept_list = [c.strip() for c in result_concepts.split(",") if c.strip()]
        
        # Convert result concepts to CodeConcept enum
        result_concept_enums = []
        for concept_str in result_concept_list:
            try:
                result_concept_enums.append(CodeConcept(concept_str))
            except ValueError:
                continue
        
        if not result_concept_enums:
            return 0.0
        
        # Calculate Jaccard similarity (intersection / union)
        query_set = set(query_concepts)
        result_set = set(result_concept_enums)
        
        intersection = len(query_set & result_set)
        union = len(query_set | result_set)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def boost_score_with_concepts(
        semantic_score: float,
        concept_score: float,
        semantic_weight: float = 0.60,
        concept_weight: float = 0.25,
        quality_weight: float = 0.10,
        recency_weight: float = 0.05,
        has_docstring: bool = False
    ) -> float:
        """Calculate final score with concept boost.
        
        Args:
            semantic_score: Embedding similarity (0-1)
            concept_score: Concept match score (0-1)
            semantic_weight: Weight for semantic similarity
            concept_weight: Weight for concept matching
            quality_weight: Weight for code quality
            recency_weight: Weight for recency
            has_docstring: Whether code has documentation
            
        Returns:
            Final boosted score (0-1)
        """
        # Quality score based on documentation
        quality_score = 1.0 if has_docstring else 0.5
        
        # Recency score (placeholder - would need timestamp)
        recency_score = 0.5
        
        # Weighted combination
        final_score = (
            semantic_score * semantic_weight +
            concept_score * concept_weight +
            quality_score * quality_weight +
            recency_score * recency_weight
        )
        
        return min(final_score, 1.0)  # Cap at 1.0

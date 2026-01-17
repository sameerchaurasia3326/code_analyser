"""Post-retrieval aggregation for search results."""

from typing import List, Dict, Any
from collections import defaultdict


class ResultAggregator:
    """Aggregate and deduplicate search results."""
    
    @staticmethod
    def aggregate_results(results: List[Dict[str, Any]], max_results: int = 10) -> List[Dict[str, Any]]:
        """Aggregate search results by grouping related code units.
        
        Args:
            results: Raw search results from vector store
            max_results: Maximum number of results to return
            
        Returns:
            Aggregated and deduplicated results
        """
        if not results:
            return []
        
        # First, deduplicate exact duplicates
        deduplicated = ResultAggregator._deduplicate(results)
        
        # Group by file for context enrichment only
        file_groups = defaultdict(list)
        for result in deduplicated:
            file_path = result.get("metadata", {}).get("file_path", "unknown")
            file_groups[file_path].append(result)
        
        # Add related context without removing results
        for file_path, file_results in file_groups.items():
            # Sort by score within file
            file_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
            
            # For each result, find related items
            for i, result in enumerate(file_results):
                # Find related items (same file, different name)
                related = []
                result_name = result.get("metadata", {}).get("name", "")
                
                for other in file_results:
                    other_name = other.get("metadata", {}).get("name", "")
                    if other_name != result_name and len(related) < 3:
                        related.append(other_name)
                
                if related:
                    result["related_methods"] = related
        
        # Return all deduplicated results, sorted by score
        deduplicated.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return deduplicated[:max_results]
    
    @staticmethod
    def _group_by_class(results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group results by class name."""
        class_groups = defaultdict(list)
        
        for result in results:
            metadata = result.get("metadata", {})
            code_type = metadata.get("type", "")
            name = metadata.get("name", "")
            
            # For methods, try to extract class name from signature or name
            if code_type == "method":
                # Use file path + type as grouping key for methods
                class_key = f"{metadata.get('file_path', '')}:methods"
            elif code_type == "class":
                class_key = f"class:{name}"
            else:
                class_key = f"standalone:{name}"
            
            class_groups[class_key].append(result)
        
        return class_groups
    
    @staticmethod
    def _deduplicate(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or very similar results."""
        if not results:
            return []
        
        deduplicated = []
        seen_signatures = set()
        
        for result in results:
            metadata = result.get("metadata", {})
            
            # Create signature for deduplication based on CONTENT, not file path
            # identifying name, type, and actual code content
            signature = (
                metadata.get("name", ""),
                metadata.get("type", ""),
                result.get("document", "").strip()  # Use content itself for dedup
            )
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                deduplicated.append(result)
        
        return deduplicated
    
    @staticmethod
    def merge_context(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge results from the same context (file/class) to show full picture.
        
        Args:
            results: Search results
            
        Returns:
            Results with merged context
        """
        # Group by file and nearby lines
        context_groups = defaultdict(list)
        
        for result in results:
            metadata = result.get("metadata", {})
            file_path = metadata.get("file_path", "")
            start_line = metadata.get("start_line", 0)
            
            # Group results within 50 lines of each other
            context_key = f"{file_path}:{start_line // 50}"
            context_groups[context_key].append(result)
        
        merged = []
        
        for context_key, group in context_groups.items():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Merge multiple results from same context
                primary = group[0]  # Highest scoring
                
                # Add context info
                primary["context_size"] = len(group)
                primary["context_items"] = [
                    {
                        "name": r.get("metadata", {}).get("name"),
                        "type": r.get("metadata", {}).get("type"),
                        "score": r.get("final_score", 0)
                    }
                    for r in group[1:4]  # Up to 3 additional items
                ]
                
                merged.append(primary)
        
        return merged

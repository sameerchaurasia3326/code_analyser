"""Query intent detection for better search results."""

from typing import List, Dict, Any
import re


class QueryIntent:
    """Detect user intent from search queries."""
    
    # Intent patterns
    INTENTS = {
        'list_all_classes': [
            r'(list|show|what are|find)\s+(all\s+)?(the\s+)?classes',
            r'responsibility\s+of\s+each\s+class',
            r'what\s+classes\s+(are|exist)',
        ],
        'list_all_functions': [
            r'(list|show|what are)\s+(all\s+)?(the\s+)?functions',
            r'(list|show|what are)\s+(all\s+)?(the\s+)?methods',
        ],
        'find_error_handling': [
            r'error\s+handling',
            r'exception\s+handling',
            r'try\s+catch',
        ],
        'find_async': [
            r'async',
            r'asynchronous',
            r'await',
        ],
    }
    
    @staticmethod
    def detect_intent(query: str) -> Dict[str, Any]:
        """Detect the intent of a search query.
        
        Args:
            query: User's search query
            
        Returns:
            Dictionary with intent information
        """
        query_lower = query.lower()
        
        detected_intent = {
            'type': 'general',
            'filter_type': None,
            'expand_limit': False
        }
        
        # Check for list all classes intent
        for pattern in QueryIntent.INTENTS['list_all_classes']:
            if re.search(pattern, query_lower):
                detected_intent['type'] = 'list_all_classes'
                detected_intent['filter_type'] = 'class'
                detected_intent['expand_limit'] = True
                return detected_intent
        
        # Check for list all functions intent
        for pattern in QueryIntent.INTENTS['list_all_functions']:
            if re.search(pattern, query_lower):
                detected_intent['type'] = 'list_all_functions'
                detected_intent['filter_type'] = 'function'
                detected_intent['expand_limit'] = True
                return detected_intent
        
        return detected_intent
    
    @staticmethod
    def adjust_search_params(query: str, default_limit: int = 5) -> Dict[str, Any]:
        """Adjust search parameters based on query intent.
        
        Args:
            query: User's search query
            default_limit: Default result limit
            
        Returns:
            Adjusted search parameters
        """
        intent = QueryIntent.detect_intent(query)
        
        params = {
            'limit': default_limit,
            'filter_dict': None
        }
        
        # Expand limit for "list all" queries
        if intent['expand_limit']:
            params['limit'] = 20
        
        # Add type filter if detected
        if intent['filter_type']:
            params['filter_dict'] = {'type': intent['filter_type']}
        
        return params

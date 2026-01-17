"""Query analysis for detecting programming concepts from natural language."""

from typing import List
from src.models.code_concepts import CodeConcept


class QueryAnalyzer:
    """Analyze search queries to detect programming concepts."""
    
    # Map keywords to concepts
    CONCEPT_KEYWORDS = {
        CodeConcept.ASYNC_OPERATION: [
            'async', 'asynchronous', 'await', 'promise', 'future',
            'non-blocking', 'concurrent operation'
        ],
        CodeConcept.THREAD_CREATION: [
            'thread', 'threading', 'concurrent', 'parallel', 'worker',
            'spawn', 'create thread'
        ],
        CodeConcept.SYNCHRONIZATION: [
            'lock', 'mutex', 'semaphore', 'synchronize', 'synchronized',
            'critical section', 'race condition'
        ],
        CodeConcept.DATABASE_QUERY: [
            'database', 'query', 'sql', 'select', 'insert', 'update',
            'delete', 'db', 'execute query'
        ],
        CodeConcept.FILE_IO: [
            'file', 'read file', 'write file', 'open file', 'file io',
            'file operation', 'read', 'write'
        ],
        CodeConcept.NETWORK_REQUEST: [
            'http', 'request', 'fetch', 'api call', 'network', 'rest',
            'get request', 'post request', 'ajax'
        ],
        CodeConcept.ERROR_HANDLING: [
            'error', 'exception', 'try', 'catch', 'handle error',
            'error handling', 'throw', 'raise'
        ],
        CodeConcept.LOOP_ITERATION: [
            'loop', 'iterate', 'for loop', 'while loop', 'foreach',
            'iteration', 'repeat'
        ],
        CodeConcept.ARRAY_OPERATION: [
            'array', 'list', 'append', 'push', 'pop', 'slice',
            'array operation', 'list operation'
        ],
        CodeConcept.MAP_OPERATION: [
            'map', 'dictionary', 'hash', 'hashmap', 'object',
            'key value', 'associative array'
        ],
        CodeConcept.INITIALIZATION: [
            'initialize', 'init', 'constructor', 'setup', 'create',
            'instantiate'
        ],
        CodeConcept.CLEANUP: [
            'cleanup', 'close', 'dispose', 'finalize', 'destroy',
            'release', 'free'
        ]
    }
    
    @staticmethod
    def detect_concepts(query: str) -> List[CodeConcept]:
        """Detect programming concepts from a natural language query.
        
        Args:
            query: Natural language search query
            
        Returns:
            List of detected concepts
        """
        concepts = []
        query_lower = query.lower()
        
        for concept, keywords in QueryAnalyzer.CONCEPT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    concepts.append(concept)
                    break  # Only add concept once
        
        return concepts

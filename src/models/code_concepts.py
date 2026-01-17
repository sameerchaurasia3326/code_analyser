"""Universal programming concepts for cross-language understanding."""

from enum import Enum
from typing import List, Set


class CodeConcept(str, Enum):
    """Universal programming concepts that exist across languages."""
    
    # Concurrency patterns
    THREAD_CREATION = "thread_creation"
    ASYNC_OPERATION = "async_operation"
    SYNCHRONIZATION = "synchronization"
    MUTEX_LOCK = "mutex_lock"
    GOROUTINE = "goroutine"
    
    # Data access patterns
    DATABASE_QUERY = "database_query"
    FILE_IO = "file_io"
    NETWORK_REQUEST = "network_request"
    CACHE_ACCESS = "cache_access"
    
    # Lifecycle management
    INITIALIZATION = "initialization"
    CLEANUP = "cleanup"
    RESOURCE_ALLOCATION = "resource_allocation"
    ERROR_HANDLING = "error_handling"
    
    # Control flow
    LOOP_ITERATION = "loop_iteration"
    CONDITIONAL_BRANCH = "conditional_branch"
    RECURSION = "recursion"
    
    # Data structures
    ARRAY_OPERATION = "array_operation"
    MAP_OPERATION = "map_operation"
    LIST_OPERATION = "list_operation"


class ConceptDetector:
    """Detect programming concepts from code."""
    
    # Language-specific patterns for each concept
    CONCEPT_PATTERNS = {
        CodeConcept.ASYNC_OPERATION: {
            'python': ['async def', 'await ', 'asyncio'],
            'javascript': ['async function', 'async (', 'await ', 'Promise'],
            'java': ['CompletableFuture', 'async', 'Future<'],
            'go': ['go func', 'goroutine', 'chan ']
        },
        CodeConcept.THREAD_CREATION: {
            'python': ['threading.Thread', 'Thread('],
            'javascript': ['new Worker(', 'worker.postMessage'],
            'java': ['new Thread(', 'Thread.start'],
            'go': ['go func(']
        },
        CodeConcept.SYNCHRONIZATION: {
            'python': ['threading.Lock', 'threading.RLock', 'Semaphore'],
            'javascript': ['Atomics.', 'SharedArrayBuffer'],
            'java': ['synchronized', 'ReentrantLock', 'Semaphore'],
            'go': ['sync.Mutex', 'sync.RWMutex', 'sync.WaitGroup']
        },
        CodeConcept.DATABASE_QUERY: {
            'python': ['cursor.execute', 'db.query', 'SELECT ', 'INSERT ', 'UPDATE '],
            'javascript': ['db.query', 'execute(', 'SELECT ', 'findOne', 'find('],
            'java': ['executeQuery', 'executeUpdate', 'PreparedStatement'],
            'go': ['db.Query', 'db.Exec', 'QueryRow']
        },
        CodeConcept.FILE_IO: {
            'python': ['open(', 'file.read', 'file.write', 'with open'],
            'javascript': ['fs.read', 'fs.write', 'readFile', 'writeFile'],
            'java': ['FileReader', 'FileWriter', 'BufferedReader'],
            'go': ['os.Open', 'ioutil.ReadFile', 'os.Create']
        },
        CodeConcept.NETWORK_REQUEST: {
            'python': ['requests.', 'urllib', 'http.client', 'aiohttp'],
            'javascript': ['fetch(', 'axios', 'http.get', 'XMLHttpRequest'],
            'java': ['HttpClient', 'HttpURLConnection', 'RestTemplate'],
            'go': ['http.Get', 'http.Post', 'http.Client']
        },
        CodeConcept.ERROR_HANDLING: {
            'python': ['try:', 'except ', 'raise ', 'finally:'],
            'javascript': ['try {', 'catch (', 'throw ', 'finally {'],
            'java': ['try {', 'catch (', 'throw ', 'throws '],
            'go': ['if err != nil', 'error', 'panic(', 'recover()']
        },
        CodeConcept.LOOP_ITERATION: {
            'python': ['for ', 'while '],
            'javascript': ['for (', 'while (', 'forEach', '.map('],
            'java': ['for (', 'while (', 'forEach'],
            'go': ['for ', 'range ']
        },
        CodeConcept.ARRAY_OPERATION: {
            'python': ['.append(', '.extend(', '.pop(', 'list['],
            'javascript': ['.push(', '.pop(', '.slice(', '.splice('],
            'java': ['.add(', '.remove(', 'ArrayList', 'Arrays.'],
            'go': ['append(', 'make([]', 'slice']
        },
        CodeConcept.MAP_OPERATION: {
            'python': ['dict[', '.get(', '.keys(', '.values('],
            'javascript': ['Map(', '.set(', '.get(', 'Object.keys'],
            'java': ['HashMap', '.put(', '.get(', 'Map<'],
            'go': ['map[', 'make(map']
        }
    }
    
    @staticmethod
    def detect_concepts(code: str, language: str) -> List[CodeConcept]:
        """Detect programming concepts in code.
        
        Args:
            code: Source code
            language: Programming language (python, javascript, java, go)
            
        Returns:
            List of detected concepts
        """
        concepts: Set[CodeConcept] = set()
        code_lower = code.lower()
        
        for concept, patterns in ConceptDetector.CONCEPT_PATTERNS.items():
            if language in patterns:
                for pattern in patterns[language]:
                    if pattern.lower() in code_lower or pattern in code:
                        concepts.add(concept)
                        break
        
        return list(concepts)
    
    @staticmethod
    def get_concept_description(concept: CodeConcept) -> str:
        """Get human-readable description of a concept."""
        descriptions = {
            CodeConcept.ASYNC_OPERATION: "Asynchronous operation",
            CodeConcept.THREAD_CREATION: "Thread/concurrency creation",
            CodeConcept.SYNCHRONIZATION: "Synchronization primitive",
            CodeConcept.DATABASE_QUERY: "Database query/operation",
            CodeConcept.FILE_IO: "File I/O operation",
            CodeConcept.NETWORK_REQUEST: "Network/HTTP request",
            CodeConcept.ERROR_HANDLING: "Error/exception handling",
            CodeConcept.LOOP_ITERATION: "Loop/iteration",
            CodeConcept.ARRAY_OPERATION: "Array/list operation",
            CodeConcept.MAP_OPERATION: "Map/dictionary operation"
        }
        return descriptions.get(concept, concept.value)

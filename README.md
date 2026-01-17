# Semantic Code Analysis System

A CLI tool that understands source code by **meaning**, not just keywords. Using semantic embeddings, it can find relevant code, group similar logic, and answer questions about your codebase based on intent.

## 🌟 Features

- **Semantic Code Search**: Find code by describing what it does in natural language
- **Multi-Language Support**: Python, JavaScript, TypeScript, Java, Go
- **Intelligent Parsing**: Extracts functions and classes as meaningful semantic units
- **Vector Embeddings**: Uses OpenAI/Gemini/OpenRouter to capture code meaning
- **Automatic Failover**: Switches between providers if one fails
- **CLI Interface**: Simple command-line tools

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -e .

# Configure API key
cp .env.example .env
# Edit .env and add your API key
```

### 2. Index Your Code

```bash
code-analyser index /path/to/your/project
```

### 3. Search Semantically

```bash
code-analyser search "function that handles authentication"
code-analyser search "database connection logic" --limit 5
code-analyser search "error handling" --type function
```

## 💻 CLI Commands

### Index Code
```bash
# Index entire directory
code-analyser index /path/to/project

# Index specific file
code-analyser index /path/to/file.py
```

### Search Code
```bash
# Basic search
code-analyser search "your query here"

# With options
code-analyser search "query" --limit 10
code-analyser search "query" --type function
code-analyser search "query" --file "specific_file.py"
```

### View Statistics
```bash
code-analyser stats
```

### Python API

```python
from src.indexer.code_indexer import CodeIndexer
from src.search.semantic_search import SemanticSearch

# Index a codebase
indexer = CodeIndexer()
stats = indexer.index_directory("/path/to/project")
print(f"Indexed {stats['total_code_units']} code units")

# Search semantically
search_engine = SemanticSearch()
results = search_engine.search("error handling logic", limit=10)

for result in results:
    metadata = result["metadata"]
    print(f"{metadata['name']} in {metadata['file_path']}")
```

## 📁 Project Structure

```
code_analyser/
├── src/
│   ├── models/          # Data models for code units
│   ├── parser/          # Code parsers (Python AST)
│   ├── embeddings/      # Gemini embedding service & vector store
│   ├── indexer/         # Code indexing orchestration
│   ├── search/          # Semantic search engine
│   ├── cli/             # Command-line interface
│   └── config.py        # Configuration management
├── tests/               # Unit tests
├── examples/            # Example usage and sample code
├── pyproject.toml       # Project configuration
└── .env.example         # Environment variables template
```

## 🔧 How It Works

1. **Parse**: Code files are parsed using AST to extract functions, classes, and methods as semantic units
2. **Embed**: Each code unit is converted to a vector embedding using Google Gemini's embedding-001 model
3. **Store**: Embeddings are stored in ChromaDB vector database with metadata
4. **Search**: Natural language queries are converted to embeddings and matched against stored code
5. **Rank**: Results are ranked by semantic similarity and returned

## 🎯 Example Queries

Instead of searching for exact keywords, you can search by intent:

- "function that validates email addresses"
- "code that connects to database"
- "authentication and login logic"
- "error handling for API requests"
- "calculate sum or total"

The system understands the **meaning** and finds relevant code even if it uses different variable names or syntax.

## 🛠️ Technologies

- **Google Gemini**: Embedding generation (embedding-001 model)
- **ChromaDB**: Vector database for storing embeddings
- **FastAPI**: HTTP API framework
- **Click**: CLI framework
- **Rich**: Beautiful terminal output
- **Pydantic**: Data validation
- **Python AST**: Code parsing

## 📝 Configuration

All settings are in `.env`:

```bash
# API Key
GOOGLE_API_KEY=your_key_here

# Embedding Model
EMBEDDING_MODEL=models/embedding-001
EMBEDDING_DIMENSION=768

# Vector Database
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=code_embeddings

# Search Settings
DEFAULT_SEARCH_LIMIT=10
SIMILARITY_THRESHOLD=0.7
```

## 🧪 Testing

Run the test script:
```bash
python test_analyser.py
```

Run unit tests (coming soon):
```bash
pytest tests/
```

## 🚧 Roadmap

- [ ] Support for JavaScript, TypeScript, Java, Go
- [ ] Code clustering and grouping
- [ ] Question-answering over codebase
- [ ] FastAPI HTTP endpoints
- [ ] Web UI interface
- [ ] Code similarity visualization
- [ ] Integration with IDEs

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! This is a semantic code analysis system designed to help developers understand and navigate codebases more effectively.

---

**Built with ❤️ using Google Gemini and ChromaDB**

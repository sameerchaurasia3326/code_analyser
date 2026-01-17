#!/usr/bin/env python3
"""Interactive terminal interface for code analysis."""

import sys
import tempfile
import os
from pathlib import Path

from src.indexer.code_indexer import CodeIndexer
from src.search.semantic_search import SemanticSearch
from src.utils.display_helpers import format_code_preview


def main():
    """Run interactive code analyzer."""
    print("=" * 70)
    print("🚀 Semantic Code Analyzer - Interactive Terminal")
    print("=" * 70)
    print()
    print("📚 Supported Languages: Python, JavaScript, TypeScript, Java, Go")
    print()
    
    # Initialize
    indexer = CodeIndexer()
    search_engine = SemanticSearch()
    
    while True:
        print("-" * 70)
        print("📝 PASTE YOUR CODE (or type 'search' to search, 'quit' to exit)")
        print("-" * 70)
        print("Enter 'search' to search, or paste your code: ", end="")
        
        first_line = input().strip().lower()
        
        if first_line in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
            
        if first_line == 'clear':
            # Clear database command
            try:
                search_engine.vector_store.clear()
                # Re-initialize indexer and search engine to get fresh collection reference
                # This fixes "Collection does not exist" error
                indexer = CodeIndexer()
                search_engine = SemanticSearch()
                print("\n🧹 Database cleared successfully!\n")
            except Exception as e:
                print(f"\n❌ Error clearing database: {e}\n")
            continue
        
        if first_line == 'search':
            # Search mode
            print("\n🔍 Enter your search query: ", end="")
            query = input().strip()
            
            if not query:
                continue
            
            print(f"\n🔎 Searching for: '{query}'")
            print("-" * 70)
            
            try:
                results = search_engine.search(query, limit=5)
                
                if results:
                    print(f"\n✅ Found {len(results)} results:\n")
                    
                    for i, result in enumerate(results, 1):
                        metadata = result["metadata"]
                        distance = result.get("distance", 0)
                        similarity = (1 - distance / 2) * 100 if distance is not None else 100
                        
                        lang_emoji = {
                            'python': '🐍',
                            'javascript': '📜',
                            'java': '☕',
                            'go': '🔷'
                        }
                        emoji = lang_emoji.get(metadata.get('language', ''), '📄')
                        
                        print(f"{i}. {emoji} {metadata['name']} ({metadata['type']}) - {similarity:.1f}% match")
                        print(f"   Language: {metadata.get('language', 'unknown')}")
                        print(f"   File: Line {metadata['start_line']}-{metadata['end_line']}")
                        if metadata.get('signature'):
                            print(f"   Signature: {metadata['signature']}")
                        
                        # Show related methods if available
                        if result.get("related_methods"):
                            related = ", ".join(result["related_methods"])
                            print(f"   Related: {related}")
                        
                        # Show context size if merged
                        if result.get("context_size", 0) > 1:
                            print(f"   Context: {result['context_size']} related items in same area")
                        
                        # Show relevant code lines based on query
                        if result.get("document"):
                            print(f"   📄 Relevant Code:")
                            preview = format_code_preview(result["document"], query, max_lines=5)
                            print(preview)
                        
                        print()
                    
                    print("-" * 70)
                    print("🤖 Generating AI Summary...")
                    try:
                        summary = search_engine.summarize_results(query, results)
                        print("\n💡 AI Summary:")
                        print(summary)
                    except Exception as e:
                        print(f"⚠️ Could not generate summary: {e}")
                    print("-" * 70)
                else:
                    print("\n❌ No results found.\n")
            except Exception as e:
                print(f"\n❌ Search error: {e}\n")
            
            continue
        
        # Get code input (first line already read)
        print("\n📋 Paste your code (press Ctrl+D or Ctrl+Z when done):")
        print("-" * 70)
        
        try:
            lines = [first_line]  # Include the first line
            while True:
                try:
                    line = input()
                    lines.append(line)
                except EOFError:
                    break
            
            code = '\n'.join(lines)
            
            if not code.strip():
                print("\n❌ No code provided.\n")
                continue
            
            # Auto-detect language
            from src.utils.language_detector import LanguageDetector
            detected_language = LanguageDetector.detect(code)
            
            if not detected_language:
                print("\n❌ Could not detect language. Supported: Python, JavaScript, Java, Go\n")
                continue
            
            print(f"\n🔍 Detected language: {detected_language.upper()}")
            
            # Map to file extension
            lang_map = {
                'python': '.py',
                'javascript': '.js',
                'java': '.java',
                'go': '.go'
            }
            
            extension = lang_map[detected_language]
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            print(f"🔍 Processing your {detected_language} code...")
            print("-" * 70)
            
            # Index the code
            try:
                stats = indexer.index_file(temp_file)
                
                print(f"\n✅ Code processed successfully!")
                print(f"   Code units extracted: {stats['total_code_units']}")
                print(f"   Language: {detected_language}")
                print()
                
                if stats['total_code_units'] > 0:
                    print("💡 Your code is now searchable! Type 'search' to find code.\n")
                else:
                    print("⚠️  No functions or classes found in the code.\n")
                
            except Exception as e:
                print(f"\n❌ Error processing code: {e}\n")
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except KeyboardInterrupt:
            print("\n\n⚠️  Input cancelled.\n")
            continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)

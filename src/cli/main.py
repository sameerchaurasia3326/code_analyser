"""Command-line interface for code analyser."""

import click
from rich.console import Console
from rich.table import Table
from pathlib import Path

from src.indexer.code_indexer import CodeIndexer
from src.search.semantic_search import SemanticSearch
from src.config import settings

console = Console()


@click.group()
def cli():
    """Semantic Code Analysis System - Understand code by meaning, not just keywords."""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def index(path):
    """Index a codebase directory or file.

    PATH: Directory or file to index
    """
    console.print(f"\n[bold cyan]Indexing:[/bold cyan] {path}\n")

    try:
        indexer = CodeIndexer()

        if Path(path).is_dir():
            stats = indexer.index_directory(path)
        else:
            stats = indexer.index_file(path)

        # Display results
        console.print("\n[bold green]✓ Indexing Complete![/bold green]\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in stats.items():
            table.add_row(key.replace("_", " ").title(), str(value))

        console.print(table)

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        raise click.Abort()


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", default=10, help="Maximum number of results")
@click.option("--file", "-f", help="Filter by file path")
@click.option("--type", "-t", help="Filter by code type (function, class, method)")
def search(query, limit, file, type):
    """Search for code using natural language.

    QUERY: Natural language search query
    """
    console.print(f"\n[bold cyan]Searching for:[/bold cyan] '{query}'\n")

    try:
        search_engine = SemanticSearch()
        results = search_engine.search(
            query=query,
            limit=limit,
            file_filter=file,
            type_filter=type,
        )

        if not results:
            console.print("[yellow]No results found.[/yellow]\n")
            return

        console.print(f"[bold green]Found {len(results)} results:[/bold green]\n")

        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            distance = result.get("distance", 0)
            similarity = (1 - distance / 2) * 100 if distance is not None else 100

            console.print(f"[bold]{i}. {metadata['name']}[/bold] ({metadata['type']})")
            console.print(f"   [dim]File:[/dim] {metadata['file_path']}:{metadata['start_line']}")
            console.print(f"   [dim]Similarity:[/dim] {similarity:.1f}%")
            if metadata.get("signature"):
                console.print(f"   [dim]Signature:[/dim] {metadata['signature']}")
            console.print()

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        raise click.Abort()


@cli.command()
def stats():
    """Display indexing statistics."""
    try:
        indexer = CodeIndexer()
        stats_data = indexer.get_stats()

        console.print("\n[bold cyan]Vector Store Statistics:[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in stats_data.items():
            table.add_row(key.replace("_", " ").title(), str(value))

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        raise click.Abort()


if __name__ == "__main__":
    cli()

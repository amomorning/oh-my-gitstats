"""Command-line interface for oh-my-gitstats."""

from pathlib import Path

import click

from .collector import collect_all_repos, sync_repos
from .visualizer import generate_html


@click.group()
@click.version_option()
def main():
    """oh-my-gitstats: Git repository commit statistics collector and visualizer."""
    pass


@main.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-o", "--output",
    default="./data",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Directory to save JSON files (default: ./data)",
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress output messages",
)
def collect(path: str, output: str, quiet: bool):
    """Collect commit data from all git repositories under PATH.

    Scans the specified directory recursively for git repositories
    and saves commit data to individual JSON files.
    """
    verbose = not quiet
    saved_files = collect_all_repos(path, output, verbose=verbose)

    if not verbose:
        print(f"Saved {len(saved_files)} files to {output}")


@main.command()
@click.argument(
    "data_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress output messages",
)
def sync(data_dir: str, quiet: bool):
    """Incrementally update JSON files in DATA_DIR with new commits.

    Only fetches commits newer than the latest commit in each existing
    JSON file, making it much faster than a full collect.
    """
    verbose = not quiet
    sync_repos(data_dir, verbose=verbose)


@main.command()
@click.argument(
    "json_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-o", "--output",
    default="./output/stats.html",
    type=click.Path(file_okay=True, dir_okay=False),
    help="Path to save the HTML file (default: ./output/stats.html)",
)
def visualize(json_dir: str, output: str):
    """Generate HTML visualization from JSON files in JSON_DIR.

    Creates an interactive HTML file with:
    - Line chart (metric and granularity selectable via UI)
    - Aggregated calendar heatmap
    - Individual calendar heatmaps per project
    """
    try:
        output_path = generate_html(json_dir, output)
        print(f"Generated: {output_path}")
    except ValueError as e:
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()

"""Command-line interface for oh-my-gitstats."""

import os
from pathlib import Path

import click

from .collector import collect_all_repos, sync_repos
from .visualizer import generate_html


def _warn_missing_github_token():
    """Print a warning if GITHUB_TOKEN is not set."""
    if not os.environ.get("GITHUB_TOKEN"):
        print("Warning: GITHUB_TOKEN is not set. "
              "Private repos cannot be checked and rate limits are lower. "
              "See README for instructions.")


@click.group(epilog="""\
Common workflows: \n
  1. Collect:   gitstats collect ~/projects -o ./data \n
  2. Sync:      gitstats sync ./data --check \n
  3. Visualize: gitstats visualize ./data \n

Use 'gitstats COMMAND --help' for more information on a command.
""")
@click.version_option()
def main():
    """oh-my-gitstats: Git repository commit statistics collector and visualizer."""
    pass


@main.command(epilog="""\
Examples: \n
  gitstats collect ~/projects --output ./data \n
  gitstats collect ~/code -o ./data --check \n
  gitstats collect ~/repos -q \n
""")
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-o", "--output",
    default="./data",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Directory to save JSON files.",
    show_default=True,
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress output messages.",
)
@click.option(
    "--check",
    is_flag=True,
    help="Check GitHub archive status (requires network; set GITHUB_TOKEN for private repos).",
)
def collect(path: str, output: str, quiet: bool, check: bool):
    """Collect commit data from all git repositories under PATH.

    Scans the specified directory recursively for git repositories
    and saves commit data to individual JSON files.
    """
    verbose = not quiet
    if check:
        _warn_missing_github_token()
    saved_files = collect_all_repos(path, output, verbose=verbose, check=check)

    if not verbose:
        print(f"Saved {len(saved_files)} files to {output}")


@main.command(epilog="""\
Examples: \n
  gitstats sync ./data \n
  gitstats sync ./data --check \n
  gitstats sync ./data -q \n
""")
@click.argument(
    "data_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress output messages.",
)
@click.option(
    "--check",
    is_flag=True,
    help="Check GitHub archive status (requires network; set GITHUB_TOKEN for private repos).",
)
def sync(data_dir: str, quiet: bool, check: bool):
    """Incrementally update JSON files in DATA_DIR with new commits.

    Only fetches commits newer than the latest commit in each existing
    JSON file, making it much faster than a full collect.

    Use --check to also query the GitHub API and record whether each
    repository is archived.
    """
    verbose = not quiet
    if check:
        _warn_missing_github_token()
    sync_repos(data_dir, verbose=verbose, check=check)


@main.command(epilog="""\
Examples: \n
  gitstats visualize ./data \n
  gitstats visualize ./data -o ./report.html \n
""")
@click.argument(
    "json_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-o", "--output",
    default="./output/stats.html",
    type=click.Path(file_okay=True, dir_okay=False),
    help="Path to save the HTML file.",
    show_default=True,
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

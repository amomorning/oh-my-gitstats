"""Command-line interface for oh-my-gitstats."""

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

import click

from .collector import collect_all_repos, sync_repos
from .settings import add_collect_path, init_default_settings, load_settings, SETTINGS_PATH
from .visualizer import generate_html


def _warn_missing_github_token():
    """Print a warning if GITHUB_TOKEN is not set."""
    if not os.environ.get("GITHUB_TOKEN"):
        print("Warning: GITHUB_TOKEN is not set. "
              "Private repos cannot be checked and rate limits are lower. "
              "See README for instructions.")


class Spinner:
    """Simple terminal spinner for non-verbose progress indication."""

    _FRAMES = ("|", "/", "-", "\\")
    _INTERVAL = 0.1

    def __init__(self, enabled=True):
        self.enabled = enabled
        self._thread = None
        self._stop_event = threading.Event()
        self._message = ""

    def start(self, message=""):
        """Start the spinner with a status message."""
        if not self.enabled:
            return
        self._message = message
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the spinner and clear the line."""
        if not self.enabled or self._thread is None:
            return
        self._stop_event.set()
        self._thread.join()
        self._thread = None
        clear_len = len(self._message) + 2
        sys.stdout.write(f"\r{' ' * clear_len}\r")
        sys.stdout.flush()

    def _spin(self):
        idx = 0
        while not self._stop_event.is_set():
            frame = self._FRAMES[idx % len(self._FRAMES)]
            sys.stdout.write(f"\r{frame} {self._message}")
            sys.stdout.flush()
            idx += 1
            time.sleep(self._INTERVAL)


class MainGroup(click.Group):
    def invoke(self, ctx):
        init_default_settings()
        return super().invoke(ctx)


@click.group(
    cls=MainGroup,
    epilog="""\
Common workflows: \n
  Quick run:  gitstats auto \n
  1. Collect:   gitstats collect ~/projects \n
  2. Sync:      gitstats sync --check \n
  3. Visualize: gitstats visualize \n

Use 'gitstats COMMAND --help' for more information on a command.
""",
)
@click.version_option()
def main():
    """oh-my-gitstats: Git repository commit statistics collector and visualizer."""
    pass


@main.command(epilog="""\
Examples: \n
  gitstats collect ~/projects \n
  gitstats collect ~/code --check \n
  gitstats collect ~/repos -q \n
""")
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-o", "--output",
    default=None,
    type=click.Path(file_okay=False, dir_okay=True),
    help="Directory to save JSON files (default: ~/.gitstats/data).",
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress output messages.",
)
@click.option(
    "--skip",
    is_flag=True,
    help="Skip repos that already have a JSON file in the output directory.",
)
@click.option(
    "--check",
    is_flag=True,
    help="Check GitHub archive status (requires network; set GITHUB_TOKEN for private repos).",
)
def collect(path: str, output: str, quiet: bool, skip: bool, check: bool):
    """Collect commit data from all git repositories under PATH.

    Scans the specified directory recursively for git repositories
    and saves commit data to individual JSON files.
    """
    if output is None:
        settings = load_settings()
        output = str(settings["data_dir"])

    verbose = not quiet
    if check:
        _warn_missing_github_token()
    add_collect_path(path)
    saved_files = collect_all_repos(path, output, verbose=verbose, skip=skip, check=check)

    if not verbose:
        print(f"Saved {len(saved_files)} files to {output}")


@main.command(epilog="""\
Examples: \n
  gitstats sync \n
  gitstats sync --check \n
  gitstats sync ./data -q \n
""")
@click.argument(
    "data_dir",
    required=False,
    default=None,
    type=click.Path(file_okay=False, dir_okay=True),
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
    if data_dir is None:
        settings = load_settings()
        data_dir = str(settings["data_dir"])

    verbose = not quiet
    if check:
        _warn_missing_github_token()
    sync_repos(data_dir, verbose=verbose, check=check)


@main.command(epilog="""\
Examples: \n
  gitstats visualize \n
  gitstats visualize ./data -o ./report.html \n
""")
@click.argument(
    "json_dir",
    required=False,
    default=None,
    type=click.Path(file_okay=False, dir_okay=True),
)
@click.option(
    "-o", "--output",
    default=None,
    type=click.Path(file_okay=True, dir_okay=False),
    help="Path to save the HTML file (default: ~/.gitstats/stats.html).",
)
def visualize(json_dir: str, output: str):
    """Generate HTML visualization from JSON files in JSON_DIR.

    Creates an interactive HTML file with:
    - Line chart (metric and granularity selectable via UI)
    - Aggregated calendar heatmap
    - Individual calendar heatmaps per project
    """
    settings = load_settings()
    if json_dir is None:
        json_dir = str(settings["data_dir"])
    if output is None:
        output = str(settings["output_html"])

    try:
        output_path = generate_html(json_dir, output)
        print(f"Generated: {output_path}")
    except ValueError as e:
        raise click.ClickException(str(e))


@main.command(epilog="""\
Examples: \n
  gitstats auto \n
  gitstats auto --verbose \n
  gitstats auto --check \n
  gitstats auto --no-open \n
""")
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed output for each step (default: spinner only).",
)
@click.option(
    "--check",
    is_flag=True,
    help="Check GitHub archive status (requires network; set GITHUB_TOKEN for private repos).",
)
@click.option(
    "--no-open",
    is_flag=True,
    help="Do not open the HTML file in browser after generation.",
)
def auto(verbose: bool, check: bool, no_open: bool):
    """Run collect, sync, and visualize in one step.

    Reads collect_paths from ~/.gitstats/settings.json and processes
    each directory, then syncs and generates the HTML visualization.

    By default shows a compact spinner. Use --verbose for detailed output.
    """
    settings = load_settings()
    collect_paths = settings["collect_paths"]
    data_dir = str(settings["data_dir"])
    output_html = str(settings["output_html"])

    if check:
        _warn_missing_github_token()

    if not collect_paths:
        raise click.ClickException(
            "No collect_paths configured. "
            f"Edit {SETTINGS_PATH} to add directories containing git repos."
        )

    spinner = Spinner(enabled=not verbose)

    # Step 1: Collect from each configured path (skip existing)
    total_collected = 0
    spinner.start("Collecting repositories...")
    for path in collect_paths:
        if not Path(path).is_dir():
            if verbose:
                print(f"Skipping (not found): {path}")
            continue
        if verbose:
            print(f"Collecting from: {path}")
        files = collect_all_repos(path, data_dir, verbose=verbose, skip=True, check=check)
        total_collected += len(files)
    spinner.stop()

    if verbose:
        print(f"\nCollected {total_collected} repos total")

    # Step 2: Sync
    if verbose:
        print("\nSyncing...")
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    spinner.start("Syncing repositories...")
    sync_repos(data_dir, verbose=verbose, check=check)
    spinner.stop()

    # Step 3: Visualize
    if verbose:
        print("\nGenerating visualization...")
    spinner.start("Generating visualization...")
    try:
        result_path = generate_html(data_dir, output_html)
    except ValueError as e:
        spinner.stop()
        raise click.ClickException(str(e))
    spinner.stop()
    print(f"Generated: {result_path}")

    # Step 4: Open in browser
    if not no_open:
        html_path = Path(result_path).resolve()
        webbrowser.open(html_path.as_uri())
        if verbose:
            print(f"Opened in browser: {html_path}")


if __name__ == "__main__":
    main()

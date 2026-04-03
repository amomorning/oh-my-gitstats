"""Git repository commit data collector."""

import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any

from git import Repo, Commit


class SyncStatus(str, Enum):
    """Git repository sync status with remote."""

    SYNCED = "synced"
    LOCAL_CHANGES = "local_changes"
    REMOTE_AHEAD = "remote_ahead"
    DIVERGED = "diverged"
    LOCAL_ONLY_CLEAN = "local_only_clean"
    LOCAL_ONLY_DIRTY = "local_only_dirty"


def find_git_repos(root_path: str) -> List[Path]:
    """Find all git repositories under the given directory.

    Args:
        root_path: Root directory to search for git repos.

    Returns:
        List of paths to git repositories.
    """
    root = Path(root_path)
    repos = []

    for path in root.rglob(".git"):
        if path.is_dir():
            repos.append(path.parent)

    return repos


def extract_commit_data(repo_path: Path) -> Dict[str, Any]:
    """Extract commit data from a git repository.

    Args:
        repo_path: Path to the git repository.

    Returns:
        Dictionary containing repo name and commit data.
    """
    repo = Repo(repo_path)
    commits = []

    for commit in repo.iter_commits():
        commit_data = _parse_commit(commit)
        commits.append(commit_data)

    # Sort by timestamp ascending
    commits.sort(key=lambda x: x["timestamp"])

    return {
        "repo_name": repo_path.name,
        "repo_path": str(repo_path.absolute()),
        "sync_status": _get_sync_status(repo_path),
        "commits": commits
    }


def _get_sync_status(repo_path: Path) -> SyncStatus:
    """Check sync status between local repo and its remote.

    Args:
        repo_path: Path to the git repository.

    Returns:
        SyncStatus enum indicating the sync state.
    """
    repo = Repo(repo_path)
    is_dirty = repo.is_dirty(untracked_files=True)

    try:
        origin = repo.remote("origin")
        origin.fetch()
        active_branch = repo.active_branch
        tracking = active_branch.tracking_branch()
        if tracking:
            behind = list(repo.iter_commits(f"{active_branch}..{tracking}"))
            remote_ahead = len(behind) > 0
        else:
            remote_ahead = False
    except Exception:
        return SyncStatus.LOCAL_ONLY_DIRTY if is_dirty else SyncStatus.LOCAL_ONLY_CLEAN

    if is_dirty and remote_ahead:
        return SyncStatus.DIVERGED
    if is_dirty:
        return SyncStatus.LOCAL_CHANGES
    if remote_ahead:
        return SyncStatus.REMOTE_AHEAD
    return SyncStatus.SYNCED


def _parse_commit(commit: Commit) -> Dict[str, Any]:
    """Parse a single commit into our data format.

    Args:
        commit: GitPython Commit object.

    Returns:
        Dictionary with timestamp, additions, and deletions.
    """
    # Get commit stats
    stats = commit.stats.total

    return {
        "timestamp": commit.committed_datetime.isoformat(),
        "additions": stats.get("insertions", 0),
        "deletions": stats.get("deletions", 0)
    }


def save_repo_data(data: Dict[str, Any], output_dir: Path) -> Path:
    """Save repository data to a JSON file.

    Args:
        data: Repository data dictionary.
        output_dir: Directory to save the JSON file.

    Returns:
        Path to the saved JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{data['repo_name']}.json"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def collect_all_repos(root_path: str, output_dir: str, verbose: bool = True) -> List[Path]:
    """Collect commit data from all git repos under root_path.

    Args:
        root_path: Root directory to search for git repos.
        output_dir: Directory to save JSON files.
        verbose: Whether to print progress messages.

    Returns:
        List of paths to saved JSON files.
    """
    repos = find_git_repos(root_path)

    if verbose:
        print(f"Found {len(repos)} git repositories")

    output_path = Path(output_dir)
    saved_files = []

    for repo_path in repos:
        if verbose:
            print(f"Processing: {repo_path.name}")

        try:
            data = extract_commit_data(repo_path)
            if data["commits"]:  # Only save if there are commits
                filepath = save_repo_data(data, output_path)
                saved_files.append(filepath)
            else:
                if verbose:
                    print(f"  Skipped (no commits)")
        except Exception as e:
            if verbose:
                print(f"  Error: {e}")

    if verbose:
        print(f"\nSaved {len(saved_files)} JSON files to {output_dir}")

    return saved_files

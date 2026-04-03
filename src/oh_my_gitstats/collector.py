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
        "last_commit_hash": _read_head_hash(repo_path),
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


def _read_head_hash(repo_path: Path) -> str | None:
    """Read HEAD commit hash directly from .git files, no GitPython.

    Args:
        repo_path: Path to the git repository.

    Returns:
        HEAD commit hash string, or None if it cannot be determined.
    """
    git_dir = repo_path / ".git"
    head_file = git_dir / "HEAD"
    if not head_file.exists():
        return None

    head = head_file.read_text().strip()
    if head.startswith("ref: "):
        ref_path = git_dir / head[5:]
        if ref_path.exists():
            return ref_path.read_text().strip()
        # packed-refs fallback
        packed = git_dir / "packed-refs"
        if packed.exists():
            ref_name = head[5:]
            for line in packed.read_text().splitlines():
                if line.endswith(f" {ref_name}"):
                    return line.split()[0]
        return None
    return head  # detached HEAD


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


def sync_repo_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Incrementally update a single repo's data with new commits.

    Args:
        data: Existing repository data dictionary (from JSON).

    Returns:
        Updated dictionary with new commits appended and sync_status refreshed.
    """
    repo_path = Path(data["repo_path"])
    repo = Repo(repo_path)

    existing_commits = data.get("commits", [])
    existing_ts_set = {c["timestamp"] for c in existing_commits}

    new_commits = []
    if existing_commits:
        last_ts = datetime.fromisoformat(existing_commits[-1]["timestamp"])
        for commit in repo.iter_commits(since=last_ts):
            parsed = _parse_commit(commit)
            if parsed["timestamp"] not in existing_ts_set:
                new_commits.append(parsed)
    else:
        # No existing commits — full scan fallback
        for commit in repo.iter_commits():
            new_commits.append(_parse_commit(commit))

    all_commits = existing_commits + new_commits
    all_commits.sort(key=lambda x: x["timestamp"])

    return {
        "repo_name": data["repo_name"],
        "repo_path": data["repo_path"],
        "last_commit_hash": _read_head_hash(repo_path),
        "sync_status": _get_sync_status(repo_path),
        "commits": all_commits,
    }


def sync_repos(data_dir: str, verbose: bool = True) -> List[Path]:
    """Incrementally update existing JSON files with new commits.

    Args:
        data_dir: Directory containing existing JSON files.
        verbose: Whether to print progress messages.

    Returns:
        List of paths to updated JSON files.
    """
    data_path = Path(data_dir)
    json_files = list(data_path.glob("*.json"))

    if not json_files:
        if verbose:
            print("No JSON files found in data directory")
        return []

    if verbose:
        print(f"Syncing {len(json_files)} repositories")

    saved_files = []

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        repo_path = Path(data["repo_path"])
        if not repo_path.is_dir() or not (repo_path / ".git").is_dir():
            if verbose:
                print(f"  Skipped (repo not found): {data['repo_name']}")
            continue

        if verbose:
            print(f"Syncing: {data['repo_name']}")

        # Fast skip: compare HEAD hash without opening GitPython
        stored_hash = data.get("last_commit_hash")
        current_hash = _read_head_hash(repo_path)
        if stored_hash and current_hash and stored_hash == current_hash:
            if verbose:
                print("  Skipped (no changes)")
            continue

        old_count = len(data.get("commits", []))
        try:
            updated = sync_repo_data(data)
            filepath = save_repo_data(updated, data_path)
            saved_files.append(filepath)

            new_count = len(updated["commits"]) - old_count
            if verbose:
                print(f"  +{new_count} new commits")
        except Exception as e:
            if verbose:
                print(f"  Error: {e}")

    if verbose:
        print(f"\nSynced {len(saved_files)} repositories")

    return saved_files


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

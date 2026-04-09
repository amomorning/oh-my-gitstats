"""Git repository commit data collector."""

import json
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any

import requests
from git import Repo, Commit


class SyncStatus(str, Enum):
    """Git repository sync status with remote."""

    SYNCED = "synced"
    LOCAL_CHANGES = "local_changes"
    REMOTE_AHEAD = "remote_ahead"
    DIVERGED = "diverged"
    LOCAL_ONLY_CLEAN = "local_only_clean"
    LOCAL_ONLY_DIRTY = "local_only_dirty"
    NETWORK_ERROR_CLEAN = "network_error_clean"
    NETWORK_ERROR_DIRTY = "network_error_dirty"


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
        "is_archived": None,
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
    except Exception:
        # No remote named "origin" configured
        return SyncStatus.LOCAL_ONLY_DIRTY if is_dirty else SyncStatus.LOCAL_ONLY_CLEAN

    try:
        origin.fetch()
    except Exception as e:
        # Remote exists but fetch failed (network error, auth failure, etc.)
        print(f"  Warning: could not fetch remote for {repo_path.name}: {e}")
        return SyncStatus.NETWORK_ERROR_DIRTY if is_dirty else SyncStatus.NETWORK_ERROR_CLEAN

    # Fetch succeeded -- compare local and remote
    try:
        active_branch = repo.active_branch
        tracking = active_branch.tracking_branch()
        if tracking:
            behind = list(repo.iter_commits(f"{active_branch}..{tracking}"))
            remote_ahead = len(behind) > 0
        else:
            remote_ahead = False
    except Exception:
        # Detached HEAD or other edge case after successful fetch
        return SyncStatus.LOCAL_CHANGES if is_dirty else SyncStatus.SYNCED

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


def _extract_github_owner_repo(repo_path: Path) -> str | None:
    """Extract 'owner/repo' from the origin remote URL of a git repository.

    Supports:
      - https://github.com/owner/repo.git
      - git@github.com:owner/repo.git
      - ssh://git@github.com/owner/repo.git

    Returns None if no origin remote, not a GitHub remote, or URL is malformed.
    """
    try:
        repo = Repo(repo_path)
        url = repo.remote("origin").url.strip()
    except Exception:
        return None

    patterns = [
        r"(?:https?://)?github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$",
        r"git@github\.com:([^/]+/[^/]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        m = re.match(pattern, url)
        if m:
            return m.group(1)
    return None


def _check_github_archived(owner_repo: str) -> bool | None:
    """Check if a GitHub repository is archived via the REST API.

    Args:
        owner_repo: GitHub repository in 'owner/repo' format.

    Returns:
        True if archived, False if not archived, None if the check failed.
    """
    headers = {"User-Agent": "oh-my-gitstats"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        resp = requests.get(
            f"https://api.github.com/repos/{owner_repo}",
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("archived", False)
        return None
    except requests.RequestException:
        return None


def _check_repo_archived(repo_path: Path) -> bool | None:
    """Check if a local git repo's GitHub mirror is archived.

    Returns True/False for the archived state, or None if it cannot be determined.
    """
    owner_repo = _extract_github_owner_repo(repo_path)
    if owner_repo is None:
        return None
    return _check_github_archived(owner_repo)


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
        "is_archived": data.get("is_archived"),
        "commits": all_commits,
    }


def sync_repos(data_dir: str, verbose: bool = True, check: bool = False) -> List[Path]:
    """Incrementally update existing JSON files with new commits.

    Args:
        data_dir: Directory containing existing JSON files.
        verbose: Whether to print progress messages.
        check: Whether to check GitHub archive status for each repo.

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

        # Check GitHub archive status if requested
        if check:
            archived = _check_repo_archived(repo_path)
            data["is_archived"] = archived
            if verbose:
                status_map = {True: "archived", False: "active", None: "unknown"}
                print(f"  GitHub status: {status_map.get(archived, 'unknown')}")

        # Fast skip: compare HEAD hash without opening GitPython
        stored_hash = data.get("last_commit_hash")
        current_hash = _read_head_hash(repo_path)
        has_new_commits = not (stored_hash and current_hash and stored_hash == current_hash)

        # Always refresh sync_status to recover from stale network errors
        new_sync_status = _get_sync_status(repo_path)
        sync_changed = data.get("sync_status") != new_sync_status.value

        if not has_new_commits and not sync_changed and not check:
            if verbose:
                print("  Skipped (no changes)")
            continue

        if has_new_commits:
            old_count = len(data.get("commits", []))
            try:
                updated = sync_repo_data(data)
                if check:
                    updated["is_archived"] = data.get("is_archived")
                filepath = save_repo_data(updated, data_path)
                saved_files.append(filepath)

                new_count = len(updated["commits"]) - old_count
                if verbose:
                    print(f"  +{new_count} new commits")
            except Exception as e:
                if verbose:
                    print(f"  Error: {e}")
        else:
            # No new commits but status or archive changed
            updated = dict(data)
            updated["sync_status"] = new_sync_status.value
            filepath = save_repo_data(updated, data_path)
            saved_files.append(filepath)
            if verbose:
                if sync_changed:
                    print(f"  Updated sync status: {new_sync_status.value}")
                else:
                    print("  Skipped (no new commits)")

    if verbose:
        print(f"\nSynced {len(saved_files)} repositories")

    return saved_files


def collect_all_repos(root_path: str, output_dir: str, verbose: bool = True, check: bool = False) -> List[Path]:
    """Collect commit data from all git repos under root_path.

    Args:
        root_path: Root directory to search for git repos.
        output_dir: Directory to save JSON files.
        verbose: Whether to print progress messages.
        check: Whether to check GitHub archive status for each repo.

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
            if check:
                archived = _check_repo_archived(repo_path)
                data["is_archived"] = archived
                if verbose:
                    status_map = {True: "archived", False: "active", None: "unknown"}
                    print(f"  GitHub status: {status_map.get(archived, 'unknown')}")
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

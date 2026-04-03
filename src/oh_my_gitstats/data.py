"""Data loading and aggregation utilities."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


def load_json_files(json_dir: str) -> List[Dict[str, Any]]:
    """Load all JSON files from a directory.

    Args:
        json_dir: Directory containing JSON files.

    Returns:
        List of repository data dictionaries.
    """
    data = []
    for filepath in Path(json_dir).glob("*.json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data.append(json.load(f))
    return data


def aggregate_by_period(
    commits: List[Dict[str, Any]],
    granularity: str,
    metric: str = "changes"
) -> Dict[str, int]:
    """Aggregate commit data by time period.

    Args:
        commits: List of commit dictionaries.
        granularity: Aggregation period (day/week/month).
        metric: "changes" for additions+deletions, "commits" for count.

    Returns:
        Dictionary mapping period string to aggregated value.
    """
    aggregated = defaultdict(int)

    for commit in commits:
        ts = datetime.fromisoformat(commit["timestamp"])
        value = 1 if metric == "commits" else commit["additions"] + commit["deletions"]

        if granularity == "day":
            key = ts.strftime("%Y-%m-%d")
        elif granularity == "week":
            monday = ts - timedelta(days=ts.weekday())
            key = monday.strftime("%Y-%m-%d")
        else:  # month
            key = ts.strftime("%Y-%m")

        aggregated[key] += value

    return aggregated


def get_date_range(all_data: List[Dict[str, Any]]) -> tuple[str, str]:
    """Get the overall date range from all repositories.

    Args:
        all_data: List of repository data.

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format.
    """
    all_dates = []
    for repo in all_data:
        for commit in repo["commits"]:
            ts = datetime.fromisoformat(commit["timestamp"])
            all_dates.append(ts.date())

    if not all_dates:
        today = datetime.now().date()
        return f"{today.year}-01-01", f"{today.year}-12-31"

    min_date = min(all_dates)
    max_date = max(all_dates)

    return min_date.strftime("%Y-%m-%d"), max_date.strftime("%Y-%m-%d")


def get_years_from_data(all_data: List[Dict[str, Any]]) -> List[str]:
    """Extract all unique years from the data.

    Args:
        all_data: List of repository data.

    Returns:
        List of year strings in descending order.
    """
    years = set()
    for repo in all_data:
        for commit in repo["commits"]:
            ts = datetime.fromisoformat(commit["timestamp"])
            years.add(str(ts.year))
    return sorted(years, reverse=True)


def rewrite_path(path: str) -> str:
    """Rewrite file path to use forward slashes for better compatibility."""
    return path.replace("\\", "/")

"""Visualization module for generating HTML charts from commit data."""

from datetime import datetime
from pathlib import Path

from jinja2 import Template

from .constants import SYNC_STATUS_INFO, SYNC_LEGEND
from .data import load_json_files, get_date_range, get_years_from_data, rewrite_path
from .charts import (
    build_line_js_obj,
    build_heatmap_js_obj,
    build_single_repo_line_js_obj,
    build_single_repo_heatmap_js_obj,
)


def _repo_stats(repo: dict) -> dict:
    """Compute summary stats for a single repo (used by the detail modal)."""
    commits = repo.get("commits", [])
    total_commits = len(commits)
    total_changes = sum(
        c.get("additions", 0) + c.get("deletions", 0) for c in commits
    )
    if commits:
        timestamps = [c["timestamp"] for c in commits]
        first = min(timestamps)[:10]
        last = max(timestamps)[:10]
    else:
        first = last = ""
    return {
        "total_commits": total_commits,
        "total_changes": total_changes,
        "first_commit": first,
        "last_commit": last,
    }


def generate_html(json_dir: str, output_path: str) -> str:
    """Generate a complete HTML file with all visualizations.

    Args:
        json_dir: Directory containing JSON files.
        output_path: Path to save the HTML file.

    Returns:
        Path to the generated HTML file.
    """
    all_data = load_json_files(json_dir)

    if not all_data:
        raise ValueError(f"No JSON files found in {json_dir}")

    date_range = get_date_range(all_data)
    years = get_years_from_data(all_data)

    this_year = str(datetime.now().year)
    default_year = this_year if this_year in years else "all"

    # Pre-compute all chart data
    line_js_obj = build_line_js_obj(all_data)
    heatmap_js_obj, active_repos_js_obj = build_heatmap_js_obj(all_data, date_range, years)
    single_repo_line_js_obj = build_single_repo_line_js_obj(all_data)
    single_repo_heatmap_js_obj = build_single_repo_heatmap_js_obj(all_data, date_range, years)

    # Get repo info for individual heatmaps
    repo_info = []
    for repo in all_data:
        commits = repo.get("commits", [])
        last_ts = commits[-1]["timestamp"] if commits else ""
        stats = _repo_stats(repo)
        repo_info.append({
            "name": repo["repo_name"],
            "path": repo.get("repo_path", ""),
            "sync_status": repo.get("sync_status", ""),
            "is_archived": repo.get("is_archived"),
            "last_commit": last_ts,
            "stats": stats,
        })

    # Load template from file
    template_path = Path(__file__).parent / "template.html"
    html_template = Template(template_path.read_text(encoding="utf-8"))

    # Generate chart IDs for individual heatmaps
    individual_charts_data = []
    for idx, repo in enumerate(repo_info):
        chart_id = f"individual-heatmap-{idx}"
        status = repo.get("sync_status", "")
        info = SYNC_STATUS_INFO.get(status, {}) if status else {}
        local = info.get("local", {}) if info else {}
        remote = info.get("remote", {}) if info else {}
        individual_charts_data.append({
            "id": chart_id,
            "index": idx,
            "name": repo["name"],
            "path": rewrite_path(repo["path"]),
            "sync_label": info.get("label", ""),
            "local_color": local.get("color", "#9ca3af"),
            "local_label": local.get("label", ""),
            "remote_color": remote.get("color", "#9ca3af"),
            "remote_label": remote.get("label", ""),
            "is_archived": repo.get("is_archived"),
            "last_commit": repo.get("last_commit", ""),
            "stats": repo["stats"],
        })

    # Render HTML
    html_content = html_template.render(
        line_js_obj=line_js_obj,
        heatmap_js_obj=heatmap_js_obj,
        active_repos_js_obj=active_repos_js_obj,
        single_repo_line_js_obj=single_repo_line_js_obj,
        single_repo_heatmap_js_obj=single_repo_heatmap_js_obj,
        years=years,
        individual_charts=individual_charts_data,
        sync_legend=SYNC_LEGEND,
        current_year=default_year,
        generated_date=datetime.now().strftime("%Y-%m-%d"),
        repo_count=len(all_data),
        date_range=date_range,
    )

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding="utf-8")

    return str(output_file)

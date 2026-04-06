"""Visualization module for generating HTML charts from commit data."""

from datetime import datetime
from pathlib import Path

from jinja2 import Template

from .constants import SYNC_STATUS_INFO
from .data import load_json_files, get_date_range, get_years_from_data, rewrite_path
from .charts import build_line_js_obj, build_heatmap_js_obj


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

    # Get repo info for individual heatmaps
    repo_info = [
        {
            "name": repo["repo_name"],
            "path": repo.get("repo_path", ""),
            "sync_status": repo.get("sync_status", ""),
            "is_archived": repo.get("is_archived"),
        }
        for repo in all_data
    ]

    # Load template from file
    template_path = Path(__file__).parent / "template.html"
    html_template = Template(template_path.read_text(encoding="utf-8"))

    # Generate chart IDs for individual heatmaps
    individual_charts_data = []
    for idx, repo in enumerate(repo_info):
        chart_id = f"individual-heatmap-{idx}"
        status = repo.get("sync_status", "")
        info = SYNC_STATUS_INFO.get(status, {}) if status else {}
        individual_charts_data.append({
            "id": chart_id,
            "name": repo["name"],
            "path": rewrite_path(repo["path"]),
            "sync_emoji": info.get("emoji", ""),
            "sync_label": info.get("label", ""),
            "is_archived": repo.get("is_archived"),
        })

    # Render HTML
    html_content = html_template.render(
        line_js_obj=line_js_obj,
        heatmap_js_obj=heatmap_js_obj,
        active_repos_js_obj=active_repos_js_obj,
        years=years,
        individual_charts=individual_charts_data,
        sync_legend=[
            {"emoji": v["emoji"], "label": v["label"]}
            for v in SYNC_STATUS_INFO.values()
        ],
        current_year=default_year
    )

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding="utf-8")

    return str(output_file)

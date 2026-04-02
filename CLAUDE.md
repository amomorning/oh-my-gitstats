# oh-my-gitstats

Python CLI tool that batch-collects git commit data from multiple repositories and visualizes it as a single interactive HTML file.

## Directory Structure

```
oh-my-gitstats/
├── CLAUDE.md                      # This file
├── pyproject.toml                 # Project config, dependencies, entry point
├── README.md                      # User documentation
├── data/                          # Collected JSON data (one file per repo)
├── output/                        # Generated HTML visualizations
└── src/oh_my_gitstats/
    ├── __init__.py                # Package init, version
    ├── cli.py                     # Click CLI entry point (collect / visualize)
    ├── collector.py               # Git data extraction via GitPython
    └── visualizer.py              # HTML chart generation via pyecharts + Jinja2
```

## CLI Commands

```bash
# Editable install
pip install -e .

# Collect commit data from all repos under a directory
gitstats collect /path/to/repos --output ./data

# Generate HTML visualization
gitstats visualize ./data --output ./output/stats.html --granularity week
```

Entry point defined in `pyproject.toml`: `gitstats = "oh_my_gitstats.cli:main"`

## Source Files

### `cli.py`

Click group with two subcommands:

- `collect` — scans directory recursively for `.git`, extracts commits, saves JSON
- `visualize` — reads JSON files, generates single HTML with ECharts

### `collector.py`

Key functions:

- `find_git_repos(root_path)` → `List[Path]` — recursive `.git` search
- `extract_commit_data(repo_path)` → `Dict` — extracts commits with timestamp/additions/deletions
- `save_repo_data(data, output_dir)` → `Path` — writes one JSON per repo
- `collect_all_repos(root_path, output_dir)` → `List[Path]` — main collection entry point

### `visualizer.py`

Key functions:

- `load_json_files(json_dir)` — loads all `*.json` from a directory
- `aggregate_by_period(commits, granularity)` — groups by day/week/month
- `get_date_range(all_data)` / `get_years_from_data(all_data)` — date helpers
- `build_daily_repo_map(all_data)` — date → [{name, changes}] mapping for heatmap tooltips
- `create_line_chart_for_range(all_data, granularity, date_range)` → JSON string
- `create_aggregate_heatmap_for_range(all_data, date_range)` → JSON string
- `create_individual_heatmap_for_range(all_data, date_range)` → `List[str]`
- `generate_html(json_dir, output_path, granularity)` — main entry, builds complete HTML

## JSON Data Format

Each file in `data/` is named `{repo_name}.json`:

```json
{
  "repo_name": "my-project",
  "repo_path": "/absolute/path/to/my-project",
  "commits": [
    {
      "timestamp": "2024-01-15T10:30:00+08:00",
      "additions": 45,
      "deletions": 12
    }
  ]
}
```

## Dependencies

- **click** (≥8.0) — CLI framework
- **gitpython** (≥3.1) — git repository parsing
- **pyecharts** (≥2.0) — ECharts chart generation
- **jinja2** (≥3.0) — HTML templating

## pyecharts Pitfalls

1. **`type_` suffix**: Many pyecharts option classes use `type_=` (with underscore) instead of `type=` to avoid conflicting with Python's builtin. Applies to `AxisOpts`, `DataZoomOpts`, `LegendOpts`, etc.

2. **`dump_options()` vs `render_embed()`**: Use `chart.dump_options()` to get chart config as a JSON string. Then manually create `<script>` blocks with `echarts.init()` + `chart.setOption()`. Do NOT use `render_embed()` with `js_host` — it produces invalid JS in static HTML.

3. **`JsCode` in nested contexts**: `JsCode` is rendered as raw JS by `dump_options()`. When embedding chart options inside a larger JavaScript object (via string concatenation), the raw function body is fine, but do NOT embed `json.dumps()` output inside a `JsCode` string — the `\"` escapes will cause syntax errors. Instead, pass data as a separate JS global variable and reference it from the formatter function.

4. **`GridOpts`**: Not accepted by `set_global_opts()`. Use `legend_opts` positioning or chart-level `InitOpts` to control layout instead.

5. **`Page._charts`**: Access individual charts in a `Page` via `Page._charts` (list), then call `.dump_options()` on each.

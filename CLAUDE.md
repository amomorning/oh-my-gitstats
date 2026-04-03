# oh-my-gitstats

Python CLI tool that batch-collects git commit data from multiple repositories and visualizes it as a single interactive HTML file.

## Directory Structure

```text
oh-my-gitstats/
├── CLAUDE.md                      # This file
├── pyproject.toml                 # Project config, dependencies, entry point
├── README.md                      # User documentation
├── data/                          # Collected JSON data (one file per repo)
├── output/                        # Generated HTML visualizations
└── src/oh_my_gitstats/
    ├── __init__.py                # Package init, version
    ├── cli.py                     # Click CLI entry point (collect / sync / visualize)
    ├── collector.py               # Git data extraction via GitPython
    ├── constants.py               # Shared constants (metrics, colors, sync status)
    ├── data.py                    # JSON loading, date helpers, aggregation
    ├── charts.py                  # pyecharts chart building + JS object assembly
    ├── template.html              # Jinja2 HTML template for the output page
    └── visualizer.py              # Orchestration: generate_html entry point
```

## CLI Commands

```bash
# Editable install
pip install -e .

# Collect commit data from all repos under a directory
gitstats collect /path/to/repos --output ./data

# Incrementally update existing JSON files (only new commits)
gitstats sync ./data

# Generate HTML visualization
gitstats visualize ./data --output ./output/stats.html
```

Entry point defined in `pyproject.toml`: `gitstats = "oh_my_gitstats.cli:main"`

## Source Files

### `cli.py`

Click group with three subcommands:

- `collect` — scans directory recursively for `.git`, extracts commits, saves JSON. Options: `--output` (default `./data`), `--quiet` (suppress output).
- `sync` — incrementally updates existing JSON files in a data directory. Only fetches commits newer than the latest commit already recorded. Skips repos whose directory no longer exists. Options: `--quiet`.
- `visualize` — reads JSON files, generates single HTML with ECharts. Options: `--output` (default `./output/stats.html`). Granularity and metric selection are handled in-browser via JS dropdowns.

### `collector.py`

Module-level enum:

- `SyncStatus(str, Enum)` — 6 possible values: `synced`, `local_changes`, `remote_ahead`, `diverged`, `local_only_clean`, `local_only_dirty`

Key functions:

- `find_git_repos(root_path)` → `List[Path]` — recursive `.git` search
- `extract_commit_data(repo_path)` → `Dict` — extracts commits with timestamp/additions/deletions + sync status
- `_get_sync_status(repo_path)` → `SyncStatus` — private helper, checks dirty state and fetches remote to determine sync status
- `_parse_commit(commit)` → `Dict[str, Any]` — private helper, parses a single GitPython Commit object
- `save_repo_data(data, output_dir)` → `Path` — writes one JSON per repo
- `sync_repo_data(data)` → `Dict` — incrementally updates a single repo's data (new commits only, refreshed sync status)
- `sync_repos(data_dir, verbose=True)` → `List[Path]` — incremental sync entry point; reads existing JSON files, updates each with new commits
- `collect_all_repos(root_path, output_dir, verbose=True)` → `List[Path]` — full collection entry point

### `constants.py`

Module-level constants:

- `METRICS = ("changes", "commits")` — supported metric types
- `GRANULARITIES = ("day", "week", "month")` — supported time granularities
- `COLORS` — list of 10 hex color strings for chart series
- `SYNC_STATUS_INFO` — dict mapping sync status strings to `{emoji, label}` dicts

### `data.py`

Pure data manipulation functions (no chart library dependency):

- `load_json_files(json_dir)` — loads all `*.json` from a directory
- `aggregate_by_period(commits, granularity, metric="changes")` — groups by day/week/month; metric `"changes"` sums additions+deletions, `"commits"` counts commits
- `get_date_range(all_data)` → `tuple[str, str]` — overall (min_date, max_date)
- `get_years_from_data(all_data)` → `List[str]` — unique years in descending order
- `rewrite_path(path)` → `str` — replaces backslashes with forward slashes

### `charts.py`

pyecharts chart building and JS object assembly:

- `build_line_opts(all_data, granularity, metric)` → JSON string — builds Line chart options
- `build_agg_heatmap_opts(all_data, date_range, metric)` → JSON string — builds aggregate Calendar heatmap options
- `build_ind_heatmap_opts(all_data, date_range, metric)` → `List[str]` — builds individual Calendar heatmap options per repo
- `build_line_js_obj(all_data)` → JS object string — pre-computes all metric×granularity combinations (6 charts) as embedded JS
- `build_heatmap_js_obj(all_data, date_range, years)` → JS object string — pre-computes all metric×year-range combinations as embedded JS

### `template.html`

Jinja2 HTML template loaded at runtime by `visualizer.py`. Contains CSS styles, HTML structure with three card sections (Line Chart, Aggregate Heatmap, Individual Heatmaps), and client-side JavaScript for chart initialization and interactive controls.

### `visualizer.py`

Single public function:

- `generate_html(json_dir, output_path)` → `str` — orchestrates the full pipeline: load data → compute charts → render template → write file

### Architecture: Pre-computation Strategy

All metric×granularity combinations are pre-computed at HTML generation time and embedded as JavaScript global objects. Users switch between them dynamically in the browser via dropdown controls — no page reload needed.

The generated HTML provides:

1. **Line Chart** — metric dropdown (Lines Changed / Commit Count) + granularity dropdown (Day/Week/Month)
2. **Aggregate Heatmap** — year selector dropdown (All Years / specific year)
3. **Individual Heatmaps** — CSS grid of per-repo calendar charts with sync status emoji, year selector and "Open Folder" button (`vscode://file/` URI)

## JSON Data Format

Each file in `data/` is named `{repo_name}.json`:

```json
{
  "repo_name": "my-project",
  "repo_path": "/absolute/path/to/my-project",
  "sync_status": "synced",
  "commits": [
    {
      "timestamp": "2024-01-15T10:30:00+08:00",
      "additions": 45,
      "deletions": 12
    }
  ]
}
```

`sync_status` values: `synced` | `local_changes` | `remote_ahead` | `diverged` | `local_only_clean` | `local_only_dirty`

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

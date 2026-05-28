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
    ├── cli.py                     # Click CLI entry point (collect / sync / visualize / auto)
    ├── collector.py               # Git data extraction via GitPython
    ├── constants.py               # Shared constants (metrics, colors, sync status)
    ├── data.py                    # JSON loading, date helpers, aggregation
    ├── charts.py                  # pyecharts chart building + JS object assembly
    ├── settings.py                # Settings management (~/.gitstats/settings.json)
    ├── template.html              # Jinja2 HTML template for the output page
    └── visualizer.py              # Orchestration: generate_html entry point
```

## CLI Commands

```bash
# Editable install
pip install -e .

# One-step: collect + sync + visualize + open browser
gitstats auto

# Collect commit data from all repos under a directory
gitstats collect /path/to/repos

# Incrementally update existing JSON files (only new commits)
gitstats sync

# Generate HTML visualization
gitstats visualize
```

Default data directory: `~/.gitstats/data`. Default output: `~/.gitstats/stats.html`.

Entry point defined in `pyproject.toml`: `gitstats = "oh_my_gitstats.cli:main"`

## Settings

Configuration file at `~/.gitstats/settings.json` (auto-created on first run):

```json
{
  "data_dir": "~/.gitstats/data",
  "output_html": "~/.gitstats/stats.html",
  "collect_paths": []
}
```

- `data_dir` — where JSON files are stored (default `~/.gitstats/data`)
- `output_html` — where HTML visualization is generated (default `~/.gitstats/stats.html`)
- `collect_paths` — list of parent directories for `gitstats auto` to scan

## Source Files

### `cli.py`

Click group with four subcommands. Uses a custom `MainGroup` class that calls `init_default_settings()` before each command to ensure `~/.gitstats/settings.json` exists.

- `collect` — scans directory recursively for `.git`, extracts commits, saves JSON. Options: `--output` (default from settings `data_dir`), `--quiet`, `--skip`, `--check`.
- `sync` — incrementally updates existing JSON files. Optional `data_dir` argument (default from settings `data_dir`). Options: `--quiet`, `--check`.
- `visualize` — reads JSON files, generates single HTML with ECharts. Optional `json_dir` argument (default from settings `data_dir`). Options: `--output` (default from settings `output_html`).
- `auto` — one-step: collect (skip mode) → sync → visualize → open browser. Reads `collect_paths` from settings. Options: `--quiet`, `--check`, `--no-open`.

### `settings.py`

Settings management module. Module-level constants: `GITSTATS_DIR`, `SETTINGS_PATH`, `DEFAULT_SETTINGS`.

- `load_settings()` → `dict` — reads `settings.json`, merges with defaults, expands `~` in paths. Returns dict with `Path` objects for `data_dir`/`output_html` and `list[str]` for `collect_paths`.
- `save_settings(settings)` — writes settings to disk.
- `init_default_settings()` — creates default `settings.json` if missing.

### `collector.py`

Module-level enum:

- `SyncStatus(str, Enum)` — 6 possible values: `synced`, `local_changes`, `remote_ahead`, `diverged`, `local_only_clean`, `local_only_dirty`

Key functions:

- `find_git_repos(root_path)` → `List[Path]` — recursive `.git` search
- `extract_commit_data(repo_path)` → `Dict` — extracts commits with timestamp/additions/deletions + sync status + HEAD hash
- `_get_sync_status(repo_path)` → `SyncStatus` — private helper, checks dirty state and fetches remote to determine sync status
- `_read_head_hash(repo_path)` → `str | None` — private helper, reads HEAD commit hash directly from `.git` files (no GitPython)
- `_parse_commit(commit)` → `Dict[str, Any]` — private helper, parses a single GitPython Commit object
- `save_repo_data(data, output_dir)` → `Path` — writes one JSON per repo
- `sync_repo_data(data)` → `Dict` — incrementally updates a single repo's data (new commits only, refreshed sync status)
- `sync_repos(data_dir, verbose=True, check=False)` → `List[Path]` — incremental sync entry point; reads existing JSON files, skips repos with unchanged HEAD hash, updates the rest with new commits. When `check=True`, queries GitHub API for archive status.
- `_extract_github_owner_repo(repo_path)` → `str | None` — extracts `owner/repo` from origin remote URL
- `_check_github_archived(owner_repo)` → `bool | None` — checks GitHub API for archive status; supports `GITHUB_TOKEN` env var
- `_check_repo_archived(repo_path)` → `bool | None` — combines the two functions above
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
3. **Individual Heatmaps** — CSS grid of per-repo calendar charts with sync status emoji, year selector and "Continue" / "Archived" button (`vscode://file/` URI)

## JSON Data Format

Each file in `data/` is named `{repo_name}.json`:

```json
{
  "repo_name": "my-project",
  "repo_path": "/absolute/path/to/my-project",
  "last_commit_hash": "a1b2c3d4...",
  "sync_status": "synced",
  "is_archived": false,
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

`is_archived` values: `true` | `false` | `null` (not checked or check failed). Set by `sync --check` via GitHub API. Supports `GITHUB_TOKEN` env var for private repos.

## Dependencies

- **click** (≥8.0) — CLI framework
- **gitpython** (≥3.1) — git repository parsing
- **pyecharts** (≥2.0) — ECharts chart generation
- **jinja2** (≥3.0) — HTML templating
- **requests** (≥2.28) — GitHub API queries for archive status

## pyecharts Pitfalls

1. **`type_` suffix**: Many pyecharts option classes use `type_=` (with underscore) instead of `type=` to avoid conflicting with Python's builtin. Applies to `AxisOpts`, `DataZoomOpts`, `LegendOpts`, etc.

2. **`dump_options()` vs `render_embed()`**: Use `chart.dump_options()` to get chart config as a JSON string. Then manually create `<script>` blocks with `echarts.init()` + `chart.setOption()`. Do NOT use `render_embed()` with `js_host` — it produces invalid JS in static HTML.

3. **`JsCode` in nested contexts**: `JsCode` is rendered as raw JS by `dump_options()`. When embedding chart options inside a larger JavaScript object (via string concatenation), the raw function body is fine, but do NOT embed `json.dumps()` output inside a `JsCode` string — the `\"` escapes will cause syntax errors. Instead, pass data as a separate JS global variable and reference it from the formatter function.

4. **`GridOpts`**: Not accepted by `set_global_opts()`. Use `legend_opts` positioning or chart-level `InitOpts` to control layout instead.

5. **`Page._charts`**: Access individual charts in a `Page` via `Page._charts` (list), then call `.dump_options()` on each.

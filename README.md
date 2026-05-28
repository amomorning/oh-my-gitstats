<div align="center">

# 📊 oh-my-gitstats

[中文](https://github.com/amomorning/oh-my-gitstats/blob/main/README.zh-CN.md) | English

A Python CLI tool for collecting git commit statistics and visualizing them as interactive HTML charts.

</div>

![Line Chart](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/linechart.png)
![Heatmap](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/heatmap.png)

## ✨ Features

- 🔍 **Batch Collection** — Scan multiple git repositories recursively
- ⚡ **Incremental Sync** — Only fetch new commits since last collection
- 🚀 **One-Step Workflow** — `gitstats auto` does everything in one command
- 📈 **Line Charts** — Track changes over time with metric & granularity switching
- 🗓️ **Calendar Heatmaps** — Visualize commit activity with year-based filtering
- 🎯 **Aggregated & Individual Views** — See combined or per-repo statistics
- 📂 **VS Code Integration** — Open repo folders directly from the HTML report

## 🚀 Installation

```bash
pip install oh-my-gitstats
```

Or install from source:

```bash
git clone https://github.com/amomorning/oh-my-gitstats.git
cd oh-my-gitstats
pip install -e .
```

## ⚡ Quick Start

**First time**, collect from each project directory (paths are auto-recorded in config):

```bash
cd ~/projects && gitstats collect .
cd ~/work && gitstats collect .
```

**After that**, one command does collect → sync → visualize → open browser:

```bash
gitstats auto
```

You can also manually edit the config file to add directories:

```bash
# The config file is auto-created at:
~/.gitstats/settings.json
```

```json
{
  "collect_paths": [
    "/home/user/projects",
    "/home/user/work"
  ]
}
```

**Options:**

| Option | Description |
|--------|-------------|
| `-q, --quiet` | Suppress output messages |
| `--check` | Check GitHub archive status (requires network; set `GITHUB_TOKEN` for private repos) |
| `--no-open` | Do not open the HTML file in browser after generation |

## 📖 Commands

### `collect` — Collect Commit Data

Scan a directory for git repositories and export to JSON:

```bash
gitstats collect /path/to/repos
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Directory to save JSON files (default: `~/.gitstats/data`) |
| `-q, --quiet` | Suppress output messages |
| `--skip` | Skip repos that already have a JSON file |
| `--check` | Check GitHub archive status |

### `sync` — Incremental Sync

Update existing JSON files with only new commits — much faster than re-collecting:

```bash
gitstats sync
```

| Option       | Description                     |
|--------------|---------------------------------|
| `-q, --quiet` | Suppress output messages       |
| `--check`    | Check GitHub archive status     |

Typical workflow with multiple directories:

```bash
# One-time: collect from different locations
gitstats collect /path/to/work-projects
gitstats collect /path/to/personal-projects --skip

# Later: update all at once
gitstats sync
```

### `visualize` — Generate Visualization

Create an interactive HTML file from collected data:

```bash
gitstats visualize
```

| Option       | Description                                        |
|--------------|----------------------------------------------------|
| `-o, --output` | HTML file path (default: `~/.gitstats/stats.html`) |

Granularity and metric can be switched dynamically in the generated HTML — no need to regenerate.

## ⚙️ Configuration

Config file at `~/.gitstats/settings.json` (auto-created on first run):

```json
{
  "data_dir": "~/.gitstats/data",
  "output_html": "~/.gitstats/stats.html",
  "collect_paths": []
}
```

| Field           | Description                                                                      |
|-----------------|----------------------------------------------------------------------------------|
| `data_dir`      | Where JSON files are stored                                                      |
| `output_html`   | Where HTML visualization is generated                                            |
| `collect_paths` | Directories for `gitstats auto` to scan (auto-populated when you run `collect`)  |

## 🔑 GitHub Token (Optional)

`--check` queries the GitHub API to check archive status. Without authentication, only **public repositories** can be checked (rate limit: 60 requests/hour).

> If `GITHUB_TOKEN` is not set, a warning will be printed when using `--check`.

To check **private repositories**, set the `GITHUB_TOKEN` environment variable:

### Linux / macOS

```bash
export GITHUB_TOKEN=ghp_your_token_here
gitstats sync --check
```

### Windows (PowerShell)

Set for current session:

```powershell
$env:GITHUB_TOKEN="ghp_your_token_here"
gitstats sync --check
```

Set permanently: **Settings** → **System** → **About** → **Advanced system settings** → **Environment Variables** → User variables → **New**

### How to get a token

1. Go to **GitHub** → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a name (e.g. `oh-my-gitstats`)
4. Under **Select scopes**, no additional scopes are needed for public repos
5. To access **private repositories**, check the `repo` scope
6. Click **Generate token** and copy the value (starts with `ghp_`)

> **Note:** Use **Tokens (classic)**, not Fine-grained tokens. With a token, the rate limit increases to 5,000 requests/hour.

## 📁 Output

The generated HTML contains:

1. **📈 Line Chart** — Changes over time with metric selector (Lines Changed / Commit Count) and granularity selector (Day/Week/Month). Click legend to toggle projects.

2. **🗓️ Aggregate Heatmap** — Combined activity across all repos with year selector (All Years / specific year).

3. **📊 Individual Heatmaps** — Per-repository calendar views in a responsive grid, each with sync status indicator and a "Continue" / "Archived" button to open in VS Code.

![Individual Heatmaps](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/repo.png)

## 📋 JSON Format

Each repository generates a JSON file (`~/.gitstats/data/{repo_name}.json`):

```json
{
  "repo_name": "my-project",
  "repo_path": "/absolute/path/to/my-project",
  "last_commit_hash": "a1b2c3d4...",
  "sync_status": "synced",
  "is_archived": false,
  "commits": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "additions": 45,
      "deletions": 12
    }
  ]
}
```

**`last_commit_hash`** — HEAD hash at collection time. During `sync`, repos with a matching hash are skipped instantly.

**`sync_status`** — Sync state with remote:

| Status | Description |
| ------ | ----------- |
| ✅ `synced` | In sync with remote |
| ✏️ `local_changes` | Local has uncommitted changes, remote is up-to-date |
| ⬇️ `remote_ahead` | Local is clean, but remote has new commits |
| ⚠️ `diverged` | Local has uncommitted changes and remote has new commits |
| 🔒 `local_only_clean` | No remote configured, local is clean |
| 🔧 `local_only_dirty` | No remote configured, local has uncommitted changes |
| ⚠️ `network_error_clean` | Remote exists but fetch failed, local is clean |
| ⚠️ `network_error_dirty` | Remote exists but fetch failed, local has uncommitted changes |

**`is_archived`** — Whether the repo is archived on GitHub (set by `--check`). Values: `true`, `false`, or `null` (not checked). Archived repos show a grayed-out "Archived" button.

## 🔧 Requirements

- Python 3.9+
- click, gitpython, pyecharts, jinja2, requests

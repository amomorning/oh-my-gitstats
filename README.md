<div align="center">



# 📊 oh-my-gitstats

[中文](https://github.com/amomorning/oh-my-gitstats/blob/main/README.zh-CN.md) | English

A Python CLI tool for collecting git commit statistics and visualizing them as interactive HTML charts.

</div>

![Line Chart](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/linechart.png)
![Heatmap](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/heatmap.png)

## ✨ Features

- 🔍 **Batch Collection** - Scan multiple git repositories recursively
- ⚡ **Incremental Sync** - Only fetch new commits since last collection
- 📈 **Line Charts** - Track changes over time with metric & granularity switching
- 🗓️ **Calendar Heatmaps** - Visualize commit activity with year-based filtering
- 🎯 **Aggregated & Individual Views** - See combined or per-repo statistics
- 📂 **VS Code Integration** - Open repo folders directly from the HTML report

## 🚀 Installation

### From PyPI (Recommended)

```bash
pip install oh-my-gitstats
```

### From Source (Development)

```bash
git clone https://github.com/amomorning/oh-my-gitstats.git
cd oh-my-gitstats
pip install -e .
```

## 📖 Usage

### 1️⃣ Collect Commit Data

Scan a directory for git repositories and export to JSON:

```bash
gitstats collect /path/to/repos --output ./data
```

**Options:**

| Option | Description |
|--------|-------------|
| `-o, --output` | Directory to save JSON files (default: `./data`) |
| `-q, --quiet` | Suppress output messages |
| `--check` | Check GitHub archive status for each repository |

### 2️⃣ Incremental Sync

You may collect repos from multiple locations into the same `data` directory. Re-running `collect` on every location is slow — `sync` reads the existing JSON files and only fetches new commits for each repo:

```bash
# Collect from multiple locations (one-time)
gitstats collect /path/to/work-projects --output ./data
gitstats collect /path/to/personal-projects --output ./data

# Later, update all at once — only new commits
gitstats sync ./data
```

**Options:**

| Option | Description |
|--------|-------------|
| `-q, --quiet` | Suppress output messages |
| `--check` | Check GitHub archive status for each repository |

### 3️⃣ Generate Visualization

Create an interactive HTML file from collected data:

```bash
gitstats visualize ./data --output ./output/stats.html
```

**Options:**

| Option | Description |
|--------|-------------|
| `-o, --output` | HTML file path (default: `./output/stats.html`) |

Granularity and metric can be switched dynamically in the generated HTML — no need to regenerate.

## 📁 Output

The generated HTML contains:

1. **📈 Line Chart** - Changes over time with metric selector (Lines Changed / Commit Count) and granularity selector (Day/Week/Month). Click legend to toggle projects.

2. **🗓️ Aggregate Heatmap** - Combined activity across all repos with year selector (All Years / specific year).

3. **📊 Individual Heatmaps** - Per-repository calendar views in a responsive grid, each with sync status indicator and a "Continue" / "Archived" button to open in VS Code.

![alt text](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/repo.png)


## 📋 JSON Format

Each repository generates a JSON file:

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

The `last_commit_hash` field stores the HEAD commit hash at collection time. During `sync`, repositories with a matching hash are skipped instantly — no git operations needed.

The `sync_status` field indicates the repository's sync state with its remote:

| Status | Description |
| ------ | ----------- |
| ✅ `synced` | In sync with remote |
| ✏️ `local_changes` | Local has uncommitted changes, remote is up-to-date |
| ⬇️ `remote_ahead` | Local is clean, but remote has new commits |
| ⚠️ `diverged` | Local has uncommitted changes and remote has new commits |
| 🔒 `local_only_clean` | No remote configured, local is clean |
| 🔧 `local_only_dirty` | No remote configured, local has uncommitted changes |

The `is_archived` field indicates whether the repository is archived on GitHub. Set by `sync --check`. Values: `true` (archived), `false` (active), `null` (not checked or check failed). Archived repos show a grayed-out "Archived" button in the visualization.

## 🔑 GitHub Token (Optional)

`sync --check` queries the GitHub API to check archive status. Without authentication, only **public repositories** can be checked (rate limit: 60 requests/hour).

To check **private repositories**, set the `GITHUB_TOKEN` environment variable:

### Linux / macOS

```bash
export GITHUB_TOKEN=ghp_your_token_here
gitstats sync ./data --check
```

### Windows (PowerShell)

Set for current session:

```powershell
$env:GITHUB_TOKEN="ghp_your_token_here"
gitstats sync ./data --check
```

Set permanently via GUI: **Settings** → **System** → **About** → **Advanced system settings** → **Environment Variables** → User variables → **New**

Verify the value:

```powershell
echo $env:GITHUB_TOKEN
```

### How to get a token

1. Go to **GitHub** → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a name (e.g. `oh-my-gitstats`)
4. Under **Select scopes**, no additional scopes are needed (public repo access is default)
5. To access **private repositories**, check the `repo` scope
6. Click **Generate token** and copy the value (starts with `ghp_`)

> **Note:** Use **Tokens (classic)**, not Fine-grained tokens.

> With a token, the rate limit increases to 5,000 requests/hour.

## 🔧 Requirements

- Python 3.9+
- click
- gitpython
- pyecharts
- jinja2
- requests

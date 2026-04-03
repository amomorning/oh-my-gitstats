# 📊 oh-my-gitstats

A Python CLI tool for collecting git commit statistics and visualizing them as interactive HTML charts.

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
git clone https://github.com/yourusername/oh-my-gitstats.git
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

3. **📊 Individual Heatmaps** - Per-repository calendar views in a responsive grid, each with sync status indicator and an "Open Folder" button to open in VS Code.

## 📋 JSON Format

Each repository generates a JSON file:

```json
{
  "repo_name": "my-project",
  "repo_path": "/absolute/path/to/my-project",
  "sync_status": "synced",
  "commits": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "additions": 45,
      "deletions": 12
    }
  ]
}
```

The `sync_status` field indicates the repository's sync state with its remote:

| Status | Description |
| ------ | ----------- |
| `synced` | In sync with remote |
| `local_changes` | Local has uncommitted changes, remote is up-to-date |
| `remote_ahead` | Local is clean, but remote has new commits |
| `diverged` | Local has uncommitted changes and remote has new commits |
| `local_only_clean` | No remote configured, local is clean |
| `local_only_dirty` | No remote configured, local has uncommitted changes |

## 🔧 Requirements

- Python 3.9+
- click
- gitpython
- pyecharts
- jinja2

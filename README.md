# 📊 oh-my-gitstats

A Python CLI tool for collecting git commit statistics and visualizing them as interactive HTML charts.

## ✨ Features

- 🔍 **Batch Collection** - Scan multiple git repositories recursively
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

### 2️⃣ Generate Visualization

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

3. **📊 Individual Heatmaps** - Per-repository calendar views in a responsive grid, each with an "Open Folder" button to open in VS Code.

## 📋 JSON Format

Each repository generates a JSON file:

```json
{
  "repo_name": "my-project",
  "repo_path": "/absolute/path/to/my-project",
  "commits": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "additions": 45,
      "deletions": 12
    }
  ]
}
```

## 🔧 Requirements

- Python 3.9+
- click
- gitpython
- pyecharts
- jinja2

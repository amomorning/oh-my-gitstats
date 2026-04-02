# 📊 oh-my-gitstats

A Python CLI tool for collecting git commit statistics and visualizing them as interactive HTML charts.

## ✨ Features

- 🔍 **Batch Collection** - Scan multiple git repositories recursively
- 📈 **Line Charts** - Track changes over time with clickable legends
- 🗓️ **Calendar Heatmaps** - Visualize commit activity at a glance
- 🎯 **Aggregated & Individual Views** - See combined or per-repo statistics

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
| `-g, --granularity` | Time aggregation: `day`, `week`, `month` (default: `week`) |

## 📁 Output

The generated HTML contains:

1. **📈 Line Chart** - Changes over time, click legend to toggle projects
2. **🗓️ Aggregate Heatmap** - Combined activity across all repos
3. **📊 Individual Heatmaps** - Per-repository calendar views

## 📋 JSON Format

Each repository generates a JSON file:

```json
{
  "repo_name": "my-project",
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

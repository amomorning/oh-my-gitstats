<div align="center">



# 📊 oh-my-gitstats

中文 | [English](https://github.com/amomorning/oh-my-gitstats/blob/main/README.md)

一个 Python CLI 工具，用于批量收集 git commit 统计数据并生成交互式 HTML 图表。

</div>

![折线图](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/linechart.png)
![热力图](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/heatmap.png)

## ✨ 功能

- 🔍 **批量收集** - 递归扫描目录下的所有 git 仓库
- ⚡ **增量同步** - 仅获取上次采集之后的新 commit
- 📈 **折线图** - 支持切换指标和时间粒度查看变化趋势
- 🗓️ **日历热力图** - 按年份筛选查看提交活跃度
- 🎯 **聚合 & 独立视图** - 查看所有仓库汇总或单仓库统计
- 📂 **VS Code 集成** - 从 HTML 报告中直接打开仓库文件夹

## 🚀 安装

### 从 PyPI 安装（推荐）

```bash
pip install oh-my-gitstats
```

### 从源码安装（开发）

```bash
git clone https://github.com/amomorning/oh-my-gitstats.git
cd oh-my-gitstats
pip install -e .
```

## 📖 使用

### 1️⃣ 收集 Commit 数据

扫描目录下的 git 仓库，导出为 JSON：

```bash
gitstats collect /path/to/repos --output ./data
```

**选项：**

| 选项 | 说明 |
|------|------|
| `-o, --output` | JSON 文件保存目录（默认 `./data`） |
| `-q, --quiet` | 静默模式，不输出提示信息 |

### 2️⃣ 增量同步

你可以将不同位置的仓库收集到同一个 `data` 目录。每次重新 `collect` 所有位置很慢，`sync` 直接读取已有 JSON，仅获取每个仓库的新 commit：

```bash
# 一次性从多个位置收集
gitstats collect /path/to/work-projects --output ./data
gitstats collect /path/to/personal-projects --output ./data

# 之后一键更新 — 只获取新 commit
gitstats sync ./data
```

**选项：**

| 选项 | 说明 |
|------|------|
| `-q, --quiet` | 静默模式，不输出提示信息 |
| `--check` | 检查 GitHub 仓库归档状态 |

### 3️⃣ 生成可视化

从已收集的数据生成交互式 HTML 文件：

```bash
gitstats visualize ./data --output ./output/stats.html
```

**选项：**

| 选项 | 说明 |
|------|------|
| `-o, --output` | HTML 文件路径（默认 `./output/stats.html`） |

生成的 HTML 支持在浏览器中动态切换粒度和指标，无需重新生成。

## 📁 输出

生成的 HTML 包含：

1. **📈 折线图** - 支持指标切换（代码行变更 / 提交次数）和粒度切换（天 / 周 / 月），点击图例可显示/隐藏项目。

2. **🗓️ 聚合热力图** - 所有仓库的汇总活跃度，支持年份选择（全部年份 / 指定年份）。

3. **📊 独立热力图** - 每个仓库的日历视图，网格布局排列，显示同步状态指示器和"Continue" / "Archived"按钮（在 VS Code 中打开）。

![alt text](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/repo.png)


## 📋 JSON 格式

每个仓库生成一个 JSON 文件：

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

`last_commit_hash` 字段记录采集时的 HEAD commit hash。执行 `sync` 时，hash 未变化的仓库会被直接跳过，无需执行任何 git 操作。

`sync_status` 字段表示仓库与远程的同步状态：

| 状态 | 说明 |
|------|------|
| ✅ `synced` | 与远程同步 |
| ✏️ `local_changes` | 本地有未提交更改，远程无更新 |
| ⬇️ `remote_ahead` | 本地干净，但远程有新提交 |
| ⚠️ `diverged` | 本地有未提交更改且远程有新提交 |
| 🔒 `local_only_clean` | 无远程仓库，本地干净 |
| 🔧 `local_only_dirty` | 无远程仓库，本地有未提交更改 |

`is_archived` 字段表示仓库是否已在 GitHub 上归档。通过 `sync --check` 设置。取值：`true`（已归档）、`false`（活跃）、`null`（未检查或检查失败）。已归档的仓库在可视化中显示为灰色的"Archived"按钮。

## 🔑 GitHub Token（可选）

`sync --check` 通过 GitHub API 检查归档状态。不带认证时，只能检查**公开仓库**（速率限制：60 次/小时）。

要检查**私有仓库**，请设置 `GITHUB_TOKEN` 环境变量：

### Linux / macOS

```bash
export GITHUB_TOKEN=ghp_your_token_here
gitstats sync ./data --check
```

### Windows (PowerShell)

当前会话设置：

```powershell
$env:GITHUB_TOKEN="ghp_your_token_here"
gitstats sync ./data --check
```

通过 GUI 永久设置：**设置** → **系统** → **关于** → **高级系统设置** → **环境变量** → 用户变量 → **新建**

验证是否设置成功：

```powershell
echo $env:GITHUB_TOKEN
```

### 如何获取 Token

1. 前往 **GitHub** → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. 点击 **Generate new token (classic)**
3. 填写名称（如 `oh-my-gitstats`）
4. 在 **Select scopes** 下，无需额外权限（默认可访问公开仓库）
5. 要访问**私有仓库**，勾选 `repo` 权限
6. 点击 **Generate token** 并复制值（以 `ghp_` 开头）

> **注意：** 请使用 **Tokens (classic)**，而非 Fine-grained tokens。

> 使用 Token 后，速率限制提升至 5,000 次/小时。

## 🔧 依赖

- Python 3.9+
- click
- gitpython
- pyecharts
- jinja2
- requests

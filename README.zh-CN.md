<div align="center">

# oh-my-gitstats

中文 | [English](https://github.com/amomorning/oh-my-gitstats/blob/main/README.md)

批量收集多个 git 仓库 commit 数据，生成交互式 HTML 报表。

</div>

![折线图](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/linechart.png)
![热力图](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/heatmap.png)

## 功能

- **批量收集** — 递归扫描目录下的所有 git 仓库
- **增量同步** — 只获取上次采集之后的新 commit
- **自动执行** — `gitstats auto` 依次运行 collect → sync → visualize 并打开浏览器
- **折线图** — 可切换指标（代码行变更 / 提交次数）与时间粒度（天 / 周 / 月）；带可编辑日期范围条（两个日期输入框 + 30D / 90D / 6M / 1Y / ALL 快捷按钮），图例按所选范围动态过滤
- **日历热力图** — 按年份筛选查看提交活跃度
- **聚合与单仓库视图** — 2 列网格，可查看全部仓库汇总或单个仓库统计
- **仓库详情弹窗** — 点击任意仓库卡片，打开该仓库的折线图、热力图与元信息（提交数 / 行数 / 首次 / 末次 / Local / Remote / 操作）
- **Local / Remote 信号灯** — 每个 sync 状态在渲染时拆分为两个独立的信号灯，分别表示工作树状态与远端跟踪状态
- **VS Code 集成** — 可从 HTML 报表中直接打开仓库文件夹

## 安装

```bash
pip install oh-my-gitstats
```

或从源码安装：

```bash
git clone https://github.com/amomorning/oh-my-gitstats.git
cd oh-my-gitstats
pip install -e .
```

## 快速开始

**首次使用**，到每个项目目录下收集数据（路径会自动写入配置）：

```bash
cd ~/projects && gitstats collect .
cd ~/work && gitstats collect .
```

**之后**，一条命令完成 collect → sync → visualize 并打开浏览器：

```bash
gitstats auto
```

也可以手动编辑配置文件添加目录：

```bash
# 配置文件自动创建于：
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

**选项：**

| 选项            | 说明                                           |
|---------------|----------------------------------------------|
| `-q, --quiet` | 静默模式，不输出提示信息                                 |
| `--check`     | 检查 GitHub 仓库归档状态（需联网；私有仓库需设置 `GITHUB_TOKEN`） |
| `--no-open`   | 生成后不在浏览器中打开                                  |

## 命令

### `collect` — 收集 commit 数据

扫描目录下的 git 仓库并导出为 JSON：

```bash
gitstats collect /path/to/repos
```

| 选项             | 说明                                 |
|----------------|------------------------------------|
| `-o, --output` | JSON 文件保存目录（默认 `~/.gitstats/data`） |
| `-q, --quiet`  | 静默模式，不输出提示信息                       |
| `--skip`       | 跳过已有 JSON 文件的仓库                    |
| `--check`      | 检查 GitHub 仓库归档状态                   |

### `sync` — 增量同步

只获取新 commit 来更新已有 JSON 文件，比重新收集更快：

```bash
gitstats sync
```

| 选项            | 说明               |
|---------------|------------------|
| `-q, --quiet` | 静默模式，不输出提示信息     |
| `--check`     | 检查 GitHub 仓库归档状态 |

多目录场景的典型工作流：

```bash
# 一次性：从不同位置收集
gitstats collect /path/to/work-projects
gitstats collect /path/to/personal-projects --skip

# 之后：一条命令更新全部
gitstats sync
```

### `visualize` — 生成可视化

从已收集的数据生成交互式 HTML 文件：

```bash
gitstats visualize
```

| 选项             | 说明                                     |
|----------------|----------------------------------------|
| `-o, --output` | HTML 文件路径（默认 `~/.gitstats/stats.html`） |

生成的 HTML 支持在浏览器中动态切换粒度和指标，无需重新生成。

## 配置

配置文件位于 `~/.gitstats/settings.json`（首次运行时自动创建）：

```json
{
  "data_dir": "~/.gitstats/data",
  "output_html": "~/.gitstats/stats.html",
  "collect_paths": []
}
```

| 字段              | 说明                                          |
|-----------------|---------------------------------------------|
| `data_dir`      | JSON 文件存储目录                                 |
| `output_html`   | HTML 文件生成路径                                 |
| `collect_paths` | `gitstats auto` 扫描的目录列表（运行 `collect` 时自动添加） |

## GitHub Token（可选）

`--check` 通过 GitHub API 检查归档状态。未认证时只能检查**公开仓库**（速率限制 60 次/小时）。

> 未设置 `GITHUB_TOKEN` 时，使用 `--check` 会打印警告。

要检查**私有仓库**，需设置 `GITHUB_TOKEN` 环境变量：

### Linux / macOS

```bash
export GITHUB_TOKEN=ghp_your_token_here
gitstats sync --check
```

### Windows (PowerShell)

当前会话设置：

```powershell
$env:GITHUB_TOKEN="ghp_your_token_here"
gitstats sync --check
```

永久设置：**设置** → **系统** → **关于** → **高级系统设置** → **环境变量** → 用户变量 → **新建**

### 获取 Token

1. 进入 **GitHub** → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. 点击 **Generate new token (classic)**
3. 填写名称（如 `oh-my-gitstats`）
4. **Select scopes** 下，访问公开仓库无需额外权限
5. 访问**私有仓库**需勾选 `repo` 权限
6. 点击 **Generate token** 并复制值（以 `ghp_` 开头）

> 请使用 **Tokens (classic)**，不要用 Fine-grained tokens。带 Token 后速率限制提升至 5,000 次/小时。

## 输出

生成的 HTML 包含：

1. **折线图（01 / Trend）** — 指标选择（代码行变更 / 提交次数）+ 粒度选择（天 / 周 / 月）+ **可编辑日期范围条**：两个 `<input type="date">`（粒度为月时切换为 `<input type="month">`）外加快捷按钮（30D / 90D / 6M / 1Y / ALL）。范围条与 ECharts `dataZoom` 双向联动；图例按所选范围动态过滤，只显示范围内有提交的仓库。

2. **聚合热力图（02 / Aggregate）** — 全部仓库的汇总活跃度，年份选择（全部年份 / 指定年份），切换单年/多年时高度自动调整。

3. **独立热力图（03 / Repositories）** — 2 列网格的仓库卡片。每张卡片显示仓库名、等宽字体路径、**Local + Remote 信号灯**（标记 L / R 的小圆点，红黄绿灰四色）、带 MDI 图标的 Continue / Archived 按钮（`vscode://file/` URI）。点击任意卡片打开**详情弹窗**：单仓库折线图（默认按天）、热力图、7 格元信息（提交数 / 行数 / 首次 / 末次 / Local / Remote / 操作）。可通过 × 按钮、点击背景或 ESC 键关闭。

![独立热力图](https://github.com/amomorning/oh-my-gitstats/raw/main/imgs/repo.png)

## JSON 格式

每个仓库生成一个 JSON 文件（`~/.gitstats/data/{repo_name}.json`）：

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

**`last_commit_hash`** — 采集时的 HEAD commit hash。执行 `sync` 时，hash 未变化的仓库会被跳过。

**`sync_status`** — 同步状态，渲染时拆分为两个独立的 Local + Remote 信号灯（JSON 中仍存为单个枚举值）：

| sync_status           | Local   | Remote   |
|-----------------------|---------|----------|
| `synced`              | 🟢 Clean | 🟢 Synced |
| `local_changes`       | 🟡 Dirty | 🟢 Synced |
| `remote_ahead`        | 🟢 Clean | 🟡 Ahead  |
| `diverged`            | 🟡 Dirty | 🟡 Ahead  |
| `local_only_clean`    | 🟢 Clean | ⚪ None   |
| `local_only_dirty`    | 🟡 Dirty | ⚪ None   |
| `network_error_clean` | 🟢 Clean | 🔴 Error  |
| `network_error_dirty` | 🟡 Dirty | 🔴 Error  |

**`is_archived`** — 仓库是否已在 GitHub 上归档（由 `--check` 设置）。取值 `true`（已归档）、`false`（活跃）、`null`（未检查或检查失败）。已归档仓库显示灰色的 Archived 按钮。

## 依赖

- Python 3.9+
- click, gitpython, pyecharts, jinja2, requests

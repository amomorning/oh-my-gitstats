"""Visualization module for generating HTML charts from commit data."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from pyecharts import options as opts
from pyecharts.charts import Line, Calendar
from pyecharts.commons.utils import JsCode
from jinja2 import Template


METRICS = ("changes", "commits")
GRANULARITIES = ("day", "week", "month")

COLORS = [
    "#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de",
    "#3ba272", "#fc8452", "#9a60b4", "#ea7ccc", "#48b8d0"
]


def load_json_files(json_dir: str) -> List[Dict[str, Any]]:
    """Load all JSON files from a directory.

    Args:
        json_dir: Directory containing JSON files.

    Returns:
        List of repository data dictionaries.
    """
    data = []
    for filepath in Path(json_dir).glob("*.json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data.append(json.load(f))
    return data


def aggregate_by_period(
    commits: List[Dict[str, Any]],
    granularity: str,
    metric: str = "changes"
) -> Dict[str, int]:
    """Aggregate commit data by time period.

    Args:
        commits: List of commit dictionaries.
        granularity: Aggregation period (day/week/month).
        metric: "changes" for additions+deletions, "commits" for count.

    Returns:
        Dictionary mapping period string to aggregated value.
    """
    aggregated = defaultdict(int)

    for commit in commits:
        ts = datetime.fromisoformat(commit["timestamp"])
        value = 1 if metric == "commits" else commit["additions"] + commit["deletions"]

        if granularity == "day":
            key = ts.strftime("%Y-%m-%d")
        elif granularity == "week":
            monday = ts - timedelta(days=ts.weekday())
            key = monday.strftime("%Y-%m-%d")
        else:  # month
            key = ts.strftime("%Y-%m")

        aggregated[key] += value

    return aggregated


def get_date_range(all_data: List[Dict[str, Any]]) -> tuple[str, str]:
    """Get the overall date range from all repositories.

    Args:
        all_data: List of repository data.

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format.
    """
    all_dates = []
    for repo in all_data:
        for commit in repo["commits"]:
            ts = datetime.fromisoformat(commit["timestamp"])
            all_dates.append(ts.date())

    if not all_dates:
        today = datetime.now().date()
        return f"{today.year}-01-01", f"{today.year}-12-31"

    min_date = min(all_dates)
    max_date = max(all_dates)

    return min_date.strftime("%Y-%m-%d"), max_date.strftime("%Y-%m-%d")


def get_years_from_data(all_data: List[Dict[str, Any]]) -> List[str]:
    """Extract all unique years from the data.

    Args:
        all_data: List of repository data.

    Returns:
        List of year strings in descending order.
    """
    years = set()
    for repo in all_data:
        for commit in repo["commits"]:
            ts = datetime.fromisoformat(commit["timestamp"])
            years.add(str(ts.year))
    return sorted(years, reverse=True)


def _build_line_opts(
    all_data: List[Dict[str, Any]],
    granularity: str,
    metric: str
) -> str:
    """Build line chart options JSON string.

    Args:
        all_data: List of repository data.
        granularity: Time aggregation granularity (day/week/month).
        metric: "changes" or "commits".

    Returns:
        JSON string of chart options.
    """
    all_periods = set()
    repo_series = {}

    for repo in all_data:
        aggregated = aggregate_by_period(repo["commits"], granularity, metric)
        repo_series[repo["repo_name"]] = aggregated
        all_periods.update(aggregated.keys())

    sorted_periods = sorted(all_periods)

    line = Line()
    line.add_xaxis(sorted_periods)

    for idx, (repo_name, data) in enumerate(repo_series.items()):
        y_data = [data.get(period, 0) for period in sorted_periods]
        line.add_yaxis(
            series_name=repo_name,
            y_axis=y_data,
            color=COLORS[idx % len(COLORS)],
            is_smooth=True,
            label_opts=opts.LabelOpts(is_show=False),
        )

    y_name = "Lines Changed" if metric == "changes" else "Commits"

    line.set_global_opts(
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            formatter=JsCode(
                "function(params){"
                "var tip=params[0].axisValueLabel;"
                "params.forEach(function(p){"
                "if(p.value[1])tip+='<br/>'+p.marker+p.seriesName+': '+p.value[1];"
                "});"
                "return tip;}"
            )
        ),
        legend_opts=opts.LegendOpts(
            type_="scroll",
            selected_mode="multiple"
        ),
        xaxis_opts=opts.AxisOpts(
            type_="category",
            axislabel_opts=opts.LabelOpts(rotate=45)
        ),
        yaxis_opts=opts.AxisOpts(name=y_name, type_="value"),
        datazoom_opts=[
            opts.DataZoomOpts(type_="inside"),
            opts.DataZoomOpts(type_="slider")
        ]
    )

    return line.dump_options()


def _build_agg_heatmap_opts(
    all_data: List[Dict[str, Any]],
    date_range: tuple[str, str],
    metric: str
) -> str:
    """Build aggregate heatmap options JSON string.

    Args:
        all_data: List of repository data.
        date_range: Tuple of (start_date, end_date).
        metric: "changes" or "commits".

    Returns:
        JSON string of chart options.
    """
    daily_data = defaultdict(int)
    for repo in all_data:
        for commit in repo["commits"]:
            ts = datetime.fromisoformat(commit["timestamp"])
            date_str = ts.strftime("%Y-%m-%d")
            if metric == "commits":
                daily_data[date_str] += 1
            else:
                daily_data[date_str] += commit["additions"] + commit["deletions"]

    calendar_data = [[date, value] for date, value in sorted(daily_data.items())]

    calendar = Calendar(init_opts=opts.InitOpts(width="100%", height="300px"))
    calendar.add(
        series_name="",
        yaxis_data=calendar_data,
        calendar_opts=opts.CalendarOpts(
            pos_left="100px",
            pos_right="50px",
            pos_top="50px",
            pos_bottom="20px",
            range_=date_range,
            yearlabel_opts=opts.CalendarYearLabelOpts(is_show=True),
            monthlabel_opts=opts.CalendarMonthLabelOpts(is_show=True),
            daylabel_opts=opts.CalendarDayLabelOpts(is_show=True),
        )
    )

    unit = "lines" if metric == "changes" else "commits"
    calendar.set_global_opts(
        visualmap_opts=opts.VisualMapOpts(
            max_=max(daily_data.values()) if daily_data else 100,
            min_=0,
            orient="horizontal",
            is_piecewise=False,
            pos_left="100px",
            pos_bottom="0px",
        ),
        tooltip_opts=opts.TooltipOpts(formatter=JsCode(
            f"function(p){{return p.data[0] + ': ' + p.data[1] + ' {unit}'}}"
        ))
    )

    return calendar.dump_options()


def _build_ind_heatmap_opts(
    all_data: List[Dict[str, Any]],
    date_range: tuple[str, str],
    metric: str
) -> List[str]:
    """Build individual heatmap options JSON string list.

    Args:
        all_data: List of repository data.
        date_range: Tuple of (start_date, end_date).
        metric: "changes" or "commits".

    Returns:
        List of JSON strings, one per repository.
    """
    options_list = []

    for repo in all_data:
        daily_data = defaultdict(int)
        for commit in repo["commits"]:
            ts = datetime.fromisoformat(commit["timestamp"])
            date_str = ts.strftime("%Y-%m-%d")
            if metric == "commits":
                daily_data[date_str] += 1
            else:
                daily_data[date_str] += commit["additions"] + commit["deletions"]

        calendar_data = [[date, value] for date, value in sorted(daily_data.items())]

        calendar = Calendar(init_opts=opts.InitOpts(width="100%", height="200px"))
        calendar.add(
            series_name="",
            yaxis_data=calendar_data,
            calendar_opts=opts.CalendarOpts(
                pos_left="100px",
                pos_right="50px",
                pos_top="30px",
                pos_bottom="10px",
                range_=date_range,
                yearlabel_opts=opts.CalendarYearLabelOpts(is_show=False),
                monthlabel_opts=opts.CalendarMonthLabelOpts(is_show=True),
                daylabel_opts=opts.CalendarDayLabelOpts(is_show=False),
            )
        )

        max_val = max(daily_data.values()) if daily_data else 100
        unit = "lines" if metric == "changes" else "commits"
        calendar.set_global_opts(
            visualmap_opts=opts.VisualMapOpts(
                max_=max_val,
                min_=0,
                orient="horizontal",
                is_piecewise=False,
                pos_left="100px",
                pos_bottom="0px",
            ),
            tooltip_opts=opts.TooltipOpts(formatter=JsCode(
                f"function(p){{return p.data[0] + ': ' + p.data[1] + ' {unit}'}}"
            ))
        )

        options_list.append(calendar.dump_options())

    return options_list


def rewrite_path(path: str) -> str:
    """Rewrite file path to use forward slashes for better compatibility."""
    return path.replace("\\", "/")


def _build_line_js_obj(all_data: List[Dict[str, Any]]) -> str:
    """Build JS object string for line chart data (all metric x granularity combos)."""
    parts = []
    for metric in METRICS:
        gran_parts = []
        for gran in GRANULARITIES:
            opts_json = _build_line_opts(all_data, gran, metric)
            gran_parts.append(f'"{gran}":{opts_json}')
        parts.append(f'"{metric}":{{{",".join(gran_parts)}}}')
    return "{" + ",".join(parts) + "}"


def _build_heatmap_js_obj(
    all_data: List[Dict[str, Any]],
    date_range: tuple[str, str],
    years: List[str]
) -> str:
    """Build JS object string for heatmap data (all metric x year combos)."""
    year_ranges: Dict[str, tuple[str, str]] = {"all": date_range}
    for year in years:
        year_ranges[year] = (f"{year}-01-01", f"{year}-12-31")

    parts = []
    for metric in METRICS:
        year_parts = []
        for year_key, year_range in year_ranges.items():
            agg = _build_agg_heatmap_opts(all_data, year_range, metric)
            ind_list = _build_ind_heatmap_opts(all_data, year_range, metric)
            ind_str = ",".join(ind_list)
            year_parts.append(
                f'"{year_key}":{{"aggregate":{agg},"individual":[{ind_str}]}}'
            )
        parts.append(f'"{metric}":{{{",".join(year_parts)}}}')
    return "{" + ",".join(parts) + "}"


def generate_html(json_dir: str, output_path: str) -> str:
    """Generate a complete HTML file with all visualizations.

    Args:
        json_dir: Directory containing JSON files.
        output_path: Path to save the HTML file.

    Returns:
        Path to the generated HTML file.
    """
    all_data = load_json_files(json_dir)

    if not all_data:
        raise ValueError(f"No JSON files found in {json_dir}")

    date_range = get_date_range(all_data)
    years = get_years_from_data(all_data)

    # Pre-compute all chart data
    line_js_obj = _build_line_js_obj(all_data)
    heatmap_js_obj = _build_heatmap_js_obj(all_data, date_range, years)

    # Get repo info for individual heatmaps
    repo_info = [
        {"name": repo["repo_name"], "path": repo.get("repo_path", "")}
        for repo in all_data
    ]

    # Build HTML with card layout
    html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Git Stats Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 24px;
            color: #333;
        }
        .card {
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 24px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #eee;
        }
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }
        .controls {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .selector {
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
        }
        .chart-container {
            width: 100%;
        }
        .heatmaps-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(600px, 1fr));
            gap: 20px;
        }
        .heatmap-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
        }
        .heatmap-card .chart-container {
            height: 180px;
        }
        .repo-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .repo-name {
            font-weight: 600;
            color: #333;
        }
        .open-folder-btn {
            background: #4a90d9;
            color: #fff;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .open-folder-btn:hover {
            background: #357abd;
        }
        .repo-path {
            font-size: 11px;
            color: #888;
            margin-bottom: 8px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <h1>📊 Git Stats Visualization</h1>

    <div class="card">
        <div class="card-header">
            <span class="card-title">📈 Commit Activity Over Time</span>
            <div class="controls">
                <select class="selector" id="metric-selector" onchange="onMetricChange(this.value)">
                    <option value="changes">Lines Changed</option>
                    <option value="commits">Commit Count</option>
                </select>
                <select class="selector" id="granularity-selector" onchange="onGranularityChange(this.value)">
                    <option value="day">Day</option>
                    <option value="week" selected>Week</option>
                    <option value="month">Month</option>
                </select>
            </div>
        </div>
        <div class="chart-container" id="line-chart" style="height:500px;"></div>
    </div>

    <div class="card">
        <div class="card-header">
            <span class="card-title">🗓️ Aggregated Commit Activity</span>
            <select class="selector" id="aggregate-year-selector" onchange="updateAggregateHeatmap(this.value)">
                <option value="all">All Years</option>
                {% for year in years %}
                <option value="{{ year }}">{{ year }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="chart-container" id="aggregate-heatmap" style="height:300px;"></div>
    </div>

    <div class="card">
        <div class="card-header">
            <span class="card-title">📁 Individual Repository Heatmaps</span>
            <select class="selector" id="individual-year-selector" onchange="updateIndividualHeatmaps(this.value)">
                <option value="all">All Years</option>
                {% for year in years %}
                <option value="{{ year }}">{{ year }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="heatmaps-grid">
            {% for item in individual_charts %}
            <div class="heatmap-card">
                <div class="repo-header">
                    <span class="repo-name">{{ item.name }}</span>
                    <button class="open-folder-btn" onclick="openFolder('{{ item.path }}')">
                        📂 Open Folder
                    </button>
                </div>
                <div class="repo-path">{{ item.path }}</div>
                <div class="chart-container" id="{{ item.id }}" style="height:160px;"></div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        // Pre-computed chart data
        var lineData = {{ line_js_obj }};
        var heatmapData = {{ heatmap_js_obj }};

        // Current state
        var currentMetric = 'changes';
        var currentGranularity = 'week';

        // Open folder function
        function openFolder(path) {
            var vscodeUrl = 'vscode://file/' + path.replace(/\\\\/g, '/');
            var link = document.createElement('a');
            link.href = vscodeUrl;
            link.click();
        }

        // Line chart
        var lineChart = echarts.init(document.getElementById('line-chart'));
        lineChart.setOption(lineData[currentMetric][currentGranularity]);
        window.addEventListener('resize', function() { lineChart.resize(); });

        // Aggregate heatmap
        var aggregateChart = echarts.init(document.getElementById('aggregate-heatmap'));
        aggregateChart.setOption(heatmapData[currentMetric]['all'].aggregate);
        window.addEventListener('resize', function() { aggregateChart.resize(); });

        // Individual heatmaps
        var individualCharts = [];
        {% for item in individual_charts %}
        (function() {
            var chart = echarts.init(document.getElementById('{{ item.id }}'));
            individualCharts.push(chart);
            window.addEventListener('resize', function() { chart.resize(); });
        })();
        {% endfor %}

        // Initialize individual heatmaps
        for (var i = 0; i < individualCharts.length; i++) {
            individualCharts[i].setOption(heatmapData[currentMetric]['all'].individual[i]);
        }

        // Control handlers
        function onMetricChange(metric) {
            currentMetric = metric;
            lineChart.setOption(lineData[currentMetric][currentGranularity], true);

            var year = document.getElementById('aggregate-year-selector').value;
            aggregateChart.setOption(heatmapData[currentMetric][year].aggregate, true);
            for (var i = 0; i < individualCharts.length; i++) {
                individualCharts[i].setOption(heatmapData[currentMetric][year].individual[i], true);
            }
        }

        function onGranularityChange(granularity) {
            currentGranularity = granularity;
            lineChart.setOption(lineData[currentMetric][currentGranularity], true);
        }

        function updateAggregateHeatmap(year) {
            aggregateChart.setOption(heatmapData[currentMetric][year].aggregate, true);
            document.getElementById('individual-year-selector').value = year;
            for (var i = 0; i < individualCharts.length; i++) {
                individualCharts[i].setOption(heatmapData[currentMetric][year].individual[i], true);
            }
        }

        function updateIndividualHeatmaps(year) {
            document.getElementById('aggregate-year-selector').value = year;
            for (var i = 0; i < individualCharts.length; i++) {
                individualCharts[i].setOption(heatmapData[currentMetric][year].individual[i], true);
            }
        }
    </script>
</body>
</html>
    """)

    # Generate chart IDs for individual heatmaps
    individual_charts_data = []
    for idx, repo in enumerate(repo_info):
        chart_id = f"individual-heatmap-{idx}"
        individual_charts_data.append({
            "id": chart_id,
            "name": repo["name"],
            "path": rewrite_path(repo["path"])
        })

    # Render HTML
    html_content = html_template.render(
        line_js_obj=line_js_obj,
        heatmap_js_obj=heatmap_js_obj,
        years=years,
        individual_charts=individual_charts_data
    )

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding="utf-8")

    return str(output_file)

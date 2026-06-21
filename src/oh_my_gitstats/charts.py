"""Chart building functions using pyecharts."""

from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

from pyecharts import options as opts
from pyecharts.charts import Line, Calendar
from pyecharts.commons.utils import JsCode

from .constants import METRICS, GRANULARITIES, COLORS, HEATMAP_COLORS
from .data import aggregate_by_period


def _axis_text_style() -> opts.TextStyleOpts:
    """Swiss-flavored axis/label text style."""
    return opts.TextStyleOpts(
        color="#0a0a0a",
        font_size=11,
        font_family="Inter, 'Helvetica Neue', Helvetica, Arial, sans-serif",
    )


def _tooltip_text_style() -> opts.TextStyleOpts:
    return opts.TextStyleOpts(
        color="#0a0a0a",
        font_size=12,
        font_family="Inter, 'Helvetica Neue', Helvetica, Arial, sans-serif",
    )


def build_line_opts(
    all_data: List[Dict[str, Any]],
    granularity: str,
    metric: str,
    single_repo: Dict[str, Any] | None = None
) -> str:
    """Build line chart options JSON string.

    Args:
        all_data: List of repository data (ignored when ``single_repo`` is set).
        granularity: Time aggregation granularity (day/week/month).
        metric: "changes" or "commits".
        single_repo: Optional single repo dict; when provided, builds a
            one-series chart for that repo only.

    Returns:
        JSON string of chart options.
    """
    repos = [single_repo] if single_repo else all_data

    all_periods = set()
    repo_series = {}

    for repo in repos:
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
            color=COLORS[idx % len(COLORS)] if not single_repo else COLORS[1],
            is_smooth=True,
            symbol="circle",
            symbol_size=6,
            label_opts=opts.LabelOpts(is_show=False),
            linestyle_opts=opts.LineStyleOpts(width=2),
        )

    y_name = "Lines Changed" if metric == "changes" else "Commits"

    line.set_global_opts(
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            background_color="#ffffff",
            border_color="#0a0a0a",
            border_width=1,
            textstyle_opts=_tooltip_text_style(),
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
            selected_mode="multiple",
            textstyle_opts=_axis_text_style(),
            inactive_color="#bbbbbb",
        ),
        xaxis_opts=opts.AxisOpts(
            type_="category",
            axislabel_opts=opts.LabelOpts(rotate=0, color="#0a0a0a"),
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(color="#0a0a0a", width=1)
            ),
            axistick_opts=opts.AxisTickOpts(length=4),
        ),
        yaxis_opts=opts.AxisOpts(
            name=y_name,
            name_textstyle_opts=_axis_text_style(),
            type_="value",
            axislabel_opts=opts.LabelOpts(color="#0a0a0a"),
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(color="#0a0a0a", width=1)
            ),
            splitline_opts=opts.SplitLineOpts(
                is_show=True,
                linestyle_opts=opts.LineStyleOpts(color="#eeeeee", width=1),
            ),
        ),
        datazoom_opts=[
            opts.DataZoomOpts(type_="inside"),
            opts.DataZoomOpts(type_="slider"),
        ],
    )

    return line.dump_options()


def build_agg_heatmap_opts(
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
            pos_left="60px",
            pos_right="20px",
            pos_top="40px",
            pos_bottom="30px",
            range_=date_range,
            cell_size="auto",
            yearlabel_opts=opts.CalendarYearLabelOpts(is_show=True),
            monthlabel_opts=opts.CalendarMonthLabelOpts(is_show=True),
            daylabel_opts=opts.CalendarDayLabelOpts(is_show=True),
        ),
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
            range_color=HEATMAP_COLORS,
            textstyle_opts=_axis_text_style(),
        ),
        tooltip_opts=opts.TooltipOpts(
            background_color="#ffffff",
            border_color="#0a0a0a",
            border_width=1,
            textstyle_opts=_tooltip_text_style(),
            formatter=JsCode(
                f"function(p){{return p.data[0] + ': ' + p.data[1] + ' {unit}'}}"
            ),
        ),
    )

    return calendar.dump_options()


def build_ind_heatmap_opts(
    all_data: List[Dict[str, Any]],
    date_range: tuple[str, str],
    metric: str,
    cell_size: int = 10,
    pos_left: str = "30px",
    pos_right: str = "10px"
) -> List[str]:
    """Build individual heatmap options JSON string list.

    Args:
        all_data: List of repository data.
        date_range: Tuple of (start_date, end_date).
        metric: "changes" or "commits".
        cell_size: Pixel size for each calendar cell (forced square).
        pos_left: Left position of the calendar inside the chart container.
        pos_right: Right position of the calendar inside the chart container.

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
                pos_left=pos_left,
                pos_right=pos_right,
                pos_top="30px",
                pos_bottom="10px",
                range_=date_range,
                cell_size=[cell_size, cell_size],
                yearlabel_opts=opts.CalendarYearLabelOpts(is_show=False),
                monthlabel_opts=opts.CalendarMonthLabelOpts(is_show=True),
                daylabel_opts=opts.CalendarDayLabelOpts(is_show=False),
            ),
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
                range_color=HEATMAP_COLORS,
                textstyle_opts=_axis_text_style(),
            ),
            tooltip_opts=opts.TooltipOpts(
                background_color="#ffffff",
                border_color="#0a0a0a",
                border_width=1,
                textstyle_opts=_tooltip_text_style(),
                formatter=JsCode(
                    f"function(p){{return p.data[0] + ': ' + p.data[1] + ' {unit}'}}"
                ),
            ),
        )

        options_list.append(calendar.dump_options())

    return options_list


def build_single_repo_heatmap_opts(
    repo: Dict[str, Any],
    date_range: tuple[str, str],
    metric: str
) -> str:
    """Build a large single-repo heatmap options JSON string.

    Uses a larger cell size and wider side padding than the grid cards since
    the modal has more horizontal room.

    Args:
        repo: Single repository data dict.
        date_range: Tuple of (start_date, end_date).
        metric: "changes" or "commits".

    Returns:
        JSON string of chart options.
    """
    return build_ind_heatmap_opts(
        [repo], date_range, metric,
        cell_size=16, pos_left="60px", pos_right="20px"
    )[0]


def build_line_js_obj(all_data: List[Dict[str, Any]]) -> str:
    """Build JS object string for line chart data (all metric x granularity combos)."""
    parts = []
    for metric in METRICS:
        gran_parts = []
        for gran in GRANULARITIES:
            opts_json = build_line_opts(all_data, gran, metric)
            gran_parts.append(f'"{gran}":{opts_json}')
        parts.append(f'"{metric}":{{{",".join(gran_parts)}}}')
    return "{" + ",".join(parts) + "}"


def build_heatmap_js_obj(
    all_data: List[Dict[str, Any]],
    date_range: tuple[str, str],
    years: List[str]
) -> tuple[str, str]:
    """Build JS object strings for heatmap data and active repo index.

    Returns:
        Tuple of (heatmap_js_obj, active_repos_js_obj).
    """
    year_ranges: Dict[str, tuple[str, str]] = {"all": date_range}
    for year in years:
        year_ranges[year] = (f"{year}-01-01", f"{year}-12-31")

    heatmap_parts = []
    active_parts = []

    for metric in METRICS:
        year_heatmap_parts = []
        year_active_parts = []

        for year_key, year_range in year_ranges.items():
            agg = build_agg_heatmap_opts(all_data, year_range, metric)
            ind_list = build_ind_heatmap_opts(all_data, year_range, metric)
            ind_str = ",".join(ind_list)
            year_heatmap_parts.append(
                f'"{year_key}":{{"aggregate":{agg},"individual":[{ind_str}]}}'
            )

            # Determine active repos for this metric x year combo
            active_indices = []
            for i, repo in enumerate(all_data):
                for commit in repo["commits"]:
                    ts = datetime.fromisoformat(commit["timestamp"])
                    date_str = ts.strftime("%Y-%m-%d")
                    if year_range[0] <= date_str <= year_range[1]:
                        active_indices.append(i)
                        break
            year_active_parts.append(
                f'"{year_key}":[{",".join(str(x) for x in active_indices)}]'
            )

        heatmap_parts.append(f'"{metric}":{{{",".join(year_heatmap_parts)}}}')
        active_parts.append(f'"{metric}":{{{",".join(year_active_parts)}}}')

    heatmap_js = "{" + ",".join(heatmap_parts) + "}"
    active_js = "{" + ",".join(active_parts) + "}"
    return heatmap_js, active_js


def build_single_repo_line_js_obj(all_data: List[Dict[str, Any]]) -> str:
    """Build JS object string for per-repo line chart data.

    Structure: { repo_index: { metric: { granularity: <lineOptsJSON> } } }.
    Used by the detail modal to render a single repo's line chart with its
    own metric/granularity controls.
    """
    repo_parts: List[str] = []
    for idx, repo in enumerate(all_data):
        metric_parts: List[str] = []
        for metric in METRICS:
            gran_parts: List[str] = []
            for gran in GRANULARITIES:
                opts_json = build_line_opts(
                    all_data, gran, metric, single_repo=repo
                )
                gran_parts.append(f'"{gran}":{opts_json}')
            metric_parts.append(f'"{metric}":{{{",".join(gran_parts)}}}')
        repo_parts.append(f'"{idx}":{{{",".join(metric_parts)}}}')
    return "{" + ",".join(repo_parts) + "}"


def build_single_repo_heatmap_js_obj(
    all_data: List[Dict[str, Any]],
    date_range: tuple[str, str],
    years: List[str]
) -> str:
    """Build JS object string for per-repo large heatmap data.

    Structure: { repo_index: { metric: { year_key: <heatmapOptsJSON> } } }.
    Used by the detail modal to render a single repo's large heatmap.
    """
    year_ranges: Dict[str, tuple[str, str]] = {"all": date_range}
    for year in years:
        year_ranges[year] = (f"{year}-01-01", f"{year}-12-31")

    repo_parts: List[str] = []
    for idx, repo in enumerate(all_data):
        metric_parts: List[str] = []
        for metric in METRICS:
            year_parts: List[str] = []
            for year_key, year_range in year_ranges.items():
                opts_json = build_single_repo_heatmap_opts(repo, year_range, metric)
                year_parts.append(f'"{year_key}":{opts_json}')
            metric_parts.append(f'"{metric}":{{{",".join(year_parts)}}}')
        repo_parts.append(f'"{idx}":{{{",".join(metric_parts)}}}')
    return "{" + ",".join(repo_parts) + "}"

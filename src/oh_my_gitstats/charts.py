"""Chart building functions using pyecharts."""

from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

from pyecharts import options as opts
from pyecharts.charts import Line, Calendar
from pyecharts.commons.utils import JsCode

from .constants import METRICS, GRANULARITIES, COLORS
from .data import aggregate_by_period


def build_line_opts(
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


def build_ind_heatmap_opts(
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
) -> str:
    """Build JS object string for heatmap data (all metric x year combos)."""
    year_ranges: Dict[str, tuple[str, str]] = {"all": date_range}
    for year in years:
        year_ranges[year] = (f"{year}-01-01", f"{year}-12-31")

    parts = []
    for metric in METRICS:
        year_parts = []
        for year_key, year_range in year_ranges.items():
            agg = build_agg_heatmap_opts(all_data, year_range, metric)
            ind_list = build_ind_heatmap_opts(all_data, year_range, metric)
            ind_str = ",".join(ind_list)
            year_parts.append(
                f'"{year_key}":{{"aggregate":{agg},"individual":[{ind_str}]}}'
            )
        parts.append(f'"{metric}":{{{",".join(year_parts)}}}')
    return "{" + ",".join(parts) + "}"

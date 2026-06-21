"""Shared constants for the visualization module."""

METRICS = ("changes", "commits")
GRANULARITIES = ("day", "week", "month")

# Bright Swiss-restrained 10-color palette. Lighter mid-tones keep multi-series
# line charts legible; no black so every series stays visually distinct against
# the white background.
COLORS = [
    "#e60012",  # Swiss red (accent)
    "#3b82f6",  # blue
    "#10b981",  # green
    "#f59e0b",  # amber
    "#8b5cf6",  # purple
    "#06b6d4",  # cyan
    "#ec4899",  # pink
    "#84cc16",  # lime
    "#6366f1",  # indigo
    "#f97316",  # orange
]

# GitHub-style green gradient for heatmap visualMap.
# white -> light green -> deep green
HEATMAP_COLORS = ["#ffffff", "#c6e48b", "#7bc96f", "#239a3b", "#196127"]

# Traffic-light signal colors for Local/Remote status indicators.
SIGNAL_GREEN = "#10b981"   # nominal
SIGNAL_YELLOW = "#f5b400"  # warning
SIGNAL_RED = "#ef4444"     # error
SIGNAL_GRAY = "#9ca3af"    # no remote / unknown

# Sync status decomposed into (Local, Remote) signal pairs.
# Each entry exposes:
#   local:  {"color", "label"}   working-tree state
#   remote: {"color", "label"}   remote-tracking state
#   label:  full human description (used as tooltip)
SYNC_STATUS_INFO = {
    "synced": {
        "local":  {"color": SIGNAL_GREEN,  "label": "Clean"},
        "remote": {"color": SIGNAL_GREEN,  "label": "Synced"},
        "label": "Synced with remote",
    },
    "local_changes": {
        "local":  {"color": SIGNAL_YELLOW, "label": "Dirty"},
        "remote": {"color": SIGNAL_GREEN,  "label": "Synced"},
        "label": "Local changes, remote up-to-date",
    },
    "remote_ahead": {
        "local":  {"color": SIGNAL_GREEN,  "label": "Clean"},
        "remote": {"color": SIGNAL_YELLOW, "label": "Ahead"},
        "label": "Remote has new commits",
    },
    "diverged": {
        "local":  {"color": SIGNAL_YELLOW, "label": "Dirty"},
        "remote": {"color": SIGNAL_YELLOW, "label": "Ahead"},
        "label": "Local changes + remote ahead",
    },
    "local_only_clean": {
        "local":  {"color": SIGNAL_GREEN,  "label": "Clean"},
        "remote": {"color": SIGNAL_GRAY,   "label": "None"},
        "label": "No remote, local clean",
    },
    "local_only_dirty": {
        "local":  {"color": SIGNAL_YELLOW, "label": "Dirty"},
        "remote": {"color": SIGNAL_GRAY,   "label": "None"},
        "label": "No remote, local changes",
    },
    "network_error_clean": {
        "local":  {"color": SIGNAL_GREEN,  "label": "Clean"},
        "remote": {"color": SIGNAL_RED,    "label": "Error"},
        "label": "Network error, local clean",
    },
    "network_error_dirty": {
        "local":  {"color": SIGNAL_YELLOW, "label": "Dirty"},
        "remote": {"color": SIGNAL_RED,    "label": "Error"},
        "label": "Network error, local changes",
    },
}

# Legend entries grouped by kind, preserving display order.
SYNC_LEGEND = [
    {"kind": "Local",  "color": SIGNAL_GREEN,  "label": "Clean"},
    {"kind": "Local",  "color": SIGNAL_YELLOW, "label": "Dirty"},
    {"kind": "Remote", "color": SIGNAL_GREEN,  "label": "Synced"},
    {"kind": "Remote", "color": SIGNAL_YELLOW, "label": "Ahead"},
    {"kind": "Remote", "color": SIGNAL_RED,    "label": "Error"},
    {"kind": "Remote", "color": SIGNAL_GRAY,   "label": "None"},
]

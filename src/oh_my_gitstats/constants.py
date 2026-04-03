"""Shared constants for the visualization module."""

METRICS = ("changes", "commits")
GRANULARITIES = ("day", "week", "month")

COLORS = [
    "#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de",
    "#3ba272", "#fc8452", "#9a60b4", "#ea7ccc", "#48b8d0"
]

SYNC_STATUS_INFO = {
    "synced":           {"emoji": "\u2705", "label": "Synced with remote"},
    "local_changes":    {"emoji": "\u270f\ufe0f", "label": "Local changes, remote up-to-date"},
    "remote_ahead":     {"emoji": "\u2b07\ufe0f", "label": "Remote has new commits"},
    "diverged":         {"emoji": "\u26a0\ufe0f", "label": "Local changes + remote ahead"},
    "local_only_clean": {"emoji": "\U0001f512", "label": "No remote, local clean"},
    "local_only_dirty": {"emoji": "\U0001f527", "label": "No remote, local changes"},
}

#!/usr/bin/env bash
# session-start-clip2path.sh
# Launches clip2path silently when Claude Code starts.
# Does nothing if an instance is already running (checked via PID file).
#
# Usage: add this script to ~/.claude/settings.json under hooks.SessionStart
# See README for full setup instructions.

CLIP2PATH_SCRIPT="C:/Claude/clip2path/clip2path.py"
PID_FILE="$HOME/claude-images/clip2path.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        # Instance already running
        exit 0
    fi
fi

# Launch without a console window (pythonw suppresses the terminal)
pythonw "$CLIP2PATH_SCRIPT" start &

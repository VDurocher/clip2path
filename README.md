# clip2path

**Copy a screenshot → paste a file path. Automatically.**

clip2path runs silently in the background on Windows. The moment you copy an image or screenshot, it saves it as a timestamped PNG and replaces your clipboard with the absolute file path — ready to paste directly into [Claude Code](https://claude.ai/code).

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## The problem

Claude Code accepts image file paths directly in chat. But getting a screenshot *into* Claude used to mean:

1. Take screenshot
2. Open Paint / Snip & Sketch
3. Save the file somewhere
4. Navigate to it in Explorer, copy the path
5. Paste into Claude

**With clip2path:** `Win+Shift+S` → `Ctrl+V`. That's it.

---

## Demo

> *Copy any image or screenshot → your clipboard now contains the file path*

```
[clip2path running in background]

You: Ctrl+C on any image
→ clipboard: C:\Users\you\claude-images\clip_20260405_143022.png

You: Ctrl+V into Claude Code chat
→ Claude sees the image ✓
```

---

## Install

**Requires:** Python 3.9+ on Windows

```bash
pip install Pillow pyperclip
```

---

## Usage

```bash
# Start watching (default output: ~/claude-images/)
python clip2path.py start

# Custom output folder
python clip2path.py start --dir C:\screenshots

# Delete all saved images
python clip2path.py clear
```

Stop with **Ctrl+C**.

Logs are written to `~/claude-images/clip2path.log` — useful when running as a background process.

---

## Auto-start with Claude Code

clip2path can launch automatically every time you open Claude Code using a `SessionStart` hook.

**Step 1** — Create `~/.claude/hooks/session-start-clip2path.sh`:

```bash
#!/usr/bin/env bash
# Start clip2path silently if no instance is already running

PID_FILE="$HOME/claude-images/clip2path.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    # Check if the process is still alive
    if kill -0 "$PID" 2>/dev/null; then
        exit 0  # Already running
    fi
fi

# Launch without a console window
pythonw "C:/Claude/clip2path/clip2path.py" start &
```

**Step 2** — Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "bash ~/.claude/hooks/session-start-clip2path.sh",
        "timeout": 5,
        "async": true
      }
    ]
  }
}
```

> **Note:** Adjust the path in the shell script to match where you placed `clip2path.py`.

---

## How it works

1. Polls clipboard every 500ms using `PIL.ImageGrab`
2. MD5-hashes image bytes in memory to skip duplicate saves
3. Writes `clip_YYYYMMDD_HHmmss.png` to the output folder
4. Copies the absolute path back to clipboard with `pyperclip`
5. Writes a PID file so the hook won't spawn duplicate instances

---

## Platform support

| Platform | Status |
|----------|--------|
| Windows 10 / 11 | ✅ Fully supported |
| macOS | ⚠️ Untested — `ImageGrab` should work |
| Linux | ❌ `ImageGrab.grabclipboard()` is not supported |

---

## Dependencies

| Package | Why |
|---------|-----|
| [Pillow](https://python-pillow.org) | `ImageGrab.grabclipboard()` — reads image from clipboard |
| [pyperclip](https://github.com/asweigart/pyperclip) | Writes the file path back to clipboard |

---

## License

MIT — see [LICENSE](LICENSE)

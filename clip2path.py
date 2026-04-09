"""
clip2path - clipboard watcher that saves images as PNG
and replaces the clipboard with the absolute file path.
"""

import argparse
import hashlib
import io
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import pyperclip
from PIL import ImageGrab

# Default output directory
DEFAULT_OUTPUT_DIR = Path.home() / "claude-images"

# Clipboard polling interval in seconds
POLL_INTERVAL = 0.5

# PID file used by the hook to avoid duplicate instances
PID_FILE = Path.home() / "claude-images" / "clip2path.pid"


def setup_logging(output_dir: Path) -> None:
    """Configure logging to file and optionally to stdout."""
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "clip2path.log"

    handlers: list[logging.Handler] = [
        logging.FileHandler(log_path, encoding="utf-8"),
    ]

    # Add console handler only when a real terminal is attached (not pythonw)
    if sys.stdout is not None:
        try:
            if sys.stdout.fileno() >= 0:
                handlers.append(logging.StreamHandler(sys.stdout))
        except (OSError, io.UnsupportedOperation):
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )


def compute_image_hash(image) -> str:
    """Return an MD5 hex digest of the PNG-encoded image bytes for dedup."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return hashlib.md5(buffer.getvalue(), usedforsecurity=False).hexdigest()  # noqa: S324


def generate_filename() -> str:
    """Return a timestamped filename: clip_YYYYMMDD_HHmmss.png."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"clip_{timestamp}.png"


def write_pid_file(output_dir: Path) -> None:
    """Write current PID to a lock file so the hook can detect a running instance."""
    pid_path = output_dir / "clip2path.pid"
    pid_path.write_text(str(os.getpid()), encoding="utf-8")


def remove_pid_file(output_dir: Path) -> None:
    """Remove the PID lock file on exit."""
    pid_path = output_dir / "clip2path.pid"
    try:
        pid_path.unlink(missing_ok=True)
    except OSError:
        pass


def handle_sigint(signum, frame) -> None:
    """Graceful shutdown on Ctrl+C."""
    logging.info("clip2path stopped.")
    sys.exit(0)


def start_watcher(output_dir: Path) -> None:
    """Start the clipboard polling loop."""
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(output_dir)
    write_pid_file(output_dir)

    logging.info("clip2path running — output: %s", output_dir)

    signal.signal(signal.SIGINT, handle_sigint)

    last_hash: str = ""

    try:
        while True:
            try:
                image = ImageGrab.grabclipboard()
            except Exception:
                # Clipboard temporarily unavailable — ignore and retry
                time.sleep(POLL_INTERVAL)
                continue

            if image is None or not hasattr(image, "save"):
                time.sleep(POLL_INTERVAL)
                continue

            current_hash = compute_image_hash(image)

            # Skip if same image as last saved (dedup)
            if current_hash == last_hash:
                time.sleep(POLL_INTERVAL)
                continue

            last_hash = current_hash

            filename = generate_filename()
            output_path = output_dir / filename

            try:
                image.save(output_path, format="PNG")
            except Exception as error:
                logging.error("Save failed: %s", error)
                time.sleep(POLL_INTERVAL)
                continue

            absolute_path = str(output_path.resolve())
            pyperclip.copy(absolute_path)

            logging.info("Saved → %s", absolute_path)

            time.sleep(POLL_INTERVAL)
    finally:
        remove_pid_file(output_dir)


def clear_output_dir(output_dir: Path) -> None:
    """Delete all clip_*.png files from the output directory."""
    if not output_dir.exists():
        print(f"Directory does not exist: {output_dir}")
        return

    png_files = list(output_dir.glob("clip_*.png"))

    if not png_files:
        print("Nothing to delete.")
        return

    for file in png_files:
        file.unlink()

    print(f"Deleted {len(png_files)} file(s) from {output_dir}")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="clip2path",
        description="Watch the clipboard and replace copied images with their file path.",
    )
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start", help="Start watching the clipboard")
    start_parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )

    clear_parser = subparsers.add_parser("clear", help="Delete saved images")
    clear_parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to clear (default: {DEFAULT_OUTPUT_DIR})",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "start":
        start_watcher(args.dir)
    elif args.command == "clear":
        clear_output_dir(args.dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

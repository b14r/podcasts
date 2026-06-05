#!/usr/bin/env python3
"""Compress every episodes/*.m4a to a low bitrate AAC, exactly once.

A marker is baked into each file's `comment` metadata tag after compression.
On later runs, files already carrying the marker are skipped, so episodes are
never re-compressed (which would degrade quality each pass).

Usage: python3 compress.py
Bitrate comes from config.json -> "compress_bitrate" (default 64k).
Requires ffmpeg + ffprobe on PATH.
"""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
EP_DIR = ROOT / "episodes"
MARKER = "podcast-compressed"


def bitrate():
    try:
        return json.loads((ROOT / "config.json").read_text()).get("compress_bitrate", "64k")
    except (FileNotFoundError, json.JSONDecodeError):
        return "64k"


def already_compressed(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags=comment",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return out.stdout.strip() == MARKER


def compress(path, br):
    tmp = path.with_suffix(".tmp.m4a")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(path),
         "-c:a", "aac", "-b:a", br,
         "-movflags", "+faststart",
         "-map_metadata", "0",
         "-metadata", f"comment={MARKER}",
         str(tmp)],
        check=True, capture_output=True, text=True,
    )
    os.replace(tmp, path)


def main():
    EP_DIR.mkdir(exist_ok=True)
    br = bitrate()
    changed = 0
    for f in sorted(EP_DIR.glob("*.m4a")):
        if already_compressed(f):
            print(f"skip (already compressed): {f.name}")
            continue
        before = f.stat().st_size
        print(f"compressing {f.name} @ {br} ...")
        compress(f, br)
        after = f.stat().st_size
        print(f"  {before//1024}KB -> {after//1024}KB")
        changed += 1
    print(f"Compressed {changed} file(s).")


if __name__ == "__main__":
    main()

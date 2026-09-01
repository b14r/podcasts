#!/usr/bin/env python3
"""Convert every episodes/*.{m4a,wav,mp3} to a low-bitrate MP3, exactly once.

MP3 is the one format every directory accepts (YouTube's RSS ingestion
rejects M4A/AAC). Output is episodes/<stem>.mp3; the source file is removed
after a successful conversion so the feed never sees duplicates.

A marker is baked into each MP3's `comment` tag after compression. On later
runs, files already carrying the marker are skipped, so episodes are never
re-compressed (which would degrade quality each pass).

Usage: python3 compress.py
Bitrate comes from config.json -> "compress_bitrate" (default 96k).
Requires ffmpeg (with libmp3lame) + ffprobe on PATH.
"""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
EP_DIR = ROOT / "episodes"
MARKER = "podcast-compressed"
SOURCE_EXTS = (".m4a", ".wav", ".mp3")


def bitrate():
    try:
        return json.loads((ROOT / "config.json").read_text()).get("compress_bitrate", "96k")
    except (FileNotFoundError, json.JSONDecodeError):
        return "96k"


def already_compressed(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags=comment",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return out.stdout.strip() == MARKER


def compress(src, dst, br):
    tmp = dst.with_suffix(".tmp.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-vn", "-c:a", "libmp3lame", "-b:a", br,
         "-map_metadata", "0", "-id3v2_version", "3",
         "-metadata", f"comment={MARKER}",
         str(tmp)],
        check=True, capture_output=True, text=True,
    )
    os.replace(tmp, dst)
    if src != dst:
        src.unlink()


def main():
    EP_DIR.mkdir(exist_ok=True)
    br = bitrate()
    changed = 0
    for f in sorted(EP_DIR.iterdir()):
        if f.suffix.lower() not in SOURCE_EXTS or f.name.endswith(".tmp.mp3"):
            continue
        if f.suffix.lower() == ".mp3" and already_compressed(f):
            print(f"skip (already compressed): {f.name}")
            continue
        dst = f.with_suffix(".mp3")
        before = f.stat().st_size
        print(f"compressing {f.name} -> {dst.name} @ {br} ...")
        compress(f, dst, br)
        after = dst.stat().st_size
        print(f"  {before//1024}KB -> {after//1024}KB")
        changed += 1
    print(f"Compressed {changed} file(s).")


if __name__ == "__main__":
    main()

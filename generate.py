#!/usr/bin/env python3
"""Scan episodes/ for .m4a files and build feed.xml (a podcast RSS feed).

Usage: python3 generate.py
Edit config.json first (set base_url to your GitHub Pages URL).

Per-episode metadata is optional. To override the auto-generated title or add
notes, create a sidecar .json next to the audio file, e.g.:

    episodes/001-intro.m4a
    episodes/001-intro.json   ->  {"title": "Intro", "description": "..."}
"""
import json
import os
import subprocess
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).parent
EP_DIR = ROOT / "episodes"
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"


def load_config():
    cfg = json.loads((ROOT / "config.json").read_text())
    cfg["base_url"] = cfg["base_url"].rstrip("/")
    if "USERNAME" in cfg["base_url"] or "REPO" in cfg["base_url"]:
        print("!! Edit config.json: set base_url to your real GitHub Pages URL.")
    return cfg


def git_added_date(path):
    """Date the file was first committed (stable across machines/checkouts).

    File mtimes are NOT preserved by git, so they're useless for ordering in CI.
    The original add-commit date is deterministic everywhere. Returns None for
    files not yet committed (brand-new episodes) -> caller falls back to mtime.
    """
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%aI", "--", str(path)],
            capture_output=True, text=True, cwd=ROOT,
        )
        lines = [l for l in out.stdout.splitlines() if l.strip()]
        if not lines:
            return None
        # last line = the original add commit (oldest)
        return datetime.fromisoformat(lines[-1])
    except (ValueError, OSError, subprocess.SubprocessError):
        return None


def ffprobe_duration(path):
    """Return duration in seconds, or None if ffprobe unavailable."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return int(float(out.stdout.strip()))
    except (FileNotFoundError, ValueError, subprocess.SubprocessError):
        return None


def fmt_duration(secs):
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def gather_episodes(cfg):
    eps = []
    for f in sorted(EP_DIR.glob("*.m4a")):
        stat = f.stat()
        meta = {}
        sidecar = f.with_suffix(".json")
        if sidecar.exists():
            meta = json.loads(sidecar.read_text())
        pub = git_added_date(f) or datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        dur = ffprobe_duration(f)
        eps.append({
            "title": meta.get("title", f.stem.replace("_", " ").strip()),
            "description": meta.get("description", ""),
            "url": f"{cfg['base_url']}/episodes/{f.name}",
            "length": stat.st_size,
            "guid": f.name,
            "_pub": pub,
            "pubDate": format_datetime(pub),
            "duration": fmt_duration(dur) if dur else None,
        })
    # newest first (sort by datetime, NOT the RFC-822 string)
    eps.sort(key=lambda e: e["_pub"], reverse=True)
    return eps


def build_feed(cfg, eps):
    e = escape
    explicit = "true" if cfg.get("explicit") else "false"
    cover = f"{cfg['base_url']}/{cfg.get('cover', 'cover.jpg')}"
    now = format_datetime(datetime.now(timezone.utc))

    items = []
    for ep in eps:
        dur = f'\n      <itunes:duration>{ep["duration"]}</itunes:duration>' if ep["duration"] else ""
        desc = f"\n      <description>{e(ep['description'])}</description>" if ep["description"] else ""
        items.append(f"""    <item>
      <title>{e(ep['title'])}</title>{desc}
      <enclosure url="{e(ep['url'])}" length="{ep['length']}" type="audio/x-m4a"/>
      <guid isPermaLink="false">{e(ep['guid'])}</guid>
      <pubDate>{ep['pubDate']}</pubDate>{dur}
    </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="{ITUNES_NS}">
  <channel>
    <title>{e(cfg['title'])}</title>
    <link>{e(cfg['base_url'])}</link>
    <language>{e(cfg.get('language', 'en-us'))}</language>
    <description>{e(cfg['description'])}</description>
    <lastBuildDate>{now}</lastBuildDate>
    <itunes:author>{e(cfg['author'])}</itunes:author>
    <itunes:summary>{e(cfg['description'])}</itunes:summary>
    <itunes:explicit>{explicit}</itunes:explicit>
    <itunes:category text="{e(cfg.get('category', 'Technology'))}"/>
    <itunes:image href="{e(cover)}"/>
    <itunes:owner>
      <itunes:name>{e(cfg['author'])}</itunes:name>
      <itunes:email>{e(cfg.get('email', ''))}</itunes:email>
    </itunes:owner>
    <image>
      <url>{e(cover)}</url>
      <title>{e(cfg['title'])}</title>
      <link>{e(cfg['base_url'])}</link>
    </image>
{chr(10).join(items)}
  </channel>
</rss>
"""


def main():
    cfg = load_config()
    EP_DIR.mkdir(exist_ok=True)
    eps = gather_episodes(cfg)
    feed = build_feed(cfg, eps)
    (ROOT / "feed.xml").write_text(feed)
    print(f"Wrote feed.xml with {len(eps)} episode(s).")
    if not eps:
        print("Drop .m4a files into episodes/ then run again.")


if __name__ == "__main__":
    main()

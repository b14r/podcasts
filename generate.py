#!/usr/bin/env python3
"""Scan episodes/ for .mp3 files and build feed.xml (a podcast RSS feed).

Usage: python3 generate.py
Edit config.json first (set base_url to your GitHub Pages URL).

Per-episode metadata is optional. To override the auto-generated title or add
notes, create a sidecar .json next to the audio file, e.g.:

    episodes/001-intro.mp3
    episodes/001-intro.json   ->  {"title": "Intro", "description": "..."}

Per-episode artwork: episodes/001-intro.jpg (see episode_art.py) is emitted
as <itunes:image> on the item when present.
"""
import hashlib
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
    """Date the episode was first committed (stable across machines/checkouts).

    File mtimes are NOT preserved by git, so they're useless for ordering in CI.
    The original add-commit date is deterministic everywhere. Returns None for
    files not yet committed (brand-new episodes) -> caller falls back to mtime.
    Episodes were .m4a before the MP3 switch, so the legacy path is checked too
    and the oldest date wins.
    """
    dates = []
    for p in (path, path.with_suffix(".m4a")):
        try:
            out = subprocess.run(
                ["git", "log", "--diff-filter=A", "--format=%aI", "--", str(p)],
                capture_output=True, text=True, cwd=ROOT,
            )
            lines = [l for l in out.stdout.splitlines() if l.strip()]
            if lines:
                dates.append(datetime.fromisoformat(lines[-1]))  # last = original add
        except (ValueError, OSError, subprocess.SubprocessError):
            pass
    return min(dates) if dates else None


def img_url(cfg, rel_path):
    """URL for an image with a content-hash query so apps refetch when it changes."""
    p = ROOT / rel_path
    h = hashlib.sha1(p.read_bytes()).hexdigest()[:8] if p.exists() else "0"
    return f"{cfg['base_url']}/{rel_path}?v={h}"


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
    for f in sorted(EP_DIR.glob("*.mp3")):
        stat = f.stat()
        meta = {}
        sidecar = f.with_suffix(".json")
        if sidecar.exists():
            meta = json.loads(sidecar.read_text())
        pub = git_added_date(f) or datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        dur = ffprobe_duration(f)
        img = f.with_suffix(".jpg")
        eps.append({
            "image": img_url(cfg, f"episodes/{img.name}") if img.exists() else None,
            "title": meta.get("title", f.stem.replace("_", " ").strip()),
            "description": meta.get("description", ""),
            "url": f"{cfg['base_url']}/episodes/{f.name}",
            "length": stat.st_size,
            "guid": f.stem,
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
    cover = img_url(cfg, cfg.get('cover', 'cover.jpg'))
    now = format_datetime(datetime.now(timezone.utc))

    items = []
    for ep in eps:
        dur = f'\n      <itunes:duration>{ep["duration"]}</itunes:duration>' if ep["duration"] else ""
        desc = f"\n      <description>{e(ep['description'])}</description>" if ep["description"] else ""
        img = f'\n      <itunes:image href="{e(ep["image"])}"/>' if ep["image"] else ""
        items.append(f"""    <item>
      <title>{e(ep['title'])}</title>{desc}
      <enclosure url="{e(ep['url'])}" length="{ep['length']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{e(ep['guid'])}</guid>
      <pubDate>{ep['pubDate']}</pubDate>{dur}{img}
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
        print("Drop audio files into episodes/ then run again.")


if __name__ == "__main__":
    main()

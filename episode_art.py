#!/usr/bin/env python3
"""Render per-episode artwork: episodes/<Name>.jpg for every episodes/<Name>.m4a.

Design (see CLAUDE.md): black background, a cross on top, the episode title big
in UnifrakturMaguntia, the podcast name small at the bottom. 3000x3000 JPG.

Sidecar options (episodes/<Name>.json):
    "title": "..."          episode title (falls back to filename)
    "cross": "latin"        one of: latin, jerusalem, maltese, pattee, lorraine

Usage:
    python3 episode_art.py            # render missing images only
    python3 episode_art.py --force    # re-render everything

Needs Google Chrome (headless) + macOS `sips`. Skips gracefully if Chrome is
missing (CI), since the images are committed to the repo.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
EP_DIR = ROOT / "episodes"
SIZE = 3000

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chromium-browser",
]

CROSSES = {
    "pattee": '<g id="c"><path d="M-10 0L-46-98H46L10 0z"/></g>'
              '<use href="#c" transform="rotate(90)"/><use href="#c" transform="rotate(180)"/><use href="#c" transform="rotate(270)"/>',
    "maltese": '<g id="c"><path d="M0 0L-50-100L0-74L50-100z"/></g>'
               '<use href="#c" transform="rotate(90)"/><use href="#c" transform="rotate(180)"/><use href="#c" transform="rotate(270)"/>',
    "jerusalem": '<rect x="-13" y="-92" width="26" height="184"/><rect x="-92" y="-13" width="184" height="26"/>'
                 '<rect x="-46" y="-104" width="92" height="24"/><rect x="-46" y="80" width="92" height="24"/>'
                 '<rect x="-104" y="-46" width="24" height="92"/><rect x="80" y="-46" width="24" height="92"/>'
                 '<g id="c"><rect x="-6" y="-24" width="12" height="48"/><rect x="-24" y="-6" width="48" height="12"/></g>'
                 '<use href="#c" transform="translate(-56,-56)"/><use href="#c" transform="translate(56,-56)"/>'
                 '<use href="#c" transform="translate(-56,56)"/><use href="#c" transform="translate(56,56)"/>',
    "latin": '<rect x="-14" y="-100" width="28" height="200"/><rect x="-70" y="-50" width="140" height="28"/>',
    "lorraine": '<rect x="-13" y="-100" width="26" height="200"/><rect x="-46" y="-68" width="92" height="24"/>'
                '<rect x="-74" y="-16" width="148" height="24"/>',
}

TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&display=swap" rel="stylesheet">
<style>
html,body{{margin:0;width:{S}px;height:{S}px;overflow:hidden;background:#000}}
.cross{{position:absolute;left:50%;top:300px;transform:translateX(-50%)}}
.rule{{position:absolute;left:50%;transform:translateX(-50%);width:1500px;height:10px;background:#fff}}
.r1{{top:760px}}.r2{{top:2260px}}
.title{{position:absolute;left:150px;width:2700px;top:830px;height:1370px;display:flex;align-items:center;justify-content:center;
  text-align:center;font-family:'UnifrakturMaguntia',serif;color:#fff;line-height:1.02;font-size:560px;text-wrap:balance}}
.show{{position:absolute;left:0;right:0;top:2380px;text-align:center;font-family:'UnifrakturMaguntia',serif;font-size:210px;color:#fff}}
</style></head><body>
<svg class="cross" width="420" height="420" viewBox="-110 -110 220 220" fill="#fff">{CROSS}</svg>
<div class="rule r1"></div>
<div class="title"><div id="t">{TITLE}</div></div>
<div class="rule r2"></div>
<div class="show">{SHOW}</div>
<script>
document.fonts.ready.then(()=>{{
  const box=document.querySelector('.title'), t=document.getElementById('t');
  let fs=560;
  while(fs>120 && (t.scrollHeight>box.clientHeight || t.scrollWidth>box.clientWidth)){{fs-=10; box.style.fontSize=fs+'px';}}
  document.title='ready';
}});
</script>
</body></html>
"""


def find_chrome():
    for c in CHROME_CANDIDATES:
        if Path(c).exists() or shutil.which(c):
            return c
    return None


def render(chrome, html_path, out_jpg):
    with tempfile.TemporaryDirectory() as td:
        png = Path(td) / "out.png"
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--allow-file-access-from-files", "--virtual-time-budget=10000",
             f"--window-size={SIZE},{SIZE}", f"--screenshot={png}",
             f"file://{html_path}"],
            check=True, capture_output=True, timeout=120,
        )
        subprocess.run(
            ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90",
             str(png), "--out", str(out_jpg)],
            check=True, capture_output=True, timeout=60,
        )


def main():
    force = "--force" in sys.argv
    chrome = find_chrome()
    if not chrome:
        print("episode_art: Chrome not found, skipping (images are committed).")
        return
    show = json.loads((ROOT / "config.json").read_text())["title"]
    done = 0
    for f in sorted(EP_DIR.glob("*.m4a")):
        jpg = f.with_suffix(".jpg")
        if jpg.exists() and not force:
            continue
        meta = {}
        sidecar = f.with_suffix(".json")
        if sidecar.exists():
            meta = json.loads(sidecar.read_text())
        title = meta.get("title", f.stem.replace("_", " ").strip())
        cross = CROSSES.get(meta.get("cross", "latin"), CROSSES["latin"])
        html = TEMPLATE.format(S=SIZE, CROSS=cross, TITLE=escape(title), SHOW=escape(show))
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tf:
            tf.write(html)
            html_path = Path(tf.name)
        try:
            print(f"rendering {jpg.name} ({meta.get('cross', 'latin')} cross) ...")
            render(chrome, html_path, jpg)
            done += 1
        finally:
            html_path.unlink(missing_ok=True)
    print(f"Rendered {done} image(s).")


if __name__ == "__main__":
    main()

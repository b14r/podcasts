# My Podcast

Self-hosted podcast feed served as static files from GitHub Pages.

## Setup (once)

1. **Edit `config.json`** — set `base_url` to your GitHub Pages URL, e.g.
   `https://yourname.github.io/podcasts`. Fill in title/author/email.
2. **Add cover art** — drop a square `cover.jpg` (1400×1400 to 3000×3000 px,
   required by Apple Podcasts) in the repo root.
3. **Enable GitHub Pages** — repo Settings → Pages → deploy from `main` branch,
   `/ (root)` folder.

## Add an episode

1. Copy your `.m4a` file into `episodes/`. Name it sortably, e.g.
   `001-intro.m4a`. The filename (without extension) becomes the title.
2. *(Optional)* Override metadata with a sidecar JSON of the same name:
   ```json
   // episodes/001-intro.json
   { "title": "Intro", "description": "First episode." }
   ```
3. Rebuild and publish:
   ```sh
   python3 generate.py
   git add -A && git commit -m "Add episode" && git push
   ```

## Notes

- `pubDate` comes from each file's modified time. Newest shows first.
- Episode **duration** tags are added automatically if `ffprobe`
  (from ffmpeg) is installed; otherwise skipped (apps still work).
- No dependencies — pure Python 3 stdlib.
- Subscribe URL is `<base_url>/feed.xml`.

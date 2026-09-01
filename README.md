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

1. Copy your audio (`.m4a`, `.wav` or `.mp3`) into `episodes/`. It is converted
   to a 96k MP3 on publish (YouTube RSS ingestion only accepts MP3). The
   filename (without extension) becomes the title.
2. *(Optional)* Override metadata with a sidecar JSON of the same name:
   ```json
   // episodes/001-intro.json
   { "title": "Intro", "description": "First episode." }
   ```
3. Publish:
   ```sh
   ./publish.sh "Add episode: Title"
   ```

## Notes

- `pubDate` comes from the file's first git commit date. Newest shows first.
- Episode **duration** tags are added automatically if `ffprobe`
  (from ffmpeg) is installed; otherwise skipped (apps still work).
- No dependencies — pure Python 3 stdlib.
- Subscribe URL is `<base_url>/feed.xml`.

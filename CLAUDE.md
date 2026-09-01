# Battles of Christendom — podcast repo

Static podcast feed on GitHub Pages. `./publish.sh "msg"` = compress new audio → rebuild `feed.xml` → commit → push. CI (`.github/workflows/build.yml`) does the same on push as safety net.

- Episodes: `episodes/<Name>.m4a` + sidecar `<Name>.json` (`{"title": "...", "description": "..."}`). Always add a sidecar with a proper title (underscores → spaces is the fallback, punctuation gets lost).
- Feed order = git add-date of the audio file, newest first.
- Config: `config.json` (title, author, description, base_url, cover).
- Show cover: `cover.jpg` (3000×3000). Source is `cover.source.html` — render with headless Chrome:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files --virtual-time-budget=8000 --window-size=3000,3000 --screenshot=out.png file://$PWD/cover.source.html` then `sips -s format jpeg -s formatOptions 92 out.png --out cover.jpg`.

## Visual identity

- Background: pure black `#000`.
- Title font: **UnifrakturMaguntia** (Google Fonts, blackletter). Tagline/small text: **Cinzel** 600, letter-spaced, uppercase.
- Text color: white `#fff`. No gradients, no gold, no textures. Thin white rules (5px at 3000px canvas) frame the title.
- Show cover: row of five crosses on top (Templar pattée, Maltese, Jerusalem, Latin, Lorraine), rule, "Battles of" / "Christendom", rule, tagline "SIEGES · CRUSADES · MARTYRS".

## Per-episode artwork (spec)

Every episode gets its own square image, same design language as the show cover:

1. Black background.
2. A Christian symbol on top — a cross, ideally one that fits the episode (Maltese for Hospitallers/Malta, Jerusalem for the Crusader kingdom, pattée for Templars, Latin as default).
3. Episode title, big, in UnifrakturMaguntia, white, centered. Long titles wrap; scale font down to fit.
4. Podcast name "Battles of Christendom" at the bottom, smaller, same blackletter (or Cinzel caps).
5. Output: `episodes/<Name>.jpg`, 3000×3000 (min 1400), RGB, < 500 KB. `generate.py` should emit `<itunes:image href>` per `<item>` when the jpg exists.

Keep it very simple — no illustrations, no borders beyond thin rules.

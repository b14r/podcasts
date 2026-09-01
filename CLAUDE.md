# Battles of Christendom — podcast repo

Static podcast feed on GitHub Pages. `./publish.sh "msg"` = compress new audio → rebuild `feed.xml` → commit → push. CI (`.github/workflows/build.yml`) does the same on push as safety net.

- Episodes: `episodes/<Name>.mp3` (drop `.m4a`/`.wav`/`.mp3`; `compress.py` converts to 96k MP3 and deletes the source — MP3 because YouTube RSS ingestion rejects M4A) + sidecar `<Name>.json` (`{"title": "...", "description": "..."}`). Always add a sidecar with a proper title (underscores → spaces is the fallback, punctuation gets lost).
- Feed order = git add-date of the audio file (legacy `.m4a` path checked too), newest first. GUID = filename stem.
- Config: `config.json` (title, author, description, base_url, cover).
- Show cover: `cover.jpg` (3000×3000). Source is `cover.source.html` — render with headless Chrome:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files --virtual-time-budget=8000 --window-size=3000,3000 --screenshot=out.png file://$PWD/cover.source.html` then `sips -s format jpeg -s formatOptions 92 out.png --out cover.jpg`.

## Visual identity

- Background: pure black `#000`.
- Title font: **UnifrakturMaguntia** (Google Fonts, blackletter). Tagline/small text: **Cinzel** 600, letter-spaced, uppercase.
- Text color: white `#fff`. No gradients, no gold, no textures. Thin white rules (5px at 3000px canvas) frame the title.
- Show cover: row of five crosses on top (Templar pattée, Maltese, Jerusalem, Latin, Lorraine), rule, "Battles of" / "Christendom", rule, tagline "SIEGES · CRUSADES · MARTYRS".

## Per-episode artwork

`episode_art.py` renders `episodes/<Name>.jpg` for any episode missing one (runs inside `publish.sh`; `--force` re-renders all). Pick the cross with `"cross": "maltese"` etc. in the sidecar. `generate.py` emits `<itunes:image>` per item when the jpg exists. Design:

1. Black background.
2. A Christian symbol on top — a cross, ideally one that fits the episode (Maltese for Hospitallers/Malta, Jerusalem for the Crusader kingdom, pattée for Templars, Latin as default).
3. Episode title, big, in UnifrakturMaguntia, white, centered. Long titles wrap; scale font down to fit.
4. Podcast name "Battles of Christendom" at the bottom, smaller, same blackletter (or Cinzel caps).
5. Output: `episodes/<Name>.jpg`, 3000×3000, RGB, ~400 KB.

Keep it very simple — no illustrations, no borders beyond thin rules.

## Content plan

- **First Crusade 4-part series** (overview episode was deleted; these replace it). Filenames/titles, all `"cross": "lorraine"`:
  1. `The_First_Crusade_I_Clermont_1095.mp3` → "The First Crusade I: Clermont & the People's Crusade, 1096"
  2. `The_First_Crusade_II_Dorylaeum_1097.mp3` → "The First Crusade II: Nicaea & Dorylaeum, 1097"
  3. `The_First_Crusade_III_Antioch_1098.mp3` → "The First Crusade III: The Siege of Antioch, 1098"
  4. `The_First_Crusade_IV_Jerusalem_1099.mp3` → "The First Crusade IV: The Fall of Jerusalem, 1099"
- Episode queue after that: Lepanto 1571 → Belgrade 1456 → Las Navas de Tolosa 1212 → Tours 732 → Aljubarrota 1385. Prefer victories; avoid stacking defeats (user request). Hattin 1187 reserved as tragic lead-in to a Third Crusade series.
- Title format: "battle name, year" (e.g. "The Great Siege of Malta, 1565").
- Deleted episodes (recoverable from git history at `77ea00e`): First Crusade overview, Shimabara Rebellion.

## Distribution

- Live on Apple Podcasts + Spotify (auto-refresh from feed). YouTube: RSS ingestion pending user ID verification → Studio → Create → New podcast → Submit RSS feed. MP3-only pipeline exists because YouTube rejects M4A.
- Apple transcripts: rely on Apple's auto-transcription (user choice; no podcast:transcript tag).
- Header/background colors in apps are auto-derived from cover art — not settable.

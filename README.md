# 📻 Terminus Radio — Full-Featured TUI

## Setup (Termux — one-time)

```bash
pkg install mpv ffmpeg
pip install textual python-mpv
python radio.py
```

## Features

| Feature | Details |
|---|---|
| 🔍 Search | Live search across all stations by name or genre |
| 📂 Categories | All · News · Music · Electronic · Hip-Hop · Jazz · Classical · Pop · Local · Education · Favorites · Custom |
| ▶ Playback | Stream via mpv — any format (mp3, aac, hls) |
| 🔊 Volume | 0–130%, fine-tune with `[`/`]`, mute with `0` |
| ★ Favorites | Toggle with `F`, persisted to `~/.terminus_radio/favorites.json` |
| 🎛 EQ | 6 presets: Flat / Bass Boost / Treble Boost / Vocal / Night Mode / Pop |
| 📊 Metadata | Song title + live bitrate from stream |
| ⏺ Recording | Records via ffmpeg to `~/.terminus_radio/recordings/` |
| ➕ Add Station | Press `A` to add custom stations (persisted) |

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Play selected |
| `S` | Stop |
| `N` / `P` | Next / Previous station |
| `+` / `-` | Volume ±5% |
| `]` / `[` | Volume ±1% |
| `0` | Mute / Unmute |
| `F` | Toggle favorite |
| `E` / `Shift+E` | Cycle EQ preset |
| `R` | Start recording |
| `Shift+R` | Stop recording |
| `/` | Focus search |
| `Esc` | Clear search |
| `A` | Add custom station |
| `?` | Full help screen |
| `Q` | Quit |

## Data locations

```
~/.terminus_radio/
├── favorites.json       # saved favorites
├── custom_stations.json # added stations
└── recordings/          # recorded streams (mp3)
```

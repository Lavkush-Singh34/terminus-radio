# 📻 Terminus Radio — TUI Radio Player

A full-featured terminal radio player built with Python + Textual + mpv.

## Setup (Termux)

```bash
# 1. Install mpv (if not already installed)
pkg install mpv

# 2. Install Python dependencies
pip install textual python-mpv

# 3. Run the app
python radio.py
```

## Setup (Linux/Desktop)

```bash
# 1. Install mpv
sudo apt install mpv        # Debian/Ubuntu
sudo pacman -S mpv          # Arch
brew install mpv            # macOS

# 2. Install Python dependencies
pip install textual python-mpv

# 3. Run
python radio.py
```

## Keyboard Shortcuts

| Key         | Action           |
|-------------|------------------|
| `ENTER`     | Play selected    |
| `S`         | Stop playback    |
| `+` / `=`   | Volume up        |
| `-`         | Volume down      |
| `↑` / `↓`  | Navigate list    |
| `R`         | Refresh list     |
| `Q`         | Quit             |

## Adding More Stations

Edit the `STATIONS` list in `radio.py`:

```python
{
    "name": "My Station",
    "genre": "Pop",
    "url": "https://stream.example.com/radio",
    "country": "🇮🇳",
    "bitrate": "128k",
},
```

## Features

- 🎵 Live ICY metadata (song title from stream)
- 🔊 Volume control (0–100%)
- 📡 10 pre-loaded stations across genres
- ⏱ Live elapsed time counter
- 🌊 Animated waveform while playing
- ⌨️ Full keyboard navigation
- 🖱 Click to play

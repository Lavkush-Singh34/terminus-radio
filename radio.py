#!/usr/bin/env python3
"""
████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗██╗   ██╗███████╗
╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██║   ██║██╔════╝
   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║██║   ██║███████╗
   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██║   ██║╚════██║
   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝███████║
   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝
                     R A D I O  —  Full-Featured TUI

Install:
    pkg install mpv ffmpeg          (Termux)
    pip install textual python-mpv  (both)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (Button, Input, Label, ListItem, ListView,
                             Static, TabbedContent, TabPane)

try:
    import mpv
    MPV_AVAILABLE = True
except ImportError:
    MPV_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
#  PATHS
# ══════════════════════════════════════════════════════════════════════════════

APP_DIR     = Path.home() / ".terminus_radio"
FAV_FILE    = APP_DIR / "favorites.json"
REC_DIR     = APP_DIR / "recordings"
CUSTOM_FILE = APP_DIR / "custom_stations.json"
APP_DIR.mkdir(exist_ok=True)
REC_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
#  STATION DATABASE
# ══════════════════════════════════════════════════════════════════════════════

BUILTIN_STATIONS: list[dict] = [
    # Education
    {"name": "Clye Education",        "genre": "Education",       "category": "Education",  "country": "🌍", "bitrate": "128k", "url": "https://eu8.fastcast4u.com/proxy/clyedupq?mp=%2F1?aw_0_req_lsid=2c0fae177108c9a42a7cf24878625444"},
    # News
    {"name": "BBC World Service",     "genre": "News",            "category": "News",       "country": "🇬🇧", "bitrate": "128k", "url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"},
    {"name": "NPR News",              "genre": "News",            "category": "News",       "country": "🇺🇸", "bitrate": "128k", "url": "https://npr-ice.streamguys1.com/live.mp3"},
    {"name": "France 24 (EN)",        "genre": "News",            "category": "News",       "country": "🇫🇷", "bitrate": "128k", "url": "http://icecast.france24.com/france24_en-mid-mp3"},
    {"name": "DW Radio (EN)",         "genre": "News",            "category": "News",       "country": "🇩🇪", "bitrate": "128k", "url": "https://icecast.dw.com/dw/en/icecast.audio"},
    # Music – Rock / Indie
    {"name": "Radio Paradise",        "genre": "Rock / Eclectic", "category": "Music",      "country": "🇺🇸", "bitrate": "128k", "url": "https://stream.radioparadise.com/aac-128"},
    {"name": "KEXP 90.3 FM",          "genre": "Indie / Alt",     "category": "Music",      "country": "🇺🇸", "bitrate": "64k",  "url": "https://live-aacplus-64.kexp.org/kexp64.aac"},
    {"name": "NTS Radio 1",           "genre": "Experimental",    "category": "Music",      "country": "🇬🇧", "bitrate": "128k", "url": "https://stream-relay-geo.ntslive.net/stream"},
    # Electronic / Ambient
    {"name": "SomaFM — Groove Salad", "genre": "Ambient",         "category": "Electronic", "country": "🇺🇸", "bitrate": "128k", "url": "https://ice6.somafm.com/groovesalad-128-mp3"},
    {"name": "SomaFM — Drone Zone",   "genre": "Ambient / Space", "category": "Electronic", "country": "🇺🇸", "bitrate": "128k", "url": "https://ice6.somafm.com/dronezone-128-mp3"},
    {"name": "SomaFM — DEF CON",      "genre": "Electronica",     "category": "Electronic", "country": "🇺🇸", "bitrate": "128k", "url": "https://ice6.somafm.com/defcon-128-mp3"},
    # Hip-Hop / Lo-Fi
    {"name": "Chillhop Radio",        "genre": "Lo-Fi / Hip-Hop", "category": "Hip-Hop",    "country": "🌍", "bitrate": "128k", "url": "https://stream.chillhop.com/hls/chillhop.m3u8"},
    {"name": "Lofi Girl",             "genre": "Lo-Fi",           "category": "Hip-Hop",    "country": "🌍", "bitrate": "128k", "url": "http://stream.zeno.fm/0r0xa792kwzuv"},
    # Jazz
    {"name": "Radio Swiss Jazz",      "genre": "Jazz",            "category": "Jazz",       "country": "🇨🇭", "bitrate": "128k", "url": "http://stream.srg-ssr.ch/m/rsj/mp3_128"},
    {"name": "WBGO Jazz 88.3",        "genre": "Jazz",            "category": "Jazz",       "country": "🇺🇸", "bitrate": "128k", "url": "https://wbgo.streamguys1.com/wbgo128"},
    # Classical
    {"name": "Radio Swiss Classic",   "genre": "Classical",       "category": "Classical",  "country": "🇨🇭", "bitrate": "128k", "url": "http://stream.srg-ssr.ch/m/rsc_de/mp3_128"},
    {"name": "Classic FM (UK)",       "genre": "Classical",       "category": "Classical",  "country": "🇬🇧", "bitrate": "128k", "url": "http://media-ice.musicradio.com/ClassicFMMP3"},
    # Pop
    {"name": "Virgin Radio UK",       "genre": "Pop / Top 40",    "category": "Pop",        "country": "🇬🇧", "bitrate": "128k", "url": "http://icecast.thisisdax.com/VirginRadioUK"},
    {"name": "Radio One (Canada)",    "genre": "Pop / Hits",      "category": "Pop",        "country": "🇨🇦", "bitrate": "128k", "url": "https://cbcmp3.ic.cbc.ca/cbcradioone"},
    # Local / Indian
    {"name": "All India Radio",       "genre": "Indian Classical", "category": "Local",     "country": "🇮🇳", "bitrate": "128k", "url": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio001/playlist.m3u8"},
    {"name": "AIR FM Rainbow",        "genre": "Bollywood",       "category": "Local",      "country": "🇮🇳", "bitrate": "128k", "url": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio012/playlist.m3u8"},
]

CATEGORIES = ["All", "News", "Music", "Electronic", "Hip-Hop", "Jazz",
               "Classical", "Pop", "Local", "Education", "Favorites", "Custom"]

# ══════════════════════════════════════════════════════════════════════════════
#  EQ PRESETS
# ══════════════════════════════════════════════════════════════════════════════

EQ_PRESETS: dict[str, str] = {
    "Flat":        "",
    "Bass Boost":  "lavfi=[equalizer=f=80:width_type=o:w=2:g=6,equalizer=f=200:width_type=o:w=2:g=3]",
    "Treble Boost":"lavfi=[equalizer=f=8000:width_type=o:w=2:g=5,equalizer=f=16000:width_type=o:w=2:g=4]",
    "Vocal":       "lavfi=[equalizer=f=300:width_type=o:w=1:g=-3,equalizer=f=3000:width_type=o:w=1:g=5]",
    "Night Mode":  "lavfi=[equalizer=f=8000:width_type=o:w=2:g=-6,equalizer=f=16000:width_type=o:w=2:g=-8]",
    "Pop":         "lavfi=[equalizer=f=60:width_type=o:w=2:g=3,equalizer=f=3000:width_type=o:w=1:g=4,equalizer=f=12000:width_type=o:w=2:g=3]",
}
EQ_NAMES = list(EQ_PRESETS.keys())

# ══════════════════════════════════════════════════════════════════════════════
#  VISUALIZER FRAMES
# ══════════════════════════════════════════════════════════════════════════════

VIZ = [
    "▁▃▅▇█▇▅▃▁▂▄▆█▆▄▂",
    "▂▄▆█▆▄▂▁▃▅▇█▇▅▃▁",
    "▃▅▇█▇▅▃▁▂▄▆█▆▄▂▁",
    "▄▆█▆▄▂▁▃▅▇█▇▅▃▁▂",
    "▅▇█▇▅▃▁▂▄▆█▆▄▂▁▃",
    "▆█▆▄▂▁▃▅▇█▇▅▃▁▂▄",
    "▇█▇▅▃▁▂▄▆█▆▄▂▁▃▅",
    "█▇▅▃▁▂▄▆█▆▄▂▁▃▅▇",
    "▇▅▃▁▂▄▆█▆▄▂▁▃▅▇█",
    "▅▃▁▂▄▆█▆▄▂▁▃▅▇█▇",
    "▃▁▂▄▆█▆▄▂▁▃▅▇█▇▅",
    "▁▂▄▆█▆▄▂▁▃▅▇█▇▅▃",
]

# ══════════════════════════════════════════════════════════════════════════════
#  PERSISTENCE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default

def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

# ══════════════════════════════════════════════════════════════════════════════
#  MPV PLAYER WRAPPER
# ══════════════════════════════════════════════════════════════════════════════

class RadioPlayer:
    def __init__(self):
        self.player      = None
        self.is_playing  = False
        self.volume      = 70
        self.eq_preset   = "Flat"
        self._on_song    = None
        self._on_bitrate = None

        if MPV_AVAILABLE:
            self.player = mpv.MPV(
                ytdl=False,
                input_default_bindings=False,
                input_vo_keyboard=False,
                video=False,
                terminal=False,
                really_quiet=True,
            )
            self.player.volume = self.volume

            @self.player.property_observer("media-title")
            def _title(name, value):
                if self._on_song and value:
                    self._on_song(str(value))

            @self.player.property_observer("audio-bitrate")
            def _br(name, value):
                if self._on_bitrate and value:
                    self._on_bitrate(f"{int(value/1000)} kbps")

    def play(self, url: str):
        if not self.player:
            return
        self.player.play(url)
        self.player.volume = self.volume
        self.is_playing = True

    def stop(self):
        if self.player:
            self.player.stop()
        self.is_playing = False

    def set_volume(self, v: int):
        self.volume = max(0, min(130, v))
        if self.player:
            self.player.volume = self.volume

    def vol_up(self, n=5): self.set_volume(self.volume + n)
    def vol_dn(self, n=5): self.set_volume(self.volume - n)

    def set_eq(self, name: str):
        self.eq_preset = name
        af = EQ_PRESETS.get(name, "")
        if self.player:
            try:
                self.player.af = af if af else ""
            except Exception:
                pass

    def record(self, url: str, outpath: str) -> Optional[subprocess.Popen]:
        try:
            return subprocess.Popen(
                ["ffmpeg", "-y", "-i", url, "-acodec", "copy", outpath],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            return None

    def quit(self):
        if self.player:
            try:
                self.player.stop()
                self.player.terminate()
            except Exception:
                pass

# ══════════════════════════════════════════════════════════════════════════════
#  MODAL SCREENS
# ══════════════════════════════════════════════════════════════════════════════

class AddStationScreen(ModalScreen):
    CSS = """
    AddStationScreen { align: center middle; }
    #dlg {
        width: 58; height: 22;
        border: double #58a6ff;
        background: #0d1117;
        padding: 1 2;
    }
    #dlg-title { color: #58a6ff; text-style: bold; margin-bottom: 1; }
    #dlg Label { color: #8b949e; height: 1; }
    #dlg Input { margin-bottom: 1; background: #161b22; border: tall #30363d; color: #c9d1d9; }
    #dlg Input:focus { border: tall #58a6ff; }
    #btn-row { height: 3; align: center middle; margin-top: 1; }
    Button { margin: 0 1; }
    """
    def compose(self) -> ComposeResult:
        with Container(id="dlg"):
            yield Label("➕  Add Custom Station", id="dlg-title")
            yield Label("Station Name")
            yield Input(placeholder="My Station", id="i-name")
            yield Label("Stream URL")
            yield Input(placeholder="https://stream.example.com/live.mp3", id="i-url")
            yield Label("Genre")
            yield Input(placeholder="Pop", id="i-genre")
            yield Label("Country emoji (optional)")
            yield Input(placeholder="🌍", id="i-flag")
            with Horizontal(id="btn-row"):
                yield Button("✓  Add", variant="primary", id="btn-ok")
                yield Button("✕  Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
            return
        name  = self.query_one("#i-name",  Input).value.strip()
        url   = self.query_one("#i-url",   Input).value.strip()
        genre = self.query_one("#i-genre", Input).value.strip() or "Custom"
        flag  = self.query_one("#i-flag",  Input).value.strip() or "🌍"
        if name and url:
            self.dismiss({"name": name, "url": url, "genre": genre,
                          "category": "Custom", "country": flag, "bitrate": "?"})


class HelpScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss_help"), Binding("question_mark", "dismiss_help")]
    CSS = """
    HelpScreen { align: center middle; }
    #hbox {
        width: 62; height: 38;
        border: double #58a6ff;
        background: #0d1117;
        padding: 1 2;
        overflow-y: auto;
    }
    """
    KEYS = [
        ("Playback",  [("Enter","Play selected"),("S","Stop"),("N","Next station"),("P","Previous station")]),
        ("Volume",    [("+ / =","Volume +5%"),("-","Volume -5%"),("0","Mute/Unmute"),("] / [","Fine +1/-1%")]),
        ("EQ",        [("E","Next EQ preset"),("Shift+E","Previous EQ preset")]),
        ("Favorites", [("F","Toggle favorite for selected")]),
        ("Recording", [("R","Start recording current stream"),("Shift+R","Stop recording")]),
        ("Search",    [("/","Focus search box"),("Escape","Clear search / close")]),
        ("Navigate",  [("↑ / ↓","Move list cursor"),("Tab","Switch category tab")]),
        ("App",       [("A","Add custom station"),("?","This help screen"),("Q","Quit")]),
    ]
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="hbox"):
            yield Label("[bold cyan]⌨  TERMINUS RADIO — KEYBOARD SHORTCUTS[/bold cyan]\n")
            for section, items in self.KEYS:
                yield Label(f"\n[bold yellow]── {section} ──[/bold yellow]")
                for k, d in items:
                    yield Label(f"  [bold white]{k:<18}[/bold white][dim]{d}[/dim]")
            yield Label("\n[dim]Recordings saved to: ~/.terminus_radio/recordings/[/dim]")
            yield Label("[dim]Press Escape or ? to close[/dim]")

    def action_dismiss_help(self) -> None:
        self.dismiss()

    def on_key(self, event) -> None:
        if event.key in ("escape", "question_mark"):
            self.dismiss()

# ══════════════════════════════════════════════════════════════════════════════
#  WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

class NowPlayingBar(Static):
    station  : reactive[str]  = reactive("No station selected")
    song     : reactive[str]  = reactive("—")
    status   : reactive[str]  = reactive("IDLE")
    volume   : reactive[int]  = reactive(70)
    elapsed  : reactive[int]  = reactive(0)
    viz      : reactive[int]  = reactive(0)
    bitrate  : reactive[str]  = reactive("—")
    eq_preset: reactive[str]  = reactive("Flat")
    recording: reactive[bool] = reactive(False)
    muted    : reactive[bool] = reactive(False)

    def render(self) -> str:
        playing = self.status == "PLAYING"
        s_col   = "green" if playing else ("yellow" if self.status == "CONNECTING" else "dim red")
        s_icon  = "▶" if playing else ("⟳" if self.status == "CONNECTING" else "■")
        m, s = divmod(self.elapsed, 60)
        h, m = divmod(m, 60)
        t = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        vfill   = self.volume // 10
        vbar    = "█" * vfill + "░" * (10 - vfill)
        vicon   = "🔇" if self.muted else ("🔊" if self.volume > 50 else "🔉")
        frame   = VIZ[self.viz % len(VIZ)] if playing else ("─" * 18)
        rec     = "  [bold red blink]⏺ REC[/bold red blink]" if self.recording else ""
        return (
            f"\n"
            f"  [{s_col}]{s_icon} {self.status}[/{s_col}]"
            f"  ⏱ {t}"
            f"  {vicon} {vbar} {self.volume}%"
            f"  [dim]BR:{self.bitrate}  EQ:{self.eq_preset}[/dim]"
            f"{rec}\n\n"
            f"  [bold cyan]📻 {self.station}[/bold cyan]\n\n"
            f"  [yellow]♪  {self.song}[/yellow]\n\n"
            f"  [dim cyan]{frame}[/dim cyan]\n"
        )


class StationRow(ListItem):
    def __init__(self, station: dict, fav: bool = False) -> None:
        super().__init__()
        self.station = station
        self._fav    = fav

    def compose(self) -> ComposeResult:
        s   = self.station
        star = " [yellow]★[/yellow]" if self._fav else "  "
        yield Label(
            f"{star} {s['country']}  [bold]{s['name']}[/bold]"
            f"  [dim]{s['genre']}  •  {s['bitrate']}[/dim]"
        )


class EQBar(Static):
    preset: reactive[str] = reactive("Flat")

    def render(self) -> str:
        parts = []
        for n in EQ_NAMES:
            if n == self.preset:
                parts.append(f"[bold white on #1f6feb] {n} [/bold white on #1f6feb]")
            else:
                parts.append(f"[dim] {n} [/dim]")
        return "  EQ ▸ " + "  ".join(parts)


class RecBar(Static):
    recording: reactive[bool] = reactive(False)
    filename : reactive[str]  = reactive("")
    elapsed  : reactive[int]  = reactive(0)

    def render(self) -> str:
        if not self.recording:
            return "  [dim]● Not recording  (R = start)[/dim]"
        m, s = divmod(self.elapsed, 60)
        return (
            f"  [bold red]⏺ RECORDING[/bold red]"
            f"  [dim]{self.filename}[/dim]"
            f"  [yellow]{m:02d}:{s:02d}[/yellow]"
            f"  [dim](Shift+R to stop)[/dim]"
        )

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

class TerminusRadio(App):
    CSS = """
    Screen { background: #0d1117; }

    NowPlayingBar {
        height: 10;
        border: round #30363d;
        background: #161b22;
        margin: 1 1 0 1;
        padding: 0 1;
        color: #c9d1d9;
    }

    #search-wrap {
        height: 3;
        margin: 0 1;
    }
    #search-wrap Input {
        background: #161b22;
        border: tall #30363d;
        color: #c9d1d9;
        height: 3;
    }
    #search-wrap Input:focus { border: tall #58a6ff; }

    TabbedContent { margin: 0 1; height: 1fr; }
    TabPane       { padding: 0;  height: 1fr; }

    ListView { background: #0d1117; height: 1fr; border: round #21262d; }
    ListItem { background: #0d1117; color: #8b949e; padding: 0 1; height: 2; }
    ListItem:hover       { background: #161b22; color: #c9d1d9; }
    ListItem.--highlight { background: #1a2332; color: #ffffff;  }
    ListItem.playing     { background: #0d2818; color: #3fb950;  }

    EQBar  { height: 1; background: #161b22; color: #8b949e; margin: 0 1; }
    RecBar { height: 1; background: #0d1117; color: #8b949e; margin: 0 1; }

    #status  { height: 1; background: #21262d; color: #58a6ff; padding: 0 2; }
    #hotkeys { height: 1; background: #161b22; color: #484f58; padding: 0 1; }

    AddStationScreen { align: center middle; }
    HelpScreen       { align: center middle; }
    Button           { background: #21262d; color: #c9d1d9; }
    Button.primary   { background: #1f6feb; color: #ffffff; }
    Button:hover     { background: #30363d; }
    """

    BINDINGS = [
        Binding("enter",   "play",        show=False),
        Binding("s",       "stop",        show=False),
        Binding("n",       "next_s",      show=False),
        Binding("p",       "prev_s",      show=False),
        Binding("plus,=",  "vol_up",      show=False),
        Binding("minus",   "vol_dn",      show=False),
        Binding("0",       "mute",        show=False),
        Binding("]",       "vol_fine_up", show=False),
        Binding("[",       "vol_fine_dn", show=False),
        Binding("e",       "eq_next",     show=False),
        Binding("E",       "eq_prev",     show=False),
        Binding("f",       "fav_toggle",  show=False),
        Binding("r",       "rec_start",   show=False),
        Binding("R",       "rec_stop",    show=False),
        Binding("/",       "search",      show=False),
        Binding("escape",  "clear",       show=False),
        Binding("up",      "cur_up",      show=False),
        Binding("down",    "cur_dn",      show=False),
        Binding("a",       "add",         show=False),
        Binding("question_mark", "help",  show=False),
        Binding("q",       "quit",        show=False),
    ]

    def __init__(self):
        super().__init__()
        self.player        = RadioPlayer()
        self.all_stations  = BUILTIN_STATIONS + load_json(CUSTOM_FILE, [])
        self.favorites     = load_json(FAV_FILE, [])
        self.playing_s     = None
        self.playing_idx   = -1
        self._elapsed      = 0
        self._pre_mute_vol = 70
        self._rec_proc     = None
        self._rec_elapsed  = 0
        self._cur_tab      = "All"
        self._query        = ""

        if MPV_AVAILABLE:
            self.player._on_song    = lambda v: self.call_from_thread(self._set_song, v)
            self.player._on_bitrate = lambda v: self.call_from_thread(self._set_bitrate, v)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield NowPlayingBar(id="npb")
        with Container(id="search-wrap"):
            yield Input(placeholder="  🔍  Search stations…", id="search-input")
        with TabbedContent(id="tabs"):
            for cat in CATEGORIES:
                with TabPane(cat, id=f"tab-{cat.lower().replace('-','_')}"):
                    yield ListView(id=f"lv-{cat.lower().replace('-','_')}")
        yield EQBar(id="eqbar")
        yield RecBar(id="recbar")
        yield Static("", id="status")
        yield Static(
            " [b]Enter[/b] Play  [b]S[/b] Stop  [b]N/P[/b] Next/Prev"
            "  [b]+/-[/b] Vol  [b]0[/b] Mute  [b]F[/b] Fav  [b]E[/b] EQ"
            "  [b]R[/b] Rec  [b]/[/b] Search  [b]A[/b] Add  [b]?[/b] Help  [b]Q[/b] Quit",
            id="hotkeys"
        )

    def on_mount(self) -> None:
        self._repopulate()
        self.set_interval(1.0,  self._tick_sec)
        self.set_interval(0.12, self._tick_viz)
        self._st("Ready  —  select a station and press Enter")

    # ── Station lists ─────────────────────────────────────────────────────────

    def _stations_for(self, cat: str) -> list[dict]:
        q = self._query.lower()
        if cat == "All":
            pool = self.all_stations
        elif cat == "Favorites":
            pool = [s for s in self.all_stations if s["name"] in self.favorites]
        elif cat == "Custom":
            pool = [s for s in self.all_stations if s.get("category") == "Custom"]
        else:
            pool = [s for s in self.all_stations if s.get("category") == cat]
        if q:
            pool = [s for s in pool if q in s["name"].lower() or q in s["genre"].lower()]
        return pool

    def _repopulate(self) -> None:
        for cat in CATEGORIES:
            lid = f"lv-{cat.lower().replace('-','_')}"
            try:
                lv = self.query_one(f"#{lid}", ListView)
            except NoMatches:
                continue
            lv.clear()
            for s in self._stations_for(cat):
                row = StationRow(s, s["name"] in self.favorites)
                if self.playing_s and s["name"] == self.playing_s["name"]:
                    row.add_class("playing")
                lv.append(row)

    def _active_list(self) -> list[dict]:
        return self._stations_for(self._cur_tab)

    def _cur_lv(self) -> Optional[ListView]:
        lid = f"lv-{self._cur_tab.lower().replace('-','_')}"
        try:
            return self.query_one(f"#{lid}", ListView)
        except NoMatches:
            return None

    # ── Playback ──────────────────────────────────────────────────────────────

    def _do_play(self, station: dict) -> None:
        npb = self.query_one("#npb", NowPlayingBar)
        self.player.stop()
        if not MPV_AVAILABLE:
            npb.station = station["name"]
            npb.song    = "⚠  python-mpv not installed"
            npb.status  = "ERROR"
            self._st("pip install python-mpv")
            return
        self.playing_s = station
        self._elapsed  = 0
        npb.elapsed    = 0
        npb.station    = station["name"]
        npb.song       = "Connecting…"
        npb.status     = "CONNECTING"
        npb.bitrate    = "—"
        self.player.play(station["url"])
        npb.status = "PLAYING"
        self.player.set_eq(self.player.eq_preset)
        self._st(f"▶  {station['name']}  —  {station['genre']}")
        self._repopulate()

    def action_play(self) -> None:
        lv = self._cur_lv()
        if lv is None or lv.index is None:
            return
        sl = self._active_list()
        if lv.index < len(sl):
            self.playing_idx = lv.index
            self._do_play(sl[lv.index])

    def action_stop(self) -> None:
        self.player.stop()
        npb = self.query_one("#npb", NowPlayingBar)
        npb.status  = "IDLE"
        npb.song    = "—"
        npb.bitrate = "—"
        self._elapsed  = 0
        npb.elapsed    = 0
        self._st("■  Stopped")
        self._repopulate()

    def action_next_s(self) -> None:
        sl = self._active_list()
        if not sl:
            return
        idx = (self.playing_idx + 1) % len(sl)
        self.playing_idx = idx
        self._do_play(sl[idx])
        lv = self._cur_lv()
        if lv:
            lv.index = idx

    def action_prev_s(self) -> None:
        sl = self._active_list()
        if not sl:
            return
        idx = (self.playing_idx - 1) % len(sl)
        self.playing_idx = idx
        self._do_play(sl[idx])
        lv = self._cur_lv()
        if lv:
            lv.index = idx

    # ── Volume ────────────────────────────────────────────────────────────────

    def _vol_sync(self) -> None:
        self.query_one("#npb", NowPlayingBar).volume = self.player.volume
        self._st(f"🔊 Volume: {self.player.volume}%")

    def action_vol_up(self):      self.player.vol_up(5); self._vol_sync()
    def action_vol_dn(self):      self.player.vol_dn(5); self._vol_sync()
    def action_vol_fine_up(self): self.player.vol_up(1); self._vol_sync()
    def action_vol_fine_dn(self): self.player.vol_dn(1); self._vol_sync()

    def action_mute(self) -> None:
        npb = self.query_one("#npb", NowPlayingBar)
        if npb.muted:
            self.player.set_volume(self._pre_mute_vol)
            npb.muted = False
        else:
            self._pre_mute_vol = self.player.volume
            self.player.set_volume(0)
            npb.muted = True
        npb.volume = self.player.volume
        self._st("🔇 Muted" if npb.muted else "🔊 Unmuted")

    # ── EQ ────────────────────────────────────────────────────────────────────

    def _eq_apply(self, name: str) -> None:
        self.player.set_eq(name)
        self.query_one("#npb",   NowPlayingBar).eq_preset = name
        self.query_one("#eqbar", EQBar).preset            = name
        self._st(f"EQ: {name}")

    def action_eq_next(self) -> None:
        i = (EQ_NAMES.index(self.player.eq_preset) + 1) % len(EQ_NAMES)
        self._eq_apply(EQ_NAMES[i])

    def action_eq_prev(self) -> None:
        i = (EQ_NAMES.index(self.player.eq_preset) - 1) % len(EQ_NAMES)
        self._eq_apply(EQ_NAMES[i])

    # ── Favorites ─────────────────────────────────────────────────────────────

    def action_fav_toggle(self) -> None:
        lv = self._cur_lv()
        if lv is None or lv.index is None:
            return
        sl = self._active_list()
        if lv.index >= len(sl):
            return
        name = sl[lv.index]["name"]
        if name in self.favorites:
            self.favorites.remove(name)
            self._st(f"☆  Removed from favorites: {name}")
        else:
            self.favorites.append(name)
            self._st(f"★  Added to favorites: {name}")
        save_json(FAV_FILE, self.favorites)
        self._repopulate()

    # ── Recording ─────────────────────────────────────────────────────────────

    def action_rec_start(self) -> None:
        rb = self.query_one("#recbar", RecBar)
        if rb.recording:
            self._st("Already recording — Shift+R to stop")
            return
        if not self.playing_s:
            self._st("⚠  No station playing")
            return
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe  = re.sub(r"[^\w\-]", "_", self.playing_s["name"])
        fname = f"{safe}_{ts}.mp3"
        fpath = str(REC_DIR / fname)
        proc  = self.player.record(self.playing_s["url"], fpath)
        if proc is None:
            self._st("⚠  ffmpeg not found — pkg install ffmpeg")
            return
        self._rec_proc = proc
        self._rec_elapsed = 0
        rb.recording = True
        rb.filename  = fname
        rb.elapsed   = 0
        self.query_one("#npb", NowPlayingBar).recording = True
        self._st(f"⏺  Recording → {fpath}")

    def action_rec_stop(self) -> None:
        rb = self.query_one("#recbar", RecBar)
        if not rb.recording:
            return
        if self._rec_proc:
            self._rec_proc.terminate()
            self._rec_proc = None
        rb.recording = False
        self.query_one("#npb", NowPlayingBar).recording = False
        self._st(f"⏹  Recording saved → {REC_DIR}")

    # ── Search ────────────────────────────────────────────────────────────────

    def action_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_clear(self) -> None:
        inp = self.query_one("#search-input", Input)
        if inp.value:
            inp.value = ""
            self._query = ""
            self._repopulate()

    @on(Input.Changed, "#search-input")
    def _on_search(self, event: Input.Changed) -> None:
        self._query = event.value.strip()
        self._repopulate()

    # ── Navigation ────────────────────────────────────────────────────────────

    def action_cur_up(self) -> None:
        lv = self._cur_lv()
        if lv:
            lv.action_cursor_up()

    def action_cur_dn(self) -> None:
        lv = self._cur_lv()
        if lv:
            lv.action_cursor_down()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        raw = str(event.tab.id).replace("tab-", "").replace("_", "-")
        for cat in CATEGORIES:
            if cat.lower() == raw:
                self._cur_tab = cat
                break

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, StationRow):
            sl = self._active_list()
            for i, s in enumerate(sl):
                if s["name"] == event.item.station["name"]:
                    self.playing_idx = i
                    break
            self._do_play(event.item.station)

    # ── Add station ───────────────────────────────────────────────────────────

    def action_add(self) -> None:
        def _cb(result):
            if result:
                self.all_stations.append(result)
                customs = [s for s in self.all_stations if s.get("category") == "Custom"]
                save_json(CUSTOM_FILE, customs)
                self._repopulate()
                self._st(f"✓  Added: {result['name']}")
        self.push_screen(AddStationScreen(), _cb)

    # ── Help ──────────────────────────────────────────────────────────────────

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    # ── Quit ─────────────────────────────────────────────────────────────────

    def action_quit(self) -> None:
        if self._rec_proc:
            self._rec_proc.terminate()
        self.player.quit()
        self.exit()

    # ── Timers ────────────────────────────────────────────────────────────────

    def _tick_sec(self) -> None:
        npb = self.query_one("#npb", NowPlayingBar)
        if npb.status == "PLAYING":
            self._elapsed += 1
            npb.elapsed   = self._elapsed
        rb = self.query_one("#recbar", RecBar)
        if rb.recording and self._rec_proc:
            if self._rec_proc.poll() is not None:
                self.action_rec_stop()
            else:
                self._rec_elapsed += 1
                rb.elapsed = self._rec_elapsed

    def _tick_viz(self) -> None:
        npb = self.query_one("#npb", NowPlayingBar)
        if npb.status == "PLAYING":
            npb.viz = (npb.viz + 1) % len(VIZ)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _set_song(self, v: str) -> None:
        self.query_one("#npb", NowPlayingBar).song = v

    def _set_bitrate(self, v: str) -> None:
        self.query_one("#npb", NowPlayingBar).bitrate = v

    def _st(self, msg: str) -> None:
        try:
            self.query_one("#status", Static).update(msg)
        except NoMatches:
            pass

# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not MPV_AVAILABLE:
        print("\n⚠  python-mpv not found — audio won't work.")
        print("   pkg install mpv && pip install python-mpv\n")
    TerminusRadio().run()

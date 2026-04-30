#!/usr/bin/env -S uv run python
"""
╔══════════════════════════════════════╗
║       TERMINUS RADIO  📻             ║
║   A full-featured TUI radio player   ║
╚══════════════════════════════════════╝

Dependencies:
    pip install textual python-mpv

On Termux:
    pkg install mpv
    pip install textual python-mpv
"""

from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Static, ListView, ListItem, Label, ProgressBar
)
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.binding import Binding
from textual import work
from textual.worker import Worker, WorkerState
from textual.color import Color

import asyncio
import time
import threading
from datetime import datetime

# ── Try importing python-mpv ──────────────────────────────────────────────────
try:
    import mpv
    MPV_AVAILABLE = True
except ImportError:
    MPV_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
#  STATION DATABASE
# ══════════════════════════════════════════════════════════════════════════════

STATIONS = [
    {
        "name": "Clye Education",
        "genre": "Education",
        "url": "https://eu8.fastcast4u.com/proxy/clyedupq?mp=%2F1?aw_0_req_lsid=2c0fae177108c9a42a7cf24878625444",
        "country": "🌍",
        "bitrate": "128k",
    },
    {
        "name": "BBC World Service",
        "genre": "News / Talk",
        "url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service",
        "country": "🇬🇧",
        "bitrate": "128k",
    },
    {
        "name": "Radio Paradise (Main)",
        "genre": "Eclectic / Rock",
        "url": "https://stream.radioparadise.com/aac-128",
        "country": "🇺🇸",
        "bitrate": "128k",
    },
    {
        "name": "SomaFM — Groove Salad",
        "genre": "Ambient / Electronica",
        "url": "https://ice6.somafm.com/groovesalad-128-mp3",
        "country": "🇺🇸",
        "bitrate": "128k",
    },
    {
        "name": "SomaFM — Drone Zone",
        "genre": "Ambient / Space",
        "url": "https://ice6.somafm.com/dronezone-128-mp3",
        "country": "🇺🇸",
        "bitrate": "128k",
    },
    {
        "name": "KEXP 90.3 FM",
        "genre": "Indie / Alternative",
        "url": "https://live-aacplus-64.kexp.org/kexp64.aac",
        "country": "🇺🇸",
        "bitrate": "64k",
    },
    {
        "name": "Chillhop Radio",
        "genre": "Lo-Fi / Hip-Hop",
        "url": "https://stream.chillhop.com/hls/chillhop.m3u8",
        "country": "🌍",
        "bitrate": "128k",
    },
    {
        "name": "Radio Swiss Jazz",
        "genre": "Jazz",
        "url": "http://stream.srg-ssr.ch/m/rsj/mp3_128",
        "country": "🇨🇭",
        "bitrate": "128k",
    },
    {
        "name": "Radio Swiss Classic",
        "genre": "Classical",
        "url": "http://stream.srg-ssr.ch/m/rsc_de/mp3_128",
        "country": "🇨🇭",
        "bitrate": "128k",
    },
    {
        "name": "NTS Radio 1",
        "genre": "Experimental / Mixed",
        "url": "https://stream-relay-geo.ntslive.net/stream",
        "country": "🇬🇧",
        "bitrate": "128k",
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#  MPV PLAYER WRAPPER
# ══════════════════════════════════════════════════════════════════════════════

class RadioPlayer:
    """Thin wrapper around python-mpv for radio stream playback."""

    def __init__(self):
        self.player = None
        self.is_playing = False
        self.volume = 70
        self._current_url = None
        self._metadata_callback = None

        if MPV_AVAILABLE:
            self.player = mpv.MPV(
                ytdl=False,
                input_default_bindings=False,
                input_vo_keyboard=False,
                video=False,                  # audio-only
                terminal=False,
                really_quiet=True,
            )
            self.player.volume = self.volume

            @self.player.property_observer("media-title")
            def on_title(name, value):
                if self._metadata_callback and value:
                    self._metadata_callback(value)

    def play(self, url: str):
        if not self.player:
            return
        self._current_url = url
        self.player.play(url)
        self.player.volume = self.volume
        self.is_playing = True

    def stop(self):
        if not self.player:
            return
        self.player.stop()
        self.is_playing = False

    def set_volume(self, vol: int):
        self.volume = max(0, min(100, vol))
        if self.player:
            self.player.volume = self.volume

    def volume_up(self, step=5):
        self.set_volume(self.volume + step)

    def volume_down(self, step=5):
        self.set_volume(self.volume - step)

    def set_metadata_callback(self, cb):
        self._metadata_callback = cb

    def quit(self):
        if self.player:
            try:
                self.player.stop()
                self.player.terminate()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
#  TEXTUAL WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

RADIO_ART = """
 ╔═══════════════════════════╗
 ║  ◉ TERMINUS RADIO  📻    ║
 ╚═══════════════════════════╝"""

WAVE_FRAMES = [
    "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁",
    "▂▃▄▅▆▇█▇▆▅▄▃▂▁▂",
    "▃▄▅▆▇█▇▆▅▄▃▂▁▂▃",
    "▄▅▆▇█▇▆▅▄▃▂▁▂▃▄",
    "▅▆▇█▇▆▅▄▃▂▁▂▃▄▅",
    "▆▇█▇▆▅▄▃▂▁▂▃▄▅▆",
    "▇█▇▆▅▄▃▂▁▂▃▄▅▆▇",
    "█▇▆▅▄▃▂▁▂▃▄▅▆▇█",
]


class NowPlayingPanel(Static):
    """Top panel — station name, metadata, waveform animation."""

    station_name: reactive[str] = reactive("No station selected")
    song_title: reactive[str] = reactive("—")
    status: reactive[str] = reactive("STOPPED")
    wave_frame: reactive[int] = reactive(0)
    volume: reactive[int] = reactive(70)
    elapsed: reactive[int] = reactive(0)

    def render(self) -> str:
        status_icon = "▶" if self.status == "PLAYING" else "■"
        status_color = "green" if self.status == "PLAYING" else "red"

        wave = WAVE_FRAMES[self.wave_frame % len(WAVE_FRAMES)] if self.status == "PLAYING" else "─────────────────"

        mins, secs = divmod(self.elapsed, 60)
        hrs, mins = divmod(mins, 60)
        time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}" if hrs else f"{mins:02d}:{secs:02d}"

        vol_bar = "█" * (self.volume // 10) + "░" * (10 - self.volume // 10)

        return (
            f"\n"
            f"  [{status_color}]{status_icon} {self.status}[/{status_color}]"
            f"  ⏱ {time_str}"
            f"  🔊 {vol_bar} {self.volume}%\n\n"
            f"  [bold cyan]📻 {self.station_name}[/bold cyan]\n\n"
            f"  [yellow]♪  {self.song_title}[/yellow]\n\n"
            f"  [dim]{wave}[/dim]\n"
        )


class StationItem(ListItem):
    """A single station row in the list."""

    def __init__(self, station: dict, index: int) -> None:
        super().__init__()
        self.station = station
        self.index = index

    def compose(self) -> ComposeResult:
        s = self.station
        yield Label(
            f" {s['country']}  [bold]{s['name']}[/bold]"
            f"  [dim]{s['genre']}  •  {s['bitrate']}[/dim]"
        )


class HelpPanel(Static):
    """Keyboard shortcuts help bar."""

    def render(self) -> str:
        return (
            " [bold]ENTER[/bold] Play  "
            " [bold]S[/bold] Stop  "
            " [bold]+[/bold]/[bold]-[/bold] Volume  "
            " [bold]A[/bold] Add station  "
            " [bold]R[/bold] Refresh  "
            " [bold]Q[/bold] Quit"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

class TerminusRadio(App):
    """Full-featured TUI radio player."""

    CSS = """
    Screen {
        background: #0d1117;
    }

    NowPlayingPanel {
        height: 10;
        border: round #30363d;
        background: #161b22;
        margin: 1 1 0 1;
        padding: 0 1;
        color: #c9d1d9;
    }

    #station-list-container {
        border: round #30363d;
        background: #0d1117;
        margin: 1 1 0 1;
        height: 1fr;
    }

    #station-title {
        background: #21262d;
        color: #58a6ff;
        padding: 0 2;
        height: 1;
        text-style: bold;
    }

    ListView {
        background: #0d1117;
        height: 1fr;
    }

    ListItem {
        background: #0d1117;
        color: #8b949e;
        padding: 0 1;
        height: 1;
    }

    ListItem:hover {
        background: #161b22;
        color: #c9d1d9;
    }

    ListItem.--highlight {
        background: #1f6feb;
        color: #ffffff;
    }

    ListItem.playing {
        background: #0d2d0d;
        color: #3fb950;
    }

    HelpPanel {
        height: 1;
        background: #21262d;
        color: #8b949e;
        padding: 0 1;
        margin: 0;
    }

    #status-bar {
        height: 1;
        background: #161b22;
        color: #58a6ff;
        padding: 0 2;
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "stop", "Stop"),
        Binding("plus,=", "volume_up", "Vol+"),
        Binding("minus", "volume_down", "Vol-"),
        Binding("r", "refresh_stations", "Refresh"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "play_selected", "Play"),
    ]

    def __init__(self):
        super().__init__()
        self.player = RadioPlayer()
        self.stations = list(STATIONS)
        self.current_station_index = -1
        self.playing_index = -1
        self._elapsed_task = None
        self._wave_task = None
        self._elapsed_seconds = 0

        # wire metadata callback
        if MPV_AVAILABLE:
            self.player.set_metadata_callback(self._on_metadata)

    # ── Compose UI ────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield NowPlayingPanel(id="now-playing")
        with Vertical(id="station-list-container"):
            yield Label(" 📡  STATIONS", id="station-title")
            lv = ListView(id="station-list")
            yield lv
        yield Static("", id="status-bar")
        yield HelpPanel()

    def on_mount(self) -> None:
        lv = self.query_one("#station-list", ListView)
        for i, station in enumerate(self.stations):
            lv.append(StationItem(station, i))
        self._set_status("Ready — select a station and press ENTER to play")
        self._start_clock()

    # ── Playback ──────────────────────────────────────────────────────────────

    def action_play_selected(self) -> None:
        lv = self.query_one("#station-list", ListView)
        if lv.index is None:
            return
        idx = lv.index
        self._play_station(idx)

    def _play_station(self, idx: int) -> None:
        station = self.stations[idx]
        panel = self.query_one("#now-playing", NowPlayingPanel)

        # stop previous
        self.player.stop()
        self._reset_playing_highlight()

        if not MPV_AVAILABLE:
            panel.station_name = station["name"]
            panel.song_title = "python-mpv not installed"
            panel.status = "ERROR"
            self._set_status("⚠  Install python-mpv:  pip install python-mpv")
            return

        self.playing_index = idx
        self._elapsed_seconds = 0
        panel.elapsed = 0
        panel.station_name = station["name"]
        panel.song_title = "Connecting…"
        panel.status = "PLAYING"
        panel.volume = self.player.volume

        self.player.play(station["url"])
        self._set_status(f"▶  Now playing: {station['name']}")

        # highlight playing row
        lv = self.query_one("#station-list", ListView)
        items = list(lv.query(StationItem))
        if idx < len(items):
            items[idx].add_class("playing")

    def action_stop(self) -> None:
        self.player.stop()
        panel = self.query_one("#now-playing", NowPlayingPanel)
        panel.status = "STOPPED"
        panel.song_title = "—"
        self._elapsed_seconds = 0
        panel.elapsed = 0
        self._reset_playing_highlight()
        self._set_status("■  Stopped")

    def _reset_playing_highlight(self) -> None:
        for item in self.query(StationItem):
            item.remove_class("playing")

    # ── Volume ────────────────────────────────────────────────────────────────

    def action_volume_up(self) -> None:
        self.player.volume_up()
        self.query_one("#now-playing", NowPlayingPanel).volume = self.player.volume
        self._set_status(f"🔊 Volume: {self.player.volume}%")

    def action_volume_down(self) -> None:
        self.player.volume_down()
        self.query_one("#now-playing", NowPlayingPanel).volume = self.player.volume
        self._set_status(f"🔉 Volume: {self.player.volume}%")

    # ── Misc ──────────────────────────────────────────────────────────────────

    def action_refresh_stations(self) -> None:
        self._set_status("✓  Station list refreshed")

    def action_quit(self) -> None:
        self.player.quit()
        self.exit()

    def action_move_up(self) -> None:
        lv = self.query_one("#station-list", ListView)
        lv.action_cursor_up()

    def action_move_down(self) -> None:
        lv = self.query_one("#station-list", ListView)
        lv.action_cursor_down()

    # ── Clock & animation ─────────────────────────────────────────────────────

    def _start_clock(self) -> None:
        self.set_interval(1.0, self._tick_clock)
        self.set_interval(0.15, self._tick_wave)

    def _tick_clock(self) -> None:
        panel = self.query_one("#now-playing", NowPlayingPanel)
        if panel.status == "PLAYING":
            self._elapsed_seconds += 1
            panel.elapsed = self._elapsed_seconds

    def _tick_wave(self) -> None:
        panel = self.query_one("#now-playing", NowPlayingPanel)
        if panel.status == "PLAYING":
            panel.wave_frame = (panel.wave_frame + 1) % len(WAVE_FRAMES)

    # ── Metadata callback (from mpv thread) ───────────────────────────────────

    def _on_metadata(self, title: str) -> None:
        """Called from mpv's observer thread — schedule UI update safely."""
        self.call_from_thread(self._update_song_title, title)

    def _update_song_title(self, title: str) -> None:
        panel = self.query_one("#now-playing", NowPlayingPanel)
        panel.song_title = title

    # ── Status bar ────────────────────────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        self.query_one("#status-bar", Static).update(msg)

    # ── Click to select ───────────────────────────────────────────────────────

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, StationItem):
            self._play_station(event.item.index)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not MPV_AVAILABLE:
        print("\n⚠  python-mpv is not installed.")
        print("   Install it with:  pip install python-mpv")
        print("   Also ensure mpv is installed:  pkg install mpv  (Termux)")
        print("\n   The app will launch but playback will not work.\n")

    app = TerminusRadio()
    app.run()

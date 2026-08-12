# 🎵 TermTune (termmusic)

> A fast, keyboard-driven, high-contrast terminal music player powered by Python, Textual, `yt-dlp`, and `mpv`.

![TermTune Banner](https://img.shields.io/badge/TermTune-Terminal_Music_Player-000000?style=for-the-badge&logo=python&logoColor=white)
![Python Version](https://img.shields.io/badge/Python-3.12%2B-black?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-white?style=for-the-badge)

---

## ✨ Features

- ⚡ **CLI Command Pipeline**: Control playback directly from any terminal prompt (`termtune play "song"`, `termtune next`, `termtune pause`, `termtune status`).
- 🎮 **"Zen Mode" Screensaver (`Shift+Z`)**: Full-screen minimal animated ASCII spinning vinyl record with floating track metadata.
- ⚡ **Zero-Latency Playback**: Direct stream extraction via `yt-dlp` with automatic background pre-fetching for instant track transitions.
- 📁 **Playlist Manager**: Create, load, edit, and delete saved playlists stored under `~/.termtune/playlists/`. Loading a playlist starts playback immediately.
- 🛡️ **Strict Duplicate Prevention**: Blocks duplicate tracks from polluting your queue with real-time warning notifications.
- ⌨️ **Keyboard-Centric UI**: Complete TUI navigation built using Textual. No mouse selection required.
- 💾 **Queue Persistence**: Saves your active queue state to `~/.termtune/queue_state.json` on exit and restores it on launch.
- ⏱️ **Queue Duration Header**: Real-time calculated queue statistics displaying total tracks and combined playback duration.
- 🔀 **Smart Queue Engine**: Instant track removal (`d`/`Delete`), live reordering (`Alt+Up`/`Alt+Down`), Play Next insertion (`Shift+A`), and inline queue filtering (`/`).
- ⚪ **Monochrome High-Contrast Theme**: Pure dark aesthetic with clean white scrollbars and dynamic micro-animations.

---

## 💻 CLI Command Pipeline

Control music from any shell tab or script without opening the full TUI:

```bash
# Search and play a track directly from bash
termtune play "lo-fi hip hop chill beats"

# Skip to next or previous track
termtune next
termtune prev

# Toggle pause / resume
termtune pause
termtune resume

# Print current track status and progress
termtune status
```

---

## 🚀 Quick Start

### 1. Prerequisites

TermTune requires **`mpv`** installed on your system for audio playback:

#### Linux (Ubuntu/Debian)
```bash
sudo apt update && sudo apt install -y mpv
```

#### macOS
```bash
brew install mpv
```

---

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Vibin-007/termmusic.git
cd termmusic

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package in editable mode
pip install -e .
```

---

### 3. Launching TermTune

```bash
termtune
```

---

## ⌨️ Keybindings

| Key | Action |
| :--- | :--- |
| <kbd>Shift</kbd> + <kbd>Z</kbd> | Toggle **"Zen Mode" Animated ASCII Screensaver** |
| <kbd>S</kbd> | Focus Search Input |
| <kbd>Space</kbd> | Toggle Play / Pause |
| <kbd>N</kbd> | Next Track in Queue |
| <kbd>B</kbd> | Previous Track in History |
| <kbd>A</kbd> | Add Selected Track to Queue |
| <kbd>Shift</kbd> + <kbd>A</kbd> | Insert Track as **Play Next** |
| <kbd>L</kbd> | Save Selected Track to **Playlist** |
| <kbd>P</kbd> | Open **Playlist Manager** (Load / Create / Delete) |
| <kbd>d</kbd> / <kbd>Delete</kbd> | Remove Highlighted Track from Queue |
| <kbd>Alt</kbd> + <kbd>↑</kbd> / <kbd>↓</kbd> | Move Track Up / Down in Queue |
| <kbd>/</kbd> | Toggle Inline Queue Filter |
| <kbd>C</kbd> | Clear Entire Queue |
| <kbd>+</kbd> / <kbd>-</kbd> | Volume Up / Down |
| <kbd>M</kbd> | Toggle Audio Mute |
| <kbd>Z</kbd> | Toggle Shuffle Mode |
| <kbd>R</kbd> | Cycle Repeat Mode (`OFF` -> `ALL` -> `TRACK`) |
| <kbd>←</kbd> / <kbd>→</kbd> | Seek 10s Backward / Forward |
| <kbd>Esc</kbd> | Unfocus Search Input / Close Modal / Exit Zen |
| <kbd>Q</kbd> | Quit TermTune |

---

## 🛠️ Architecture Overview

```
src/termtune/
├── app.py                # Main Textual App entry point
├── config/               # Settings & persistent TOML configuration
├── ipc.py                # Inter-Process Communication UNIX socket server/client
├── models/               # Data models (Track, StreamInfo)
├── player/               # MPV adapter & PlayerController engine
├── playlist/             # PlaylistManager handling disk JSON playlists
├── providers/            # Music providers (yt-dlp YouTube search & resolution)
├── queue/                # QueueManager with deduplication, persistence & shuffle history
├── ui/                   # Textual screens, action modals, widgets, and Zen Mode screensaver
└── utils/                # Formatting helpers and custom exception types
```

---

## 🧪 Running Tests

Run the full unit test suite with `pytest`:

```bash
pytest -v
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
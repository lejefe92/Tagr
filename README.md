# Tagr

**Tagr** is a clean, fast audio tag editor for macOS — built for people who care about their music library.

Edit metadata, find cover art, and download audio from the web, all in one place.

![macOS](https://img.shields.io/badge/macOS-12%2B-black) ![Python](https://img.shields.io/badge/Python-3.12-blue) ![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Edit tags** — title, artist, album for MP3, FLAC, M4A, AAC, OGG
- **Cover art** — search, crop to square, export
- **Download** — paste a YouTube, SoundCloud or Bandcamp URL and get the audio file directly in Tagr
- **Audio tools** — trim, normalize to -14 LUFS, convert format
- **Multiple selection** — select and manage several files at once
- **Bilingual UI** — switch between French and English on the fly

---

## Installation

### Option A — Homebrew (recommended)

```bash
brew tap lejefe92/tagr
brew install --cask tagr
```

### Option B — Manual download

1. Download `Tagr-v1.3.2.zip` from the [latest release](https://github.com/lejefe92/Tagr/releases/latest)
2. Unzip and drag `Tagr.app` to your Applications folder
3. First launch: **right-click → Open** (required to bypass macOS Gatekeeper on unsigned apps)

### Requirements

- macOS 12 or later

> `ffmpeg` and `yt-dlp` are bundled inside the app — nothing to install.

---

## Usage

**Adding files** — drag and drop audio files or folders, or click `+`

**Downloading from URL** — click the `↓` button in the top left, paste a link and hit Enter

**Saving** — click Save to overwrite the existing file or create a new one named `Artist - Title`

---

## Feedback & Issues

Found a bug or have a suggestion? Open an [issue](https://github.com/lejefe92/Tagr/issues) on GitHub.

---

## License

MIT © lejefe92

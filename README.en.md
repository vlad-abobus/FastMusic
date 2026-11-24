# FastMusic — music player

[Русский](README.md) | **English**

A VK Music clone: search tracks via Deezer, download them, keep a local library, browse charts and listen to internet radio.
Two versions ship side by side — a Python desktop app (CustomTkinter) and a React + Express web app.

## Features

- Search tracks, albums and artists (Deezer)
- Deezer charts, artist top tracks, related artists
- Download tracks into the local library
- Playback: play / pause, seek, volume, keyboard shortcuts
- Internet radio (Radio Browser): popular stations, search by name, tag, country
- Album artwork and download queue

## Desktop app (Python)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py                # or: .\run-dev.ps1
```

The library is stored in the `music_library.db` SQLite file, logs go to `logs/`.

### Building the .exe

```powershell
.\build-exe.ps1              # with console
.\build-exe.ps1 -Windowed    # without console
```

Output: `dist/FastMusic.exe`. The script downloads `ffmpeg.exe` automatically if it is missing.

## Web app (React + Express)

```bash
npm install
npm run dev                  # http://localhost:3000
```

- `npm run build` — build frontend and server into `dist/`
- `npm run lint` — type check with `tsc --noEmit`

The server (`server.ts`) proxies Deezer and Radio Browser; the local library lives in
`data/library.json` and audio files in `downloads/`.

## Layout

```
main.py, logic.py, radio_client.py, radio_player.py   desktop app
src/, index.html, server.ts                           web app
andrKIVY/                                             mobile version (Kivy)
build-exe.ps1, FastMusic.spec                         .exe build
```

## Dependencies

- Python: see `requirements.txt`
- Node: see `package.json`
- Optional: Deezer token in `.env` (copy `.env.example`)

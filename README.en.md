<p align="center">
  <sub>Language / Язык</sub><br>
  <a href="README.md">🇷🇺 Русский</a> · <b>🇬🇧 English</b>
</p>

# FastMusic

FastMusic is a music player that searches tracks through Deezer, downloads them into
a local library, and supports charts and internet radio.

The repository contains two independent applications:

- **`desktop/`** — a Python desktop player (CustomTkinter, Windows);
- **`android/`** — a mobile player built with Kivy / KivyMD.

The web version is no longer part of the repository: the project is maintained as a
desktop and Android application only.

## Features

- Search tracks, albums, and artists via Deezer
- Deezer charts, artist top tracks, and related artists
- Download tracks into the local library
- Playback: play / pause, seek, volume, keyboard shortcuts
- Internet radio (Radio Browser): popular stations, search by name, tag, and country
- Album artwork, download queue, and a local SQLite library
- Dark theme

## Repository layout

```text
.
├── desktop/                     # Desktop app (Python + CustomTkinter)
│   ├── main.py                  # Entry point and UI
│   ├── logic.py                 # Library, downloads, Deezer
│   ├── deezer_client.py         # Deezer API client
│   ├── radio_client.py          # Radio Browser client
│   ├── radio_player.py          # Radio playback via ffplay
│   ├── logger.py                # Logging
│   ├── FastMusic.spec           # PyInstaller configuration
│   ├── favicon.ico              # App icon
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Environment variables example
│
├── android/                     # Android app (Kivy + KivyMD)
│   ├── main.py                  # Entry point and UI
│   ├── logic.py                 # Library, downloads, Deezer
│   ├── audio.py                 # Audio backends (ffpyplayer / pygame / Kivy)
│   ├── deezer_client.py         # Deezer API client
│   ├── logger.py                # Logging
│   ├── fastmusic.kv             # Kivy UI markup
│   ├── buildozer.spec           # APK build configuration
│   ├── requirements.txt         # Dependencies for local runs
│   ├── icon.png                 # App icon
│   ├── presplash.png            # Launch splash screen
│   └── recipes/                 # Local python-for-android recipes
│
├── README.md                    # Russian README
└── README.en.md                 # This file (English)
```

`desktop/` and `android/` are self-contained applications. Modules that serve the same
purpose (`logic.py`, `deezer_client.py`, `logger.py`) are intentionally duplicated so
each platform can be built and packaged independently without a shared package.

## Desktop app

### Requirements

- Python 3.10+
- Windows 10/11
- **ffmpeg** — required for MP3 downloads and radio playback

Install ffmpeg with Winget:

```powershell
winget install Gyan.FFmpeg
```

Alternatively, place `ffmpeg.exe` in the `desktop/` folder — the app will find it
automatically.

### Run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r desktop\requirements.txt
python desktop\main.py
```

You can also run it from the app folder:

```powershell
cd desktop
python main.py
```

### Application data

On startup, the app creates the following next to itself:

- `desktop/downloads/` — downloaded tracks;
- `desktop/music_library.db` — local SQLite library;
- `desktop/logs/` — logs.

These paths are ignored by Git. For a built `.exe`, the data is stored next to the
executable.

### Deezer configuration

A token is optional, but it raises Deezer API rate limits:

```powershell
copy desktop\.env.example desktop\.env
```

Then set `DEEZER_TOKEN` in `desktop/.env`. You can get a token at
[developers.deezer.com](https://developers.deezer.com/myapps).

### Build the `.exe`

```powershell
pip install pyinstaller
cd desktop
pyinstaller FastMusic.spec
```

The executable is written to `desktop/dist/FastMusic.exe`. If `ffmpeg.exe` is placed
next to `FastMusic.spec`, it is bundled into the build. To hide the console window,
change `console=True` to `console=False` in `FastMusic.spec`.

## Android app

The app is built with Kivy / KivyMD. The mobile UI is currently in Ukrainian. The audio
backend is selected automatically: `ffpyplayer` → `pygame` → `Kivy SoundLoader`; on
Android the built-in Kivy backend is used.

### Run locally

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r android\requirements.txt
python android\main.py
```

On Windows, local runs may require ffpyplayer and additional system libraries. This is
not required to preview the UI — the app starts without audio as well.

### Build the APK

Buildozer runs on Linux. On Windows, use WSL2 with Ubuntu:

```powershell
wsl --install -d Ubuntu
```

Inside Ubuntu:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
    autoconf automake libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo6 cmake libffi-dev libssl-dev
pip3 install --user buildozer cython
```

Then:

```bash
cd /path/to/FastMusic/android
buildozer -v android debug
```

The APK is written to `android/bin/`. Buildozer downloads the Android SDK, NDK, and the
remaining dependencies automatically. The local `materialyoucolor` recipe is wired in
through `p4a.local_recipes` in `buildozer.spec`.

### Android data

On a device, the library, logs, and downloaded tracks are stored in the app's internal
storage (`app_storage_path()`), not in the project folder.

## Development

- Check the Python code without running the apps:

  ```bash
  python -m compileall desktop android
  ```

- App logs are written to `logs/fastmusic.log` next to the app.
- Downloaded tracks and the database are not committed — they are listed in `.gitignore`.
- For the desktop app, the Deezer token lives only in `desktop/.env` (ignored by Git).

## License

No license is specified in this repository. If you plan to distribute the project
publicly, add a `LICENSE` file with a suitable license.

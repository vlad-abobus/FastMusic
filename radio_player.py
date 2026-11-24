from __future__ import annotations

import subprocess
import os
import sys
import shutil
from logger import get_logger

log = get_logger(__name__)

FFPLAY_CANDIDATES = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""),
                 r"ffmpegio\ffmpeg-downloader\ffmpeg\bin\ffplay.exe"),
    # WinGet (Gyan) install location
    os.path.join(os.environ.get("LOCALAPPDATA", ""),
                 r"Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-*-full_build\bin\ffplay.exe"),
]


def _find_ffplay():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        FFPLAY_CANDIDATES.insert(0, os.path.join(base, "ffplay.exe"))
    for fp in FFPLAY_CANDIDATES:
        # allow wildcard-ish paths from WinGet candidate
        if "*" in fp:
            try:
                import glob
                matches = glob.glob(fp)
                if matches:
                    return matches[0]
            except Exception:
                pass
        else:
            if os.path.isfile(fp):
                return fp
    # Try shutil.which which checks PATH
    try:
        w = shutil.which("ffplay")
        if w:
            return w
    except Exception:
        pass
    for dir_ in os.environ.get("PATH", "").split(os.pathsep):
        fp = os.path.join(dir_, "ffplay.exe")
        if os.path.isfile(fp):
            return fp
    return None


class RadioPlayer:
    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._url: str | None = None
        self._explicit_paused = False
        self._ffplay = _find_ffplay()
        if self._ffplay:
            log.info("Радио: ffplay найден: %s", self._ffplay)
        else:
            log.warning("Радио: ffplay не найден")

    def is_available(self) -> bool:
        return self._ffplay is not None

    @property
    def is_playing(self) -> bool:
        if self._process is None:
            return False
        ret = self._process.poll()
        return ret is None

    def play(self, url: str, volume: int = 50) -> bool:
        self.stop()
        if not self._ffplay:
            return False
        self._url = url
        try:
            self._process = subprocess.Popen(
                [self._ffplay, "-nodisp", "-loglevel", "quiet",
                 "-volume", str(volume), url],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000,
            )
            log.info("Радио: ffplay запущен PID=%d", self._process.pid)
            self._explicit_paused = False
            return True
        except Exception as e:
            log.error("Радио: ошибка запуска ffplay: %s", e)
            return False

    def stop(self):
        if self._process:
            try:
                self._process.kill()
                self._process.wait(timeout=3)
            except Exception as e:
                log.warning("Радио: ошибка остановки ffplay: %s", e)
            self._process = None
        self._url = None
        self._explicit_paused = False

    def toggle_pause(self):
        if self._explicit_paused:
            self._resume()
        elif self._process is not None:
            self._pause()

    def _pause(self):
        if self._process is None:
            return
        try:
            self._process.kill()
            self._process.wait(timeout=2)
        except Exception as e:
            log.warning("Радио: ошибка при паузе ffplay: %s", e)
        self._process = None
        self._explicit_paused = True

    def _resume(self):
        if self._url:
            self.play(self._url)

    @property
    def is_paused(self) -> bool:
        return self._explicit_paused

    @property
    def url(self) -> str | None:
        return self._url

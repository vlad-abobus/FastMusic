"""Аудио-бэкенд FastMusic Kivy.

Приоритет: ffpyplayer (любит все форматы: mp3/m4a/webm/opus),
затем pygame.mixer, затем Kivy SoundLoader (SDL2).
Интерфейс у всех бэкендов одинаковый.
"""

from logger import get_logger

log = get_logger(__name__)

FFPY_OK = False
try:
    from ffpyplayer.player import MediaPlayer

    FFPY_OK = True
except Exception as _e:
    MediaPlayer = None
    log.info("ffpyplayer недоступен (%s)", _e)

try:
    from pygame import mixer as _mixer

    PYGAME_OK = True
except Exception as _e:
    _mixer = None
    PYGAME_OK = False
    log.info("pygame недоступен (%s)", _e)


class FFPyBackend:
    name = "ffpyplayer"

    def __init__(self):
        self._player = None
        self._stopped = True
        self._user_paused = False
        self._length = 0.0
        self._ready = False
        log.info("Аудио-бэкенд: ffpyplayer")

    def init(self):
        pass

    def _close(self):
        if not self._player:
            return
        try:
            self._player.set_pause(True)
        except Exception:
            pass
        try:
            self._player.close_player()
        except AttributeError:
            try:
                self._player.close()
            except Exception:
                pass
        except Exception:
            pass
        self._player = None

    def close(self):
        self._close()

    def _duration(self):
        if self._length > 0:
            return self._length
        import time as _t
        meta = {}
        for _ in range(5):
            if self._player:
                try:
                    meta = self._player.get_metadata() or {}
                except Exception:
                    meta = {}
                dur = float(meta.get("duration") or 0)
                if dur > 0:
                    self._length = dur
                    return dur
            _t.sleep(0.12)
        return 0.0

    def load(self, path):
        try:
            self._close()
            self._player = MediaPlayer(path, ff_opts={"paused": True})
            self._stopped = True
            self._user_paused = False
            self._ready = False
            self._length = 0.0
            import time as _t
            meta = {}
            for _ in range(40):
                try:
                    meta = self._player.get_metadata() or {}
                except Exception:
                    meta = {}
                if meta.get("duration"):
                    break
                _t.sleep(0.05)
            self._length = float(meta.get("duration") or 0)
            self._ready = True
            return True
        except Exception as e:
            log.error("ffpyplayer load error: %s", e)
            self._player = None
            return False

    def play(self, start=None):
        if not self._player:
            return
        if start is not None and self._ready:
            try:
                self._player.seek(float(start))
            except Exception:
                pass
        elif self._stopped and self._ready:
            try:
                self._player.seek(0.0)
            except Exception:
                pass
        try:
            self._player.set_pause(False)
        except Exception:
            pass
        self._stopped = False
        self._user_paused = False

    def pause(self):
        if not self._player:
            return
        try:
            self._player.set_pause(True)
        except Exception:
            pass
        self._user_paused = True

    def resume(self):
        if not self._player:
            return
        try:
            self._player.set_pause(False)
        except Exception:
            pass
        self._user_paused = False

    def stop(self):
        if not self._player:
            return
        try:
            self._player.set_pause(True)
            if self._ready:
                self._player.seek(0.0)
        except Exception:
            pass
        self._stopped = True
        self._user_paused = False

    def set_volume(self, v):
        if self._player:
            try:
                self._player.set_volume(float(v))
            except Exception:
                pass

    def get_pos(self):
        if not self._player:
            return 0.0
        try:
            return float(self._player.get_pts())
        except Exception:
            return 0.0

    def is_busy(self):
        if not self._player or self._stopped:
            return False
        if self._user_paused:
            return True
        dur = self._length
        if dur <= 0:
            dur = self._duration()
        if dur > 0 and self.get_pos() >= max(dur - 0.4, 0.0):
            return False
        return True

    def length_of(self, path):
        p = None
        try:
            p = MediaPlayer(path, ff_opts={"paused": True})
            import time as _t
            dur = 0.0
            for _ in range(6):
                meta = p.get_metadata() or {}
                dur = float(meta.get("duration") or 0)
                if dur > 0:
                    break
                _t.sleep(0.1)
            return dur
        except Exception:
            return 0.0
        finally:
            if p is not None:
                try:
                    p.set_pause(True)
                    p.close_player()
                except AttributeError:
                    try:
                        p.close()
                    except Exception:
                        pass
                except Exception:
                    pass


class PygameBackend:
    name = "pygame"

    def init(self):
        if not _mixer.get_init():
            _mixer.init()
        log.info("pygame.mixer инициализирован")

    def load(self, path):
        try:
            _mixer.music.load(path)
            return True
        except Exception as e:
            log.error("pygame load error: %s", e)
            return False

    def play(self, start=None):
        if start:
            _mixer.music.play(start=start)
        else:
            _mixer.music.play()

    def pause(self):
        _mixer.music.pause()

    def resume(self):
        _mixer.music.unpause()

    def stop(self):
        _mixer.music.stop()

    def set_volume(self, v):
        _mixer.music.set_volume(float(v))

    def get_pos(self):
        return _mixer.music.get_pos() / 1000.0

    def is_busy(self):
        return bool(_mixer.music.get_busy())

    def length_of(self, path):
        try:
            from mutagen import File as MutagenFile
            m = MutagenFile(path)
            if m and getattr(m, "info", None):
                return float(m.info.length)
        except Exception:
            pass
        return 0.0


class KivyBackend:
    name = "kivy-sdl2"

    def __init__(self):
        from kivy.core.audio import SoundLoader

        self._loader = SoundLoader
        self._sound = None
        self._base = 0.0
        self._t0 = 0.0
        self._paused = False
        self._stopped = True
        log.info("Аудио-бэкенд: Kivy SDL2")

    def init(self):
        pass

    def load(self, path):
        try:
            s = self._loader.load(path)
        except Exception as e:
            log.error("SoundLoader load error: %s", e)
            return False
        if not s:
            return False
        self._sound = s
        self._base = 0.0
        self._t0 = 0.0
        self._paused = False
        self._stopped = True
        return True

    def play(self, start=None):
        if not self._sound:
            return
        if start:
            self._base = float(start)
        else:
            self._base = 0.0
        import time
        self._t0 = time.monotonic()
        if self._sound.state == "stop":
            self._sound.play()
        try:
            self._sound.seek(self._base)
        except Exception:
            pass
        self._paused = False
        self._stopped = False

    def pause(self):
        if not self._sound:
            return
        self._paused = True
        try:
            self._sound.stop()
        except Exception:
            pass

    def resume(self):
        if not self._sound or not self._paused:
            return
        import time
        self._t0 = time.monotonic()
        self._sound.play()
        try:
            self._sound.seek(self._base)
        except Exception:
            pass
        self._paused = False

    def stop(self):
        if not self._sound:
            return
        self._stopped = True
        self._paused = False
        try:
            self._sound.stop()
        except Exception:
            pass

    def set_volume(self, v):
        if self._sound:
            self._sound.volume = float(v)

    def get_pos(self):
        if self._paused or self._stopped:
            return self._base
        import time
        return self._base + (time.monotonic() - self._t0)

    def is_busy(self):
        if not self._sound or self._stopped:
            return False
        if self._paused:
            return True
        try:
            return self._sound.state != "stop"
        except Exception:
            return True

    def length_of(self, path):
        try:
            s = self._loader.load(path)
            if s and getattr(s, "len", 0):
                return float(s.len)
        except Exception:
            pass
        return 0.0


def create_backend():
    if FFPY_OK:
        try:
            return FFPyBackend()
        except Exception as e:
            log.warning("ffpyplayer не инициализировался (%s) — пробуем pygame", e)
    if PYGAME_OK:
        try:
            b = PygameBackend()
            b.init()
            return b
        except Exception as e:
            log.warning("pygame.mixer не инициализировался (%s) — пробуем Kivy", e)
    try:
        return KivyBackend()
    except Exception as e:
        log.error("Аудио-бэкенд недоступен: %s", e)
        return None

import os
import sys
import threading
import traceback

def _crash_log(msg):
    import tempfile
    paths = [
        "/sdcard/fastmusic_crash.log",
        "/storage/emulated/0/fastmusic_crash.log",
        os.path.join(tempfile.gettempdir(), "fastmusic_crash.log"),
    ]
    for p in paths:
        try:
            with open(p, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
            return
        except Exception:
            continue

try:
    _crash_log("=== main.py import start ===")
except Exception:
    pass

try:
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.graphics import Color, Rectangle, RoundedRectangle
    from kivy.lang import Builder
    from kivy.metrics import dp
    from kivy.animation import Animation
    from kivy.utils import platform as _sys_platform
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.image import AsyncImage
    from kivy.uix.slider import Slider
    _crash_log("Kivy imports OK")
except Exception as e:
    _crash_log(f"Kivy import FAILED: {e}\n{traceback.format_exc()}")
    raise

try:
    from kivymd.app import MDApp
    from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
    from kivymd.uix.button import MDIconButton, MDFlatButton
    from kivymd.uix.card import MDCard
    from kivymd.uix.label import MDLabel
    from kivymd.uix.list import MDList
    from kivymd.uix.screenmanager import MDScreenManager
    from kivymd.uix.textfield import MDTextField
    from kivymd.uix.toolbar import MDTopAppBar
    _crash_log("KivyMD imports OK")
except Exception as e:
    _crash_log(f"KivyMD import FAILED: {e}\n{traceback.format_exc()}")
    raise

try:
    from kivymd.uix.snackbar import Snackbar
    HAS_SNACKBAR = True
except Exception:
    HAS_SNACKBAR = False

try:
    from kivymd.uix.menu import MDDropdownMenu
    HAS_MENU = True
except Exception:
    HAS_MENU = False

try:
    import logic
    from audio import create_backend
    from logger import get_logger
    _crash_log("logic/audio/logger imports OK")
except Exception as e:
    _crash_log(f"logic/audio import FAILED: {e}\n{traceback.format_exc()}")
    raise

log = get_logger(__name__)

try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

IS_MOBILE = _sys_platform in ("android", "ios")

if not IS_MOBILE:
    Window.size = (420, 800)

ROW_H = dp(66)
THUMB = dp(48)
COL_BG_A = (0.13, 0.15, 0.21, 1)
COL_BG_B = (0.16, 0.18, 0.25, 1)
COL_CARD_BG = (0.14, 0.16, 0.23, 1)
COL_TXT = (0.95, 0.96, 0.98, 1)
COL_TXT_SECONDARY = (0.62, 0.66, 0.75, 1)
COL_ACCENT = (0.35, 0.65, 1.0, 1)
COL_GRAY = (0.55, 0.58, 0.66, 1)
COL_GREEN = (0.28, 0.82, 0.48, 1)

class Row(BoxLayout):
    def __init__(self, text, art_url="", actions=None, badge=None,
                 number=None, alt=False, on_double=None, menu_items=None):
        super().__init__(
            orientation="horizontal", size_hint_y=None,
            height=ROW_H, padding=[dp(12), dp(6)], spacing=dp(10),
        )
        bg = COL_BG_A if not alt else COL_BG_B
        with self.canvas.before:
            self._rect_color = Color(*bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10),])
        self.bind(pos=self._upd_rect, size=self._upd_rect)

        self._on_double = on_double
        self._menu_items = menu_items or []
        self._menu_ref = None
        self._lp_event = None

        if number is not None:
            n = MDLabel(
                text=number, font_size="13sp", bold=True,
                theme_text_color="Custom", text_color=COL_ACCENT,
                size_hint_x=None, width=dp(26), halign="center",
                valign="middle",
            )
            self.add_widget(n)

        img = AsyncImage(
            source=art_url or "", size_hint=(None, None),
            size=(THUMB, THUMB), pos_hint={"center_y": 0.5},
            mipmap=True,
        )
        self.add_widget(img)

        # Розділення тексту треку на Назву та Виконавця для красивого дворівневого вигляду
        if " — " in text:
            parts = text.split(" — ", 1)
            artist_part, title_part = parts[0], parts[1]
            text_box = BoxLayout(orientation="vertical", pos_hint={"center_y": 0.5}, spacing=dp(2))
            t_lbl = MDLabel(
                text=title_part, font_size="13sp", bold=True,
                theme_text_color="Custom", text_color=COL_TXT,
                shorten=True, shorten_from="right"
            )
            a_lbl = MDLabel(
                text=artist_part, font_size="11sp",
                theme_text_color="Custom", text_color=COL_TXT_SECONDARY,
                shorten=True, shorten_from="right"
            )
            text_box.add_widget(t_lbl)
            text_box.add_widget(a_lbl)
            self.add_widget(text_box)
        else:
            label = MDLabel(
                text=text, font_size="13sp", bold=True,
                theme_text_color="Custom", text_color=COL_TXT,
                valign="middle", shorten=True, shorten_from="right",
            )
            self.add_widget(label)

        if badge:
            b = MDLabel(
                text=badge, font_size="10sp", bold=True,
                theme_text_color="Custom", text_color=COL_GREEN,
                size_hint_x=None, width=dp(36), halign="center", valign="middle",
            )
            self.add_widget(b)

        for icon, cb, tip in (actions or []):
            btn = MDIconButton(
                icon=icon, theme_icon_color="Custom",
                icon_color=COL_ACCENT, size=[dp(38), dp(38)],
                pos_hint={"center_y": 0.5}, md_bg_color=(0, 0, 0, 0),
            )
            btn.bind(on_release=cb)
            self.add_widget(btn)

    def _upd_rect(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Контекстне меню на праву кнопку миші
            if getattr(touch, "button", None) in ("right", "secondary"):
                Clock.schedule_once(lambda dt: self._open_menu(), 0)
                return True
            if touch.is_double_tap and self._on_double:
                Clock.schedule_once(lambda dt: self._on_double(), 0)
                return True
            if self._menu_items:
                self._lp_event = Clock.schedule_once(
                    lambda dt: self._open_menu(), 0.5)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._lp_event:
            self._lp_event.cancel()
            self._lp_event = None
        return super().on_touch_up(touch)

    def _open_menu(self):
        self._lp_event = None
        if not HAS_MENU or not self._menu_items:
            return
        items = []
        for label, cb in self._menu_items:
            def inner(*a, cb=cb):
                if self._menu_ref:
                    self._menu_ref.dismiss()
                    self._menu_ref = None
                Clock.schedule_once(lambda dt: cb(), 0.1)
            items.append({
                "text": label,
                "viewclass": "OneLineListItem",
                "theme_text_color": "Custom",
                "text_color": COL_TXT,
                "on_release": inner,
                "height": dp(44),
            })
        menu = MDDropdownMenu(
            caller=self, items=items, width_mult=4,
            background_color=(0.16, 0.18, 0.26, 1),
        )
        self._menu_ref = menu
        menu.open()


class FastMusicApp(MDApp):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.audio = create_backend()
        self.current_path = None
        self.current_name = ""
        self.current_art_url = None
        self.current_duration = 0.0
        self.seek_base = 0.0
        self._is_playing = False
        self._is_paused = False
        self._seek_updating = False
        self._is_scrubbing = False
        self._current_view = None
        self._artist_id = None
        self._artist_name = ""
        self.search_mode = "Усі"
        self._lib_cache = {}
        self._dl_rows = {}
        self._fill_events = {}
        self._pulse_events = {}
        self._meta_clear_ev = None
        self.volume_value = 0.5

    def build(self):
        _crash_log("build() called")
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        try:
            kv_path = os.path.join(os.path.dirname(__file__), 'fastmusic.kv')
            _crash_log(f"Loading KV: {kv_path}")
            root = Builder.load_file(kv_path)
            _crash_log("KV loaded OK")
            return root
        except Exception as e:
            _crash_log(f"KV load FAILED: {e}\n{traceback.format_exc()}")
            raise

    def on_start(self):
        _crash_log("on_start() called")
        try:
            log.info("Запуск FastMusic Kivy (Українська версія)")
            logic.init_db()
            _crash_log("init_db() OK")
        except Exception as e:
            _crash_log(f"init_db FAILED: {e}\n{traceback.format_exc()}")
            raise
        ids = self.root.ids

        if self.audio:
            try:
                self.audio.set_volume(self.volume_value)
            except Exception as e:
                log.warning("Не вдалося застосувати гучність: %s", e)
        else:
            self._snack("Аудіо недоступне на цьому пристрої")

        self._build_search_modes()
        _crash_log("on_start() binding widgets...")
        try:
            ids.search_field.bind(on_text_validate=lambda *a: self.search())
            ids.search_go.bind(on_release=lambda *a: self.search())
            ids.play_pause_btn.bind(on_release=lambda *a: self.toggle_play_pause())
            ids.vol_btn.bind(on_release=self.toggle_mute)
            ids.lib_refresh.bind(on_release=lambda *a: self.show_library())
            ids.dl_clear.bind(on_release=lambda *a: self.clear_done_dls())
            ids.related_btn.bind(on_release=lambda *a: self.show_related())
            _crash_log("widget bindings OK")
        except Exception as e:
            _crash_log(f"widget binding FAILED: {e}\n{traceback.format_exc()}")
            raise

        # Fixing track slider scrubber touch bindings
        try:
            seek = ids.seek
            seek.bind(on_touch_down=self._on_seek_touch_down)
            seek.bind(on_touch_up=self._on_seek_touch_up)
            seek.bind(value=self._on_seek_value_change)
            _crash_log("seek binding OK")
        except Exception as e:
            _crash_log(f"seek binding FAILED: {e}\n{traceback.format_exc()}")
            raise

        try:
            ids.nav.bind(current=self.on_nav_change)
        except Exception:
            pass
        try:
            ids.nav.bind(on_switch_tab=self.on_nav_change)
        except Exception:
            pass

        if not IS_MOBILE:
            Window.bind(on_key_down=self.on_key_down)

        Clock.schedule_interval(self.update_seek_bar, 0.5)
        _crash_log("on_start() calling show_charts()...")
        try:
            self.show_charts()
            _crash_log("show_charts() OK")
        except Exception as e:
            _crash_log(f"show_charts FAILED: {e}\n{traceback.format_exc()}")
            raise
        log.info("FastMusic готовий до роботи")

    # ─────────── NAVIGATION ───────────

    def on_nav_change(self, nav, tab_name):
        name = tab_name if isinstance(tab_name, str) else getattr(tab_name, 'name', '')
        if name == "charts":
            self.show_charts()
        elif name == "library":
            self.show_library()

    def go_back(self):
        self.root.current = "main"

    # ─────────── LOADING ───────────

    def _load_ids(self, view):
        i = self.root.ids
        return i[f"{view}_spin"], i[f"{view}_load"]

    def _show_loading(self, view, text="Завантаження"):
        spin, lbl = self._load_ids(view)
        spin.opacity = 1
        spin.active = True
        ev = self._pulse_events.get(view)
        if ev:
            ev.cancel()
        self._pulse(view, text, 0)

    def _pulse(self, view, text, dots):
        _, lbl = self._load_ids(view)
        lbl.text = text + "." * dots
        self._pulse_events[view] = Clock.schedule_once(
            lambda dt: self._pulse(view, text, (dots + 1) % 4), 0.4)

    def _hide_loading(self, view):
        spin, lbl = self._load_ids(view)
        spin.opacity = 0
        spin.active = False
        lbl.text = ""
        ev = self._pulse_events.pop(view, None)
        if ev:
            ev.cancel()

    def _snack(self, msg):
        log.info("Сповіщення: %s", msg)
        if HAS_SNACKBAR:
            try:
                Snackbar(text=msg).open()
            except Exception:
                pass

    # ─────────── SEARCH MODES ───────────

    def _build_search_modes(self):
        box = self.root.ids.search_modes
        box.clear_widgets()
        for mode in ("Усі", "Треки", "Альбоми", "Виконавці"):
            is_sel = (mode == self.search_mode)
            btn = MDFlatButton(
                text=mode, font_size="12sp",
                theme_text_color="Custom",
                text_color=COL_ACCENT if is_sel else COL_GRAY,
                md_bg_color=(0.18, 0.22, 0.32, 1) if is_sel else (0.12, 0.14, 0.19, 1),
            )
            btn.bind(on_release=lambda b, m=mode: self.set_search_mode(m))
            box.add_widget(btn)

    def set_search_mode(self, mode):
        self.search_mode = mode
        log.info("Режим пошуку: %s", mode)
        box = self.root.ids.search_modes
        for w in box.children:
            is_sel = (w.text == mode)
            w.text_color = COL_ACCENT if is_sel else COL_GRAY
            w.md_bg_color = (0.18, 0.22, 0.32, 1) if is_sel else (0.12, 0.14, 0.19, 1)

            btn = MDFlatButton(
                text=mode, font_size="12sp",
                theme_text_color="Custom",
                text_color=COL_ACCENT if mode == self.search_mode else COL_GRAY,
            )
            btn.bind(on_release=lambda b, m=mode: self.set_search_mode(m))
            box.add_widget(btn)

    def set_search_mode(self, mode):
        self.search_mode = mode
        log.info("Режим пошуку: %s", mode)
        box = self.root.ids.search_modes
        for w in box.children:
            w.text_color = COL_ACCENT if w.text == mode else COL_GRAY

    # ─────────── PAGES ───────────

    def show_charts(self, *_a):
        log.info("Користувач: відкрити чарти")
        self._current_view = "charts"
        self._show_loading("charts", "Завантажуємо чарти")
        threading.Thread(target=self._fetch_charts, daemon=True).start()

    def show_library(self, *_a):
        log.info("Користувач: відкрити бібліотеку")
        self._current_view = "library"
        self._show_loading("library", "Завантажуємо бібліотеку")
        threading.Thread(target=self._fetch_library, daemon=True).start()

    def show_artist(self, artist_id, artist_name):
        log.info("Користувач: відкрити виконавця id=%d '%s'", artist_id, artist_name)
        self._artist_id = artist_id
        self._artist_name = artist_name or ""
        self.root.ids.artist_bar.title = self._artist_name
        self.root.current = "artist"
        self._show_loading("artist", f"Завантажуємо {self._artist_name}")
        threading.Thread(target=self._fetch_artist_top, daemon=True).start()

    def show_artist_by_name(self, artist_name):
        log.info("Пошук виконавця за назвою з бібліотеки: '%s'", artist_name)
        self._show_loading("library", f"Завантажуємо {artist_name}")

        def worker():
            try:
                artists = logic.search_artists(artist_name)
                if artists and len(artists) > 0:
                    aid = artists[0]["id"]
                    aname = artists[0]["name"]
                    Clock.schedule_once(lambda dt: self.show_artist(aid, aname))
                else:
                    # Резервний варіант: шукаємо треки виконавця через загальний пошук
                    tracks = logic.search_deezer(artist_name)
                    if tracks and len(tracks) > 0 and "artist" in tracks[0]:
                        aid = tracks[0]["artist"]["id"]
                        aname = tracks[0]["artist"]["name"]
                        Clock.schedule_once(lambda dt: self.show_artist(aid, aname))
                    else:
                        Clock.schedule_once(lambda dt: self._snack(f"Виконавця '{artist_name}' не знайдено"))
            except Exception as e:
                log.error("Помилка пошуку виконавця: %s", e)
                Clock.schedule_once(lambda dt: self._snack("Не вдалося завантажити виконавця"))
            finally:
                Clock.schedule_once(lambda dt: self._hide_loading("library"))

        threading.Thread(target=worker, daemon=True).start()

    def show_related(self, *_a):
        if not self._artist_id:
            return
        log.info("Користувач: схожі на id=%d '%s'", self._artist_id, self._artist_name)
        self._show_loading("artist", f"Завантажуємо схожих на {self._artist_name}")
        threading.Thread(target=self._fetch_related, daemon=True).start()

    def search(self, *_a):
        q = self.root.ids.search_field.text.strip()
        if not q:
            log.debug("Пошук: порожній запит")
            return
        mode = self.search_mode
        log.info("Пошук: '%s' тип='%s'", q, mode)
        self._current_view = "search"
        self.root.ids.nav.switch_tab("search")
        self._show_loading("search", "Пошук")
        threading.Thread(target=self._fetch_search, args=(q, mode), daemon=True).start()

    # ─────────── FETCH (thread) ───────────

    def _refresh_lib_cache(self):
        try:
            self._lib_cache = logic.load_all_library()
        except Exception as e:
            log.warning("Не вдалося завантажити кеш бібліотеки: %s", e)
            self._lib_cache = {}

    def _fetch_search(self, query, mode):
        log.info("Пошук: '%s' режим='%s'", query, mode)
        if mode == "Альбоми":
            items = logic.search_albums(query)
        elif mode == "Виконавці":
            items = logic.search_artists(query)
        else:
            items = logic.search_deezer(query)
        log.info("Пошук: отримано %d результатів", len(items))
        self._refresh_lib_cache()
        Clock.schedule_once(lambda dt: self._render_search(items))

    def _fetch_charts(self):
        tracks = logic.get_charts()
        log.info("Чарти: отримано %d треків", len(tracks))
        self._refresh_lib_cache()
        Clock.schedule_once(lambda dt: self._render_charts(tracks))

    def _fetch_artist_top(self):
        tracks = logic.get_artist_top(self._artist_id)
        log.info("Топ треків: отримано %d треків", len(tracks))
        self._refresh_lib_cache()
        aid, aname = self._artist_id, self._artist_name
        Clock.schedule_once(lambda dt: self._render_artist_top(tracks, aname, aid))

    def _fetch_related(self):
        artists = logic.get_related_artists(self._artist_id)
        log.info("Схожі: отримано %d виконавців", len(artists))
        Clock.schedule_once(lambda dt: self._render_related(artists))

    def _fetch_library(self):
        tracks = logic.get_library()
        log.info("Бібліотека: %d треків", len(tracks))
        Clock.schedule_once(lambda dt: self._render_library(tracks))

    # ─────────── FILL HELPER (batched render) ───────────

    def _fill(self, list_id, makers, batch=5):
        ev = self._fill_events.pop(list_id, None)
        if ev:
            ev.cancel()
        lst = self.root.ids[list_id]
        lst.clear_widgets()
        view = list_id.replace("_list", "")
        self._hide_loading(view)
        state = {"i": 0}

        def step(dt=None):
            i = state["i"]
            end = min(i + batch, len(makers))
            for maker in makers[i:end]:
                try:
                    lst.add_widget(maker())
                except Exception as e:
                    log.error("Помилка рендеру рядка: %s", e, exc_info=True)
            state["i"] = end
            if end < len(makers):
                self._fill_events[list_id] = Clock.schedule_once(step, 0.015)

        step()

    def _in_lib(self, artist, title):
        key = (artist.lower(), title.lower())
        return bool(self._lib_cache.get(key)) or bool(logic.is_in_library(artist, title))

    # ─────────── ROW MAKERS ───────────

    def _track_row(self, track, idx=0, numbered=False):
        title = track["title"]
        artist_name = track["artist"]["name"]
        artist_id = track["artist"]["id"]
        art_url = track["album"].get("cover_medium") or track["album"].get("cover_small") or ""
        preview_url = track.get("preview")
        in_lib = self._in_lib(artist_name, title)
        lib_path = self._lib_cache.get((artist_name.lower(), title.lower()))

        actions = []
        if preview_url:
            play_cb = (lambda *a, u=preview_url, t=title, ar=artist_name, img=art_url:
                       self.play_preview(u, t, ar, img))
        elif lib_path:
            play_cb = (lambda *a, p=lib_path, n=f"{artist_name} — {title}", img=art_url:
                       self.play_music(p, n, img))
        else:
            play_cb = None

        if play_cb:
            actions.append(("play", play_cb, "Прев'ю"))
        actions.append(("download", lambda *a, ar=artist_name, t=title, img=art_url:
                        self.start_download(ar, t, img), "Завантажити"))
        actions.append(("information-outline", lambda *a, aid=artist_id, an=artist_name:
                        self.show_artist(aid, an), "Виконавець"))

        menu_items = [
            ("▶ Прев'ю 30 с" if preview_url else "▶ Повна версія",
             (lambda *a, u=preview_url, t=title, ar=artist_name, img=art_url:
              self.play_preview(u, t, ar, img)) if preview_url else
             (lambda *a, ar=artist_name, t=title, img=art_url:
              self.play_full(ar, t, img))),
        ]
        if lib_path:
            menu_items.append(("▶ З бібліотеки",
                               lambda *a, p=lib_path, n=f"{artist_name} — {title}", img=art_url:
                               self.play_music(p, n, img)))
        menu_items.append(("⬇ Завантажити",
                           lambda *a, ar=artist_name, t=title, img=art_url:
                           self.start_download(ar, t, img)))
        menu_items.append(("ℹ Виконавець",
                           lambda *a, aid=artist_id, an=artist_name:
                           self.show_artist(aid, an)))

        badge = "MP3" if in_lib else None
        num = str(idx + 1) if numbered else None
        text = f"{artist_name} — {title}"
        return Row(text=text, art_url=art_url, actions=actions, badge=badge,
                   number=num, alt=bool(idx % 2),
                   on_double=play_cb, menu_items=menu_items)

    def _album_row(self, album, idx=0):
        art_url = album.get("cover_medium") or album.get("cover_small") or ""
        count = album.get("tracks_count") or ""
        text = f"{album['artist']} — {album['title']} ({count} тр.)"
        return Row(text=text, art_url=art_url, alt=bool(idx % 2))

    def _artist_row(self, a, idx=0):
        fans = a.get("nb_fans") or 0
        text = f"{a['name']} — {fans:,} шанувальників".replace(",", " ")
        actions = [("account-music-outline", lambda *a, aid=a["id"], an=a["name"]:
                    self.show_artist(aid, an), "Топ")]
        menu_items = [("ℹ Топ треків", lambda *a, aid=a["id"], an=a["name"]:
                       self.show_artist(aid, an))]
        return Row(text=text, art_url=a.get("picture_medium") or "",
                   actions=actions, alt=bool(idx % 2), menu_items=menu_items)

    # ─────────── RENDER ───────────

    def _render_search(self, items):
        log.info("Рендер результатів: %d елементів", len(items))
        makers = []
        for idx, item in enumerate(items):
            t = item.get("_type")
            if t == "album":
                makers.append(lambda it=item, i=idx: self._album_row(it, i))
            elif t == "artist":
                makers.append(lambda it=item, i=idx: self._artist_row(it, i))
            else:
                makers.append(lambda it=item, i=idx: self._track_row(it, i))
        self._fill("search_list", makers)
        log.info("Рендер результатів завершено")

    def _render_charts(self, tracks):
        log.info("Рендер чартів: %d треків", len(tracks))
        makers = [lambda tr=track, i=idx: self._track_row(tr, i, numbered=True)
                  for idx, track in enumerate(tracks)]
        self._fill("charts_list", makers)
        log.info("Рендер чартів завершено")

    def _render_artist_top(self, tracks, artist_name, artist_id):
        log.info("Рендер треків виконавця '%s': %d треків", artist_name, len(tracks))
        makers = [lambda tr=t, i=idx: self._track_row(tr, i)
                  for idx, t in enumerate(tracks)]
        self._fill("artist_list", makers)
        log.info("Рендер треків виконавця завершено")

    def _render_related(self, artists):
        log.info("Рендер схожих: %d виконавців", len(artists))
        makers = [lambda a=a, i=idx: self._artist_row(a, i)
                  for idx, a in enumerate(artists)]
        self._fill("artist_list", makers)

    def _render_library(self, tracks):
        log.info("Рендер бібліотеки: %d треків", len(tracks))
        makers = []
        for idx, t in enumerate(tracks):
            tid, title, artist, art, fpath = t[:5]

            def make(tid=tid, title=title, artist=artist, art=art, fpath=fpath, idx=idx):
                play_cb = (lambda *a, p=fpath, n=f"{artist} — {title}", img=art:
                           self.play_music(p, n, img))
                actions = [
                    ("play", play_cb, "Слухати"),
                    ("information-outline", lambda *a, an=artist: self.show_artist_by_name(an), "Виконавець"),
                    ("delete-outline", lambda *a, t_id=tid: self.delete_track(t_id), "Видалити"),
                ]
                menu_items = [
                    ("▶ Відтворити", play_cb),
                    ("ℹ Про виконавця", lambda *a, an=artist: self.show_artist_by_name(an)),
                    ("🗑 Видалити трек", lambda *a, t_id=tid: self.delete_track(t_id)),
                ]
                return Row(text=f"{artist} — {title}", art_url=art or "",
                           actions=actions, badge="MP3", alt=bool(idx % 2),
                           on_double=play_cb, menu_items=menu_items)
            makers.append(make)

        self._fill("library_list", makers)
        log.info("Рендер бібліотеки завершено")

    def delete_track(self, track_id):
        log.info("Видалення треку id=%s", track_id)
        logic.delete_from_db(track_id)
        self.show_library()

    def toggle_play_pause(self, *_a):
        if not self._is_playing or not self.audio:
            return
        if self._is_paused:
            self.audio.resume()
            self._is_paused = False
        else:
            self.audio.pause()
            self._is_paused = True
        self._update_play_pause_btn()

    def _update_play_pause_btn(self):
        btn = self.root.ids.play_pause_btn
        if self._is_playing and not self._is_paused:
            btn.icon = "pause"
        else:
            btn.icon = "play"

    def play_preview(self, url, title, artist, art_url):
        log.info("Відтворення прев'ю: '%s — %s'", artist, title)
        if not self.audio:
            self._snack("Аудіо недоступне")
            return
        self._set_meta("Завантаження прев'ю…")

        def worker():
            path = logic.download_preview(url)
            Clock.schedule_once(lambda dt: self._after_preview(path, url, title, artist, art_url))

        threading.Thread(target=worker, daemon=True).start()

    def _after_preview(self, path, url, title, artist, art_url):
        if not path:
            log.error("Preview: файл не завантажено")
            self._set_meta("❌ Прев'ю недоступне", clear_after=3.0)
            return
        self.current_duration = 30.0
        self.current_path = path
        self.current_name = f"{artist} — {title}"
        self.current_art_url = art_url
        if not self.audio.load(path):
            self._set_meta("❌ Помилка аудіо", clear_after=3.0)
            return
        self.audio.play()
        self.root.ids.player_title.text = self.current_name
        self.root.ids.player_art.source = art_url or ""
        self._set_meta("Прев'ю 30 с")
        self.seek_base = 0.0
        self.root.ids.seek.value = 0
        self._is_playing = True
        self._is_paused = False
        self._update_play_pause_btn()
        log.info("Прев'ю лунає: '%s'", path)

    def play_full(self, artist, title, art_url):
        log.info("Повне відтворення: '%s — %s'", artist, title)
        self._set_meta("Завантаження треку…")

        def worker():
            path = logic.download_track(artist, title, art_url)
            if path:
                Clock.schedule_once(lambda dt: self._start_playback(path, f"{artist} — {title}", art_url))
            else:
                Clock.schedule_once(lambda dt: self._set_meta("❌ Не вдалося завантажити трек", clear_after=3.0))

        threading.Thread(target=worker, daemon=True).start()

    def _start_playback(self, path, name, art_url):
        log.info("Старт відтворення: '%s'", name)
        if not self.audio:
            self._snack("Аудіо недоступне")
            return
        self.current_path = path
        self.current_name = name
        self.current_art_url = art_url
        self.current_duration = 0.0

        if HAS_MUTAGEN and os.path.exists(path):
            try:
                self.current_duration = MutagenFile(path).info.length
            except Exception as e:
                log.warning("Не вдалося прочитати тривалість: %s", e)
        if not self.current_duration:
            try:
                self.current_duration = self.audio.length_of(path)
            except Exception:
                pass
        log.info("Тривалість треку: %.1f сек", self.current_duration)

        if not self.audio.load(path):
            self._set_meta("❌ Помилка аудіо", clear_after=3.0)
            return
        self.audio.play()

        self.root.ids.player_title.text = name
        self.root.ids.player_art.source = art_url or ""
        self._set_meta("")
        self.seek_base = 0.0
        self.root.ids.seek.value = 0
        self._is_playing = True
        self._is_paused = False
        self._update_play_pause_btn()
        log.info("Відтворення розпочато: '%s'", name)

    def play_music(self, path, name, art_url=None):
        log.info("Відтворення файлу: '%s'", name)
        if not os.path.exists(path):
            log.error("Файл не знайдено: %s", path)
            self._snack("Файл не знайдено")
            return
        self._start_playback(path, name, art_url)

    def _set_meta(self, text, clear_after=None):
        if "player_meta" in self.root.ids:
            self.root.ids.player_meta.text = text
        if self._meta_clear_ev:
            self._meta_clear_ev.cancel()
            self._meta_clear_ev = None
        if clear_after and "player_meta" in self.root.ids:
            self._meta_clear_ev = Clock.schedule_once(
                lambda dt: setattr(self.root.ids.player_meta, "text", ""), clear_after)

    # ─────────── SCRUBBER / SEEKBAR FIX ───────────

    def _get_current_pos(self):
        """Отримує точну поточну позицію треку, враховуючи особливості різних брушіїв (ffpyplayer vs pygame)"""
        if not self.audio:
            return 0.0
        try:
            raw_pos = float(self.audio.get_pos())
        except Exception:
            raw_pos = 0.0

        # Якщо брушій повертає абсолютну позицію (як ffpyplayer), raw_pos буде близьким до seek_base
        if self.seek_base > 1.0 and raw_pos >= (self.seek_base - 1.0):
            return raw_pos
        # Якщо брушій повертає відносний час від початку програвання (як pygame)
        return self.seek_base + raw_pos

    def _on_seek_touch_down(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self._is_scrubbing = True

    def _on_seek_value_change(self, instance, value):
        if self._is_scrubbing and self.current_duration > 0:
            pos = (value / 100.0) * self.current_duration
            self.root.ids.time_lbl.text = (
                f"{self._fmt_time(pos)} / {self._fmt_time(self.current_duration)}")

    def _on_seek_touch_up(self, instance, touch):
        if self._is_scrubbing:
            self._is_scrubbing = False
            max_val = instance.max if instance.max > 0 else 100.0
            pct = max(0.0, min(1.0, instance.value / max_val))
            self._do_seek(pct)

    def _do_seek(self, pct):
        if not self._is_playing or not self.audio:
            return
        if self.current_duration <= 0:
            return
        pct = max(0.0, min(1.0, float(pct)))
        pos = pct * self.current_duration
        was_paused = self._is_paused
        try:
            if hasattr(self.audio, 'seek'):
                self.audio.seek(pos)
            else:
                if self.current_path and os.path.exists(self.current_path):
                    self.audio.load(self.current_path)
                self.audio.play(start=pos)
            self.seek_base = pos
            if was_paused:
                self.audio.pause()
            log.info("Перемотування успішне: %.1f%% -> %.1f сек", pct * 100, pos)
        except Exception as e:
            log.warning("Помилка seek: %s", e)

    def _set_volume(self, v):
        v = max(0.0, min(1.0, float(v)))
        self.volume_value = v
        if self.audio:
            try:
                self.audio.set_volume(v)
            except Exception:
                pass
        try:
            muted = getattr(self, "_muted", False) or v <= 0.001
            self.root.ids.vol_btn.icon = "volume-off" if muted else "volume-high"
        except Exception:
            pass
        log.debug("Гучність: %.2f", v)

    def toggle_mute(self, *_a):
        if getattr(self, "_muted", False) or self.volume_value <= 0.001:
            self._muted = False
            self._set_volume(getattr(self, "_prev_volume", None) or 0.5)
        else:
            self._muted = True
            self._prev_volume = self.volume_value
            self._set_volume(0.0)

    def update_seek_bar(self, dt):
        if not self._is_playing or not self.audio or self._is_scrubbing:
            return
        busy = self.audio.is_busy() or self._is_paused
        if busy:
            pos = self._get_current_pos()
            if self.current_duration > 0:
                pct = min(pos / self.current_duration * 100, 100)
                self._seek_updating = True
                self.root.ids.seek.value = pct
                self._seek_updating = False
                self.root.ids.time_lbl.text = (
                    f"{self._fmt_time(pos)} / {self._fmt_time(self.current_duration)}")
        else:
            self._is_playing = False
            self._is_paused = False
            self._update_play_pause_btn()
            self._set_meta("")
            self.root.ids.time_lbl.text = "0:00 / 0:00"
            if self.root.ids.seek.value != 0:
                self.root.ids.seek.value = 0

    @staticmethod
    def _fmt_time(sec):
        m = int(sec // 60)
        s = int(sec % 60)
        return f"{m}:{s:02d}"

    # ─────────── KEYBOARD (desktop only) ───────────

    def on_key_down(self, window, key, scancode=None, codepoint=None, modifier=None):
        field = self.root.ids.search_field
        if getattr(field, "focus", False):
            return False
        if key == 32:
            self.toggle_play_pause()
        elif key == 276:
            self._seek_rel(-5)
        elif key == 275:
            self._seek_rel(5)
        elif key == 273:
            self._set_volume(self.volume_value + 0.05)
        elif key == 274:
            self._set_volume(self.volume_value - 0.05)
        else:
            return False
        return True

    def _seek_rel(self, sec):
        if not self._is_playing or self.current_duration <= 0:
            return
        cur = self._get_current_pos()
        new = max(0, min(cur + sec, self.current_duration))
        pct = new / self.current_duration
        self._do_seek(pct)

    # ─────────── DOWNLOADS ───────────

    def start_download(self, artist, title, img_url):
        log.info("Запуск завантаження: '%s — %s'", artist, title)
        key = (artist, title)
        if key in self._dl_rows:
            return
        card = self.root.ids.dl_card
        if card.height < dp(60):
            card.opacity = 1
            Animation(height=dp(118), d=0.2).start(card)

        row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(4))
        icon = MDLabel(text="⬇", font_size="11sp", size_hint_x=None,
                       width=dp(16), valign="middle",
                       theme_text_color="Custom", text_color=COL_TXT)
        label = MDLabel(text=f"{artist[:15]} — {title[:20]}", font_size="11sp",
                        valign="middle", shorten=True,
                        theme_text_color="Custom", text_color=COL_TXT)
        status = MDLabel(text="…", font_size="10sp", size_hint_x=None,
                         width=dp(50), halign="right", valign="middle",
                         theme_text_color="Custom", text_color=COL_GRAY)
        row.add_widget(icon)
        row.add_widget(label)
        row.add_widget(status)
        self.root.ids.dl_list.add_widget(row)
        self._dl_rows[key] = (row, icon, status)

        threading.Thread(target=self.do_download, args=(artist, title, img_url, key),
                         daemon=True).start()

    def do_download(self, artist, title, img_url, key):
        log.info("Завантаження: '%s — %s'", artist, title)
        file_path = logic.download_track(artist, title, img_url)
        if file_path:
            logic.save_to_db(title, artist, img_url, file_path)
            self._refresh_lib_cache()
            Clock.schedule_once(lambda dt: self._set_dl_status(key, "✅", "Готово"))
            if self._current_view == "library" and \
                    self.root.ids.nav.current == "library":
                Clock.schedule_once(lambda dt: self.show_library(), 0.5)
        else:
            Clock.schedule_once(lambda dt: self._set_dl_status(key, "❌", "Помилка"))
            Clock.schedule_once(lambda dt: self._snack(f"Не вдалося завантажити: {title}"))
            log.error("Не вдалося завантажити '%s — %s'", artist, title)

    def _set_dl_status(self, key, icon_text, status_text=""):
        item = self._dl_rows.get(key)
        if not item:
            return
        row, icon, status = item
        icon.text = icon_text
        status.text = status_text

    def clear_done_dls(self, *_a):
        done_icons = {"✅", "❌"}
        for key in list(self._dl_rows.keys()):
            row, icon, status = self._dl_rows[key]
            if icon.text in done_icons:
                self.root.ids.dl_list.remove_widget(row)
                del self._dl_rows[key]
        if not self._dl_rows:
            card = self.root.ids.dl_card
            anim = Animation(height=0, opacity=0, d=0.2)
            anim.start(card)


if __name__ == "__main__":
    import builtins
    _orig_excepthook = sys.excepthook
    def _log_excepthook(exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _crash_log(f"UNCAUGHT EXCEPTION:\n{tb}")
        _orig_excepthook(exc_type, exc_value, exc_tb)
    sys.excepthook = _log_excepthook

    def _log_thread_exception(args):
        tb = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
        _crash_log(f"THREAD EXCEPTION:\n{tb}")
    threading.excepthook = _log_thread_exception

    _crash_log("=== Starting FastMusicApp ===")
    FastMusicApp().run()
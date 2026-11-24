import os
import threading
from PIL import Image
import customtkinter as ctk
from pygame import mixer

import logic
from logger import get_logger

log = get_logger(__name__)

try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
    log.info("mutagen доступен")
except ImportError:
    HAS_MUTAGEN = False
    log.warning("mutagen не установлен, длительность не определяется")

PLAYER_ART_SIZE = 130
ROW_IMG_SIZE = 44

ctk.set_appearance_mode("Dark")


class MusicApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FastMusic")
        self.geometry("1100x720")
        log.info("Запуск FastMusic")

        mixer.init()
        log.info("pygame.mixer инициализирован")
        logic.init_db()

        # left column: content, right column: player
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=280)
        self.grid_rowconfigure(1, weight=1)

        self.minsize(800, 480)

        self._nav_buttons = []
        self._resize_timer = None
        self._seek_updating = False

        self.bind("<Configure>", self._on_resize)

        self._setup_search_top()
        self._setup_content()
        self._setup_player()

        self.current_path = None
        self.current_name = "Ничего не играет"
        self.current_art_url = None
        self.current_duration = 0
        self.current_seek_start = 0.0
        self._is_playing = False
        self._is_paused = False
        self._current_view = None
        self._player_ctk_image = None
        self._blank_image = ctk.CTkImage(
            light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 0)),
            dark_image=Image.new("RGBA", (1, 1), (0, 0, 0, 0)),
            size=(1, 1),
        )

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.update_seek_bar()
        self._bind_shortcuts()
        log.info("FastMusic готов к работе")

    # ─────────── KEYBOARD SHORTCUTS ───────────

    def _bind_shortcuts(self):
        self.bind_all("<space>", lambda e: self.toggle_play_pause())
        self.bind_all("<Left>", lambda e: self._seek_rel(-5))
        self.bind_all("<Right>", lambda e: self._seek_rel(5))
        self.bind_all("<Up>", lambda e: self._adjust_vol(0.05))
        self.bind_all("<Down>", lambda e: self._adjust_vol(-0.05))

    def _seek_rel(self, sec):
        if not self._is_playing or self.current_duration <= 0:
            return
        cur = self.current_seek_start + mixer.music.get_pos() / 1000.0
        new = max(0, min(cur + sec, self.current_duration))
        pct = new / self.current_duration * 100
        self.seek_var.set(pct)
        self.seek_music(pct)

    def _adjust_vol(self, delta):
        v = max(0, min(1, self.volume_var.get() + delta))
        self.volume_var.set(v)
        mixer.music.set_volume(v)

    # ─────────── TOP SEARCH BAR ───────────

    def _setup_search_top(self):
        top = ctk.CTkFrame(self, height=46, corner_radius=0)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.grid_propagate(False)
        top.grid_columnconfigure(0, weight=1)

        entry_frame = ctk.CTkFrame(top, fg_color="transparent")
        entry_frame.grid(row=0, column=0, sticky="ew", padx=(12, 4), pady=8)

        self.search_entry = ctk.CTkEntry(entry_frame, placeholder_text="Поиск треков, альбомов, исполнителей…")
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda e: self.search())

        self.search_type_var = ctk.StringVar(value="Всё")
        self.search_type_menu = ctk.CTkOptionMenu(
            top, values=["Всё", "Треки", "Альбомы", "Исполнители"],
            variable=self.search_type_var, width=110)
        self.search_type_menu.grid(row=0, column=1, padx=(0, 4))

        ctk.CTkButton(top, text="Поиск", width=70, command=self.search).grid(row=0, column=2, padx=(0, 6))

        nav_frame = ctk.CTkFrame(top, fg_color="transparent")
        nav_frame.grid(row=0, column=3, padx=(0, 10))

        for text, cmd in [("Чарты", self.show_charts),
                  ("Мои аудио", self.show_library)]:
            btn = ctk.CTkButton(nav_frame, text=text, command=cmd,
                                width=60, fg_color="transparent",
                                text_color=("gray10", "gray90"),
                                hover_color=("gray75", "gray35"))
            btn.pack(side="left", padx=1)
            self._nav_buttons.append((text.lower(), btn))

    # ─────────── CONTENT ───────────

    def _setup_content(self):
        left = ctk.CTkFrame(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(10, 4), pady=10)
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.content_scroll = ctk.CTkScrollableFrame(left)
        self.content_scroll.grid(row=0, column=0, sticky="nsew")
        self.content_frame = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)

        # download panel below content
        self._dl_panel = ctk.CTkFrame(left, fg_color="transparent", height=100)
        self._dl_panel.grid(row=1, column=0, sticky="sew", pady=(6, 0))
        self._dl_panel.grid_propagate(False)
        dl_header = ctk.CTkFrame(self._dl_panel, fg_color="transparent")
        dl_header.pack(fill="x")
        ctk.CTkLabel(dl_header, text="Загрузки", font=("Arial", 10, "bold"),
                     text_color="gray").pack(side="left")
        self._dl_clear_btn = ctk.CTkButton(dl_header, text="✕", width=20, height=18,
                                            font=("Arial", 9), fg_color="transparent",
                                            text_color="gray", hover_color=("gray80", "gray30"),
                                            command=self._clear_done_dls)
        self._dl_clear_btn.pack(side="right")
        self._dl_scroll = ctk.CTkScrollableFrame(self._dl_panel, fg_color="transparent",
                                                   height=70)
        self._dl_scroll.pack(fill="both", expand=True, pady=(2, 0))
        self._dl_labels = {}

    # ─────────── PLAYER ───────────

    def _setup_player(self):
        self.player_frame = ctk.CTkFrame(self, corner_radius=8, width=280)
        self.player_frame.grid(row=1, column=1, sticky="ns", padx=(4, 10), pady=10)
        self.player_frame.grid_propagate(False)
        self.player_frame.grid_rowconfigure(0, weight=0)
        self.player_frame.grid_columnconfigure(0, weight=1)

        # album art
        self.player_art_label = ctk.CTkLabel(self.player_frame, text="", width=200, height=200)
        self.player_art_label.grid(row=0, column=0, pady=(16, 8))

        # track name
        self.current_track_label = ctk.CTkLabel(
            self.player_frame, text="Ничего не играет",
            font=("Arial", 15, "bold"), anchor="center", wraplength=250)
        self.current_track_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(10, 0))

        # artist
        self.current_meta_label = ctk.CTkLabel(
            self.player_frame, text="",
            font=("Arial", 12), text_color="gray", anchor="center", wraplength=250)
        self.current_meta_label.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 0))

        # play/pause
        ctrls = ctk.CTkFrame(self.player_frame, fg_color="transparent")
        ctrls.grid(row=3, column=0, pady=(10, 4))
        self.play_pause_btn = ctk.CTkButton(
            ctrls, text="▶", width=52, height=42,
            command=self.toggle_play_pause, font=("Arial", 18))
        self.play_pause_btn.pack()

        # seek slider
        self.seek_var = ctk.DoubleVar(value=0)
        self.seek_slider = ctk.CTkSlider(
            self.player_frame, variable=self.seek_var, from_=0, to=100,
            command=self.seek_music)
        self.seek_slider.grid(row=4, column=0, sticky="ew", padx=16, pady=(6, 0))

        # time label
        self.time_label = ctk.CTkLabel(
            self.player_frame, text="0:00 / 0:00",
            font=("Arial", 10), text_color="gray")
        self.time_label.grid(row=5, column=0, pady=(2, 0))

        # volume
        vol_frame = ctk.CTkFrame(self.player_frame, fg_color="transparent")
        vol_frame.grid(row=6, column=0, pady=(10, 16))
        ctk.CTkLabel(vol_frame, text="Громкость", font=("Arial", 11)).pack()
        self.volume_var = ctk.DoubleVar(value=0.5)
        ctk.CTkSlider(vol_frame, variable=self.volume_var, from_=0, to=1,
                       command=self.set_volume, width=140,
                       button_length=14).pack(pady=(4, 0))
        mixer.music.set_volume(0.5)

    # ─────────── CLOSE ───────────

    def _on_close(self):
        log.info("Завершение FastMusic")
        self.destroy()

    # ─────────── RESIZE ───────────

    def _on_resize(self, event=None):
        if self._resize_timer is not None:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(100, self._do_resize)

    def _do_resize(self):
        w = self.winfo_width()
        panel_w = max(240, min(400, w // 3))
        self.player_frame.configure(width=panel_w)
        art = max(120, min(240, panel_w - 60))
        try:
            self.player_art_label.configure(width=art, height=art)
        except Exception:
            pass
        log.debug("Ресайз: окно=%dx%d арт=%d", w, self.winfo_height(), art)

    # ─────────── PAGES ───────────

    def _clear(self):
        self._hide_loading()
        for w in self.content_frame.winfo_children():
            w.destroy()

    # ─────────── LOADING ───────────

    def _show_loading(self, text="Загрузка"):
        self._clear()
        self._loading_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self._loading_frame.pack(fill="both", expand=True)
        self._loading_label = ctk.CTkLabel(
            self._loading_frame, text=text, font=("Arial", 16), text_color="gray"
        )
        self._loading_label.pack(expand=True)
        self._pulse_loading(text, 0)

    def _pulse_loading(self, text, dots):
        if not hasattr(self, '_loading_label') or not self._loading_label:
            return
        self._loading_label.configure(text=text + "." * dots)
        self.after(400, lambda: self._pulse_loading(text, (dots + 1) % 4))

    def _hide_loading(self):
        if hasattr(self, '_loading_frame') and self._loading_frame:
            self._loading_frame.destroy()
            self._loading_frame = None
            self._loading_label = None

    def _img_from_data(self, data, size):
        if data:
            img = logic.image_from_bytes(data)
            if img:
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        return None

    # ─────────── CONTEXT MENU ───────────

    def _context_menu(self, event, artist=None, title=None, art_url=None,
                      preview_url=None, deezer_id=None, artist_id=None,
                      file_path=None, track_id=None, wish_id=None):
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white",
                       activebackground="#3a7ebf", activeforeground="white")
        has_preview = preview_url is not None
        in_lib = logic.is_in_library(artist, title) if artist and title else None

        if file_path:
            menu.add_command(label="▶ Воспроизвести",
                             command=lambda: self.play_music(file_path, f"{artist} — {title}", art_url))
        elif has_preview and artist_id:
            menu.add_command(label="▶ Превью 30с",
                             command=lambda: self.play_preview(preview_url, title, artist, art_url))
        elif has_preview:
            menu.add_command(label="▶ Полная версия",
                             command=lambda: self.play_full(artist, title, art_url))

        if in_lib:
            menu.add_command(label="▶ Из библиотеки",
                             command=lambda: self.play_music(in_lib[1], f"{artist} — {title}", art_url))
        else:
            menu.add_command(label="⬇ Скачать",
                             command=lambda: self.start_download(artist, title, art_url))

        if deezer_id:
            wid = logic.is_in_wishlist(deezer_id)
            if wid:
                menu.add_command(label="☆ Убрать из избранного",
                                 command=lambda wid=wid: self.unwish(wid))
            else:
                menu.add_command(label="★ В избранное",
                                 command=lambda: self.add_wish(title, artist, art_url, preview_url, deezer_id))

        if artist_id:
            menu.add_command(label="ℹ Исполнитель",
                             command=lambda: self.show_artist(artist_id, artist))

        if track_id:
            menu.add_command(label="🗑 Удалить трек",
                             command=lambda: self.delete_track(track_id))

        if wish_id:
            menu.add_command(label="✕ Удалить из избранного",
                             command=lambda wid=wish_id: self.unwish(wid, refresh=True))

        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()

    # ─────────── PLAY / PAUSE ───────────

    def toggle_play_pause(self):
        if not self._is_playing:
            return
        if self._is_paused:
            mixer.music.unpause()
            self._is_paused = False
        else:
            mixer.music.pause()
            self._is_paused = True
        self._update_play_pause_btn()

    def _update_play_pause_btn(self):
        if self._is_playing and not self._is_paused:
            self.play_pause_btn.configure(text="⏸")
        else:
            self.play_pause_btn.configure(text="▶")

    def _activate_nav(self, name):
        for key, btn in self._nav_buttons:
            btn.configure(fg_color="transparent")
        for key, btn in self._nav_buttons:
            if key == name:
                btn.configure(fg_color=("gray70", "gray30"))

    def show_charts(self):
        log.info("Пользователь: открыть чарты")
        self._current_view = "charts"
        self._activate_nav("чарты")
        self._show_loading("Загружаем чарты")
        threading.Thread(target=self._fetch_charts, daemon=True).start()

    def show_library(self):
        log.info("Пользователь: открыть библиотеку")
        self._current_view = "library"
        self._activate_nav("мои аудио")
        self._show_loading("Загружаем библиотеку")
        threading.Thread(target=self._fetch_library, daemon=True).start()

    # Wishlist feature removed

    def show_artist(self, artist_id, artist_name):
        log.info("Пользователь: открыть исполнителя id=%d '%s'", artist_id, artist_name)
        self._current_view = "artist"
        self._show_loading(f"Загружаем {artist_name}")
        threading.Thread(target=lambda: self._fetch_artist_top(artist_id, artist_name), daemon=True).start()

    def show_related(self, artist_id, artist_name):
        log.info("Пользователь: похожие на id=%d '%s'", artist_id, artist_name)
        self._current_view = "related"
        self._show_loading(f"Загружаем похожих на {artist_name}")
        threading.Thread(target=lambda: self._fetch_related(artist_id), daemon=True).start()

    # ─────────── SEARCH ───────────

    def search(self):
        q = self.search_entry.get().strip()
        if not q:
            log.debug("Поиск: пустой запрос")
            return
        mode = self.search_type_var.get()
        log.info("Поиск: '%s' тип='%s'", q, mode)
        self._show_loading("Поиск...")
        threading.Thread(target=self._fetch_search, args=(q, mode), daemon=True).start()

    # ─────────── FETCH (thread) → RENDER (main thread) ───────────

    def _fetch_search(self, query, mode):
        log.info("Поиск: '%s' режим='%s'", query, mode)
        self.after(0, self._show_loading)
        if mode == "Альбомы":
            items = logic.search_albums(query)
        elif mode == "Исполнители":
            items = logic.search_artists(query)
        else:
            items = logic.search_deezer(query)
        log.info("Поиск: получено %d результатов", len(items))
        logic.preload_images(items)
        self._load_caches()
        self.after(0, self._render_items, items)

    def _fetch_charts(self):
        log.info("Загрузка чартов")
        tracks = logic.get_charts()
        log.info("Чарты: получено %d треков", len(tracks))
        logic.preload_images(tracks)
        self._load_caches()
        self.after(0, self._render_charts, tracks)

    def _fetch_artist_top(self, artist_id, artist_name=None):
        log.info("Загрузка топ треков artist_id=%d", artist_id)
        tracks = logic.get_artist_top(artist_id)
        log.info("Топ треков: получено %d треков", len(tracks))
        logic.preload_images(tracks)
        self._load_caches()
        self.after(0, lambda: self._render_artist_top(tracks, artist_name, artist_id))

    def _fetch_related(self, artist_id):
        log.info("Загрузка похожих artist_id=%d", artist_id)
        artists = logic.get_related_artists(artist_id)
        logic.preload_images(artists)
        self._load_caches()
        self.after(0, self._render_related, artists)

    def _fetch_library(self):
        log.info("Загрузка библиотеки")
        tracks = logic.get_library()
        log.info("Библиотека: %d треков, загрузка обложек", len(tracks))
        img_data = logic.fetch_images_parallel([t[3] for t in tracks])
        log.info("Библиотека: %d обложек загружено", sum(1 for d in img_data if d))
        self._load_caches()
        self.after(0, self._render_library, tracks, img_data)

    # Wishlist feature removed

    def _load_caches(self):
        self._lib_cache = logic.load_all_library()
        # wishlist removed — no wishlist cache

    # ─────────── RENDER (main thread only) ───────────

    # ─────────── RENDER HELPERS ───────────

    def _style_row(self, row, idx, play_cmd=None):
        bg = ("gray85", "gray22") if idx % 2 == 0 else ("gray90", "gray18")
        row.configure(fg_color=bg)
        if play_cmd:
            row.bind("<Double-1>", lambda e, c=play_cmd: c())
        def on_enter(e, c=row.cget("fg_color")):
            row.configure(fg_color=("gray75", "gray28"))
        def on_leave(e, b=bg):
            row.configure(fg_color=b)
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

    def _render_items(self, items, start=0, batch=5):
        if start == 0:
            self._hide_loading()
            log.info("Рендер результатов: %d элементов", len(items))
        end = min(start + batch, len(items))
        for i in range(start, end):
            item = items[i]
            t = item.get("_type")
            if t == "album":
                self._row_album(item, i)
            elif t == "artist":
                self._row_artist(item, i)
            else:
                self._row_track(item, i)
        if end < len(items):
            self.after(15, lambda: self._render_items(items, end, batch))
        else:
            log.info("Рендер результатов завершён")

    def _row_album(self, album, idx=0):
        ctk_img = self._img_from_data(album.get("_img_data"), (ROW_IMG_SIZE, ROW_IMG_SIZE))
        row = ctk.CTkFrame(self.content_frame)
        row.pack(fill="x", pady=1)
        self._style_row(row, idx)
        if ctk_img:
            ctk.CTkLabel(row, image=ctk_img, text="").pack(side="left", padx=5)
        ctk.CTkLabel(row, text=f"{album['artist']} — {album['title']}  ({album['tracks_count']} тр.)",
                     font=("Arial", 13), anchor="w").pack(side="left", padx=10, fill="x", expand=True)

    def _row_artist(self, artist, idx=0):
        ctk_img = self._img_from_data(artist.get("_img_data"), (ROW_IMG_SIZE, ROW_IMG_SIZE))
        row = ctk.CTkFrame(self.content_frame)
        row.pack(fill="x", pady=1)
        self._style_row(row, idx)
        if ctk_img:
            ctk.CTkLabel(row, image=ctk_img, text="").pack(side="left", padx=5)
        ctk.CTkLabel(row, text=f"{artist['name']}  —  {artist['nb_fans']:,} фанатов",
                     font=("Arial", 13), anchor="w").pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(row, text="Топ треков", width=80,
                      command=lambda aid=artist["id"], an=artist["name"]: self.show_artist(aid, an)
                      ).pack(side="right", padx=5)

    def _row_track(self, track, idx=0):
        title = track["title"]
        artist_name = track["artist"]["name"]
        artist_id = track["artist"]["id"]
        art_url = track["album"]["cover_medium"] or track["album"]["cover_small"]
        preview_url = track.get("preview")
        deezer_id = track["id"]

        ctk_img = self._img_from_data(track.get("_img_data"), (ROW_IMG_SIZE, ROW_IMG_SIZE))

        row = ctk.CTkFrame(self.content_frame)
        row.pack(fill="x", pady=1)
        self._style_row(row, idx,
                         lambda u=preview_url, t=title, a=artist_name, ar=art_url:
                         self.play_preview(u, t, a, ar) if u else None)
        row.bind("<Button-3>",
                 lambda e, a=artist_name, t=title, u=art_url, p=preview_url, d=deezer_id, ai=artist_id:
                 self._context_menu(e, artist=a, title=t, art_url=u, preview_url=p, deezer_id=d, artist_id=ai))

        if ctk_img:
            ctk.CTkLabel(row, image=ctk_img, text="").pack(side="left", padx=5)

        ctk.CTkLabel(row, text=f"{artist_name} — {title}", font=("Arial", 13), anchor="w").pack(side="left", padx=5, fill="x", expand=True)

        bf = ctk.CTkFrame(row, fg_color="transparent")
        bf.pack(side="right", padx=5)

        if preview_url:
            ctk.CTkButton(bf, text="▶", width=32,
                          command=lambda u=preview_url, t=title, a=artist_name, ar=art_url:
                          self.play_preview(u, t, a, ar)
                          ).pack(side="left", padx=1)
        # wishlist removed — no star button

        lib_key = (artist_name.lower(), title.lower())
        in_lib = (self._lib_cache.get(lib_key) if hasattr(self, '_lib_cache') else None) or logic.is_in_library(artist_name, title)
        if in_lib:
            ctk.CTkLabel(bf, text="MP3", font=("Arial", 10, "bold"),
                         text_color=("green", "#4CAF50")).pack(side="left", padx=(0, 4))
        ctk.CTkButton(bf, text="⬇", width=32,
                      command=lambda a=artist_name, t=title, u=art_url: self.start_download(a, t, u)
                      ).pack(side="left", padx=1)
        ctk.CTkButton(bf, text="i", width=32,
                      command=lambda aid=artist_id, an=artist_name: self.show_artist(aid, an)
                      ).pack(side="left", padx=1)

    def _render_charts(self, tracks, start=0, batch=5):
        if start == 0:
            self._hide_loading()
            log.info("Рендер чартов: %d треков", len(tracks))
        end = min(start + batch, len(tracks))
        for idx in range(start, end):
            track = tracks[idx]
            i = idx + 1
            art_url = track["album"]["cover_medium"] or track["album"]["cover_small"]

            ctk_img = self._img_from_data(track.get("_img_data"), (ROW_IMG_SIZE, ROW_IMG_SIZE))

            title = track["title"]
            artist_name = track["artist"]["name"]
            artist_id = track["artist"]["id"]
            preview_url = track.get("preview")
            deezer_id = track["id"]

            row = ctk.CTkFrame(self.content_frame)
            row.pack(fill="x", pady=1)
            self._style_row(row, idx,
                             lambda u=preview_url, t=title, a=artist_name, ar=art_url:
                             self.play_preview(u, t, a, ar) if u else None)
            row.bind("<Button-3>",
                     lambda e, a=artist_name, t=title, u=art_url, p=preview_url, d=deezer_id, ai=artist_id:
                     self._context_menu(e, artist=a, title=t, art_url=u, preview_url=p, deezer_id=d, artist_id=ai))

            ctk.CTkLabel(row, text=f"#{i}", width=25, font=("Arial", 12, "bold")).pack(side="left")
            if ctk_img:
                ctk.CTkLabel(row, image=ctk_img, text="").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{artist_name} — {title}", font=("Arial", 13), anchor="w").pack(side="left", padx=5, fill="x", expand=True)

            bf = ctk.CTkFrame(row, fg_color="transparent")
            bf.pack(side="right", padx=5)

            if preview_url:
                ctk.CTkButton(bf, text="▶", width=32,
                              command=lambda u=preview_url, t=title, a=artist_name, ar=art_url:
                              self.play_preview(u, t, a, ar)
                              ).pack(side="left", padx=1)
            # wishlist removed
            lib_key = (artist_name.lower(), title.lower())
            if (self._lib_cache.get(lib_key) if hasattr(self, '_lib_cache') else None) or logic.is_in_library(artist_name, title):
                ctk.CTkLabel(bf, text="MP3", font=("Arial", 10, "bold"),
                             text_color=("green", "#4CAF50")).pack(side="left", padx=(0, 4))
            ctk.CTkButton(bf, text="⬇", width=32,
                          command=lambda a=artist_name, t=title, u=art_url: self.start_download(a, t, u)
                          ).pack(side="left", padx=1)
            ctk.CTkButton(bf, text="i", width=32,
                          command=lambda aid=artist_id, an=artist_name: self.show_artist(aid, an)
                          ).pack(side="left", padx=1)
        if end < len(tracks):
            self.after(15, lambda: self._render_charts(tracks, end, batch))
        else:
            log.info("Рендер чартов завершён")

    def _render_artist_top(self, tracks, artist_name=None, artist_id=None, start=0, batch=5):
        if start == 0:
            self._hide_loading()
            self._clear()
            log.info("Рендер треков исполнителя '%s': %d треков", artist_name, len(tracks))
            if artist_name:
                ctk.CTkLabel(self.content_frame, text=artist_name,
                             font=("Arial", 20, "bold")).pack(pady=(5, 0))
            ctk.CTkLabel(self.content_frame, text="Популярные треки",
                         font=("Arial", 13), text_color="gray").pack(pady=(0, 5))

            btns = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            btns.pack(pady=(0, 10))
            ctk.CTkButton(btns, text="← Назад", width=80, command=self.show_charts).pack(side="left", padx=5)
            if artist_id:
                ctk.CTkButton(btns, text="Похожие", width=90,
                              command=lambda: self.show_related(artist_id, artist_name or "")
                              ).pack(side="left", padx=5)

        end = min(start + batch, len(tracks))
        for idx in range(start, end):
            track = tracks[idx]
            art_url = track["album"]["cover_medium"] or track["album"]["cover_small"]

            ctk_img = self._img_from_data(track.get("_img_data"), (ROW_IMG_SIZE, ROW_IMG_SIZE))
            title = track["title"]
            artist_name_t = track["artist"]["name"]
            artist_id_t = track["artist"]["id"]
            preview_url = track.get("preview")
            deezer_id = track["id"]

            row = ctk.CTkFrame(self.content_frame)
            row.pack(fill="x", pady=1)
            self._style_row(row, idx,
                             lambda u=preview_url, t=title, a=artist_name_t, ar=art_url:
                             self.play_preview(u, t, a, ar) if u else None)
            row.bind("<Button-3>",
                     lambda e, a=artist_name_t, t=title, u=art_url, p=preview_url, d=deezer_id, ai=artist_id_t:
                     self._context_menu(e, artist=a, title=t, art_url=u, preview_url=p, deezer_id=d, artist_id=ai))
            if ctk_img:
                ctk.CTkLabel(row, image=ctk_img, text="").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{artist_name_t} — {title}", font=("Arial", 13), anchor="w").pack(side="left", padx=5, fill="x", expand=True)

            bf = ctk.CTkFrame(row, fg_color="transparent")
            bf.pack(side="right", padx=5)

            if preview_url:
                ctk.CTkButton(bf, text="▶", width=32,
                              command=lambda u=preview_url, t=title, a=artist_name_t, ar=art_url:
                              self.play_preview(u, t, a, ar)
                              ).pack(side="left", padx=1)
            # wishlist removed
            lib_key = (artist_name_t.lower(), title.lower())
            if (self._lib_cache.get(lib_key) if hasattr(self, '_lib_cache') else None) or logic.is_in_library(artist_name_t, title):
                ctk.CTkLabel(bf, text="MP3", font=("Arial", 10, "bold"),
                             text_color=("green", "#4CAF50")).pack(side="left", padx=(0, 4))
            ctk.CTkButton(bf, text="⬇", width=32,
                          command=lambda a=artist_name_t, t=title, u=art_url: self.start_download(a, t, u)
                          ).pack(side="left", padx=1)
        if end < len(tracks):
            self.after(15, lambda: self._render_artist_top(tracks, artist_name, artist_id, end, batch))
        else:
            log.info("Рендер треков исполнителя завершён")

    def _render_related(self, artists, start=0, batch=5):
        if start == 0:
            self._hide_loading()
            log.info("Рендер похожих: %d исполнителей", len(artists))
        end = min(start + batch, len(artists))
        for idx in range(start, end):
            a = artists[idx]
            ctk_img = self._img_from_data(a.get("_img_data"), (ROW_IMG_SIZE, ROW_IMG_SIZE))
            row = ctk.CTkFrame(self.content_frame)
            row.pack(fill="x", pady=2)
            if ctk_img:
                ctk.CTkLabel(row, image=ctk_img, text="").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=a["name"], font=("Arial", 13), anchor="w").pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkButton(row, text="Топ треков", width=80,
                          command=lambda aid=a["id"], an=a["name"]: self.show_artist(aid, an)
                          ).pack(side="right", padx=5)
        if end < len(artists):
            self.after(15, lambda: self._render_related(artists, end, batch))

    # ─────────── LIBRARY ───────────

    def _render_library(self, tracks, img_data, start=0, batch=5):
        if start == 0:
            self._hide_loading()
        end = min(start + batch, len(tracks))
        for idx in range(start, end):
            t = tracks[idx]
            img_d = img_data[idx]
            row = ctk.CTkFrame(self.content_frame)
            row.pack(fill="x", pady=1)
            self._style_row(row, idx,
                             lambda p=t[4], n=f"{t[2]} — {t[1]}", u=t[3]:
                             self.play_music(p, n, u))
            row.bind("<Button-3>",
                     lambda e, a=t[2], ttl=t[1], u=t[3], fp=t[4], tid=t[0]:
                     self._context_menu(e, artist=a, title=ttl, art_url=u, file_path=fp, track_id=tid))

            ctk_img = self._img_from_data(img_d, (ROW_IMG_SIZE, ROW_IMG_SIZE))
            if ctk_img:
                ctk.CTkLabel(row, image=ctk_img, text="").pack(side="left", padx=5)

            ctk.CTkLabel(row, text=f"{t[2]} — {t[1]}", font=("Arial", 13), anchor="w").pack(side="left", padx=10, fill="x", expand=True)

            bf = ctk.CTkFrame(row, fg_color="transparent")
            bf.pack(side="right", padx=5)

            ctk.CTkButton(bf, text="▶", width=32,
                          command=lambda p=t[4], n=f"{t[2]} — {t[1]}", u=t[3]: self.play_music(p, n, u)
                          ).pack(side="left", padx=1)
            ctk.CTkLabel(bf, text="MP3", font=("Arial", 10, "bold"),
                         text_color=("green", "#4CAF50")).pack(side="left", padx=(0, 4))
            ctk.CTkButton(bf, text="🗑", width=32,
                          command=lambda tid=t[0]: self.delete_track(tid)).pack(side="left", padx=2)
        if end < len(tracks):
            self.after(15, lambda: self._render_library(tracks, img_data, end, batch))
        else:
            log.info("Рендер библиотеки завершён")

    def delete_track(self, track_id):
        logic.delete_from_db(track_id)
        self.show_library()

    # ─────────── WISHLIST ───────────

    # Wishlist rendering removed

    # Wishlist actions removed

    # ─────────── PLAYBACK ───────────

    def play_preview(self, url, title, artist, art_url):
        log.info("Воспроизведение preview: '%s — %s'", artist, title)
        path = logic.download_preview(url)
        if not path:
            log.error("Preview: файл не загружен")
            self.current_meta_label.configure(text="❌ Preview недоступен")
            self.after(3000, lambda: self.current_meta_label.configure(text=""))
            return
        self.current_duration = 30
        self.current_path = path
        self.current_name = f"{artist} — {title}"
        self.current_art_url = art_url
        try:
            mixer.music.load(path)
            mixer.music.play()
        except Exception as e:
            log.error("Ошибка preview: %s", e, exc_info=True)
            return
        self._update_player_art(art_url)
        self.current_track_label.configure(text=f"{artist} — {title}")
        self.current_meta_label.configure(text="Превью 30 с")
        self.seek_var.set(0)
        self.current_seek_start = 0
        self._is_playing = True
        self._is_paused = False
        self._update_play_pause_btn()
        log.info("Preview воспроизводится: '%s'", path)

    def play_full(self, artist, title, art_url):
        log.info("Полное воспроизведение: '%s — %s'", artist, title)
        t = threading.Thread(target=self._do_play_full, args=(artist, title, art_url), daemon=True)
        t.start()

    def _do_play_full(self, artist, title, art_url):
        path = logic.download_track(artist, title, art_url)
        if not path:
            log.error("Не удалось загрузить трек: '%s — %s'", artist, title)
            self.after(0, lambda: self.current_meta_label.configure(text="❌ Не удалось загрузить трек"))
            return
        log.info("Полное воспроизведение: файл '%s'", path)
        self.after(0, lambda: self._start_playback(path, f"{artist} — {title}", art_url))

    def _start_playback(self, path, name, art_url):
        log.info("Старт воспроизведения: '%s'", name)
        self.current_path = path
        self.current_name = name
        self.current_art_url = art_url
        self.current_duration = 0

        if HAS_MUTAGEN:
            try:
                self.current_duration = MutagenFile(path).info.length
                log.info("Длительность трека: %.1f сек", self.current_duration)
            except Exception as e:
                log.warning("Не удалось прочитать длительность: %s", e)

        try:
            mixer.music.load(path)
            mixer.music.play()
        except Exception as e:
            log.error("Ошибка воспроизведения: %s", e, exc_info=True)
            return

        self.current_track_label.configure(text=name)
        self.current_meta_label.configure(text="")
        self.seek_var.set(0)
        self.current_seek_start = 0
        self._update_player_art(art_url)
        self._is_playing = True
        self._is_paused = False
        self._update_play_pause_btn()
        log.info("Воспроизведение начато: '%s'", name)

    def play_music(self, path, name, art_url=None):
        log.info("Воспроизведение файла: '%s'", name)
        if not os.path.exists(path):
            log.error("Файл не найден: %s", path)
            return
        self.current_path = path
        self.current_name = name
        self.current_art_url = art_url
        self.current_duration = 0

        if HAS_MUTAGEN:
            try:
                self.current_duration = MutagenFile(path).info.length
                log.info("Длительность: %.1f сек", self.current_duration)
            except Exception as e:
                log.warning("Не удалось прочитать длительность: %s", e)

        try:
            mixer.music.load(path)
            mixer.music.play()
        except Exception as e:
            log.error("Ошибка воспроизведения: %s", e, exc_info=True)
            return

        self.current_track_label.configure(text=name)
        self.current_meta_label.configure(text="")
        self.seek_slider.configure(state="normal")
        self.seek_var.set(0)
        self.current_seek_start = 0
        self._update_player_art(art_url)
        self._is_playing = True
        self._is_paused = False
        self._update_play_pause_btn()
        log.info("Файл воспроизводится: '%s'", name)

    def _update_player_art(self, url):
        self.current_art_url = url
        if not url:
            self._clear_player_art()
            return
        threading.Thread(target=self._load_art, args=(url,), daemon=True).start()

    def _clear_player_art(self):
        old_img = self._player_ctk_image
        self._player_ctk_image = None
        self.player_art_label.configure(image=self._blank_image, text="🎵")

    def _load_art(self, url):
        img = logic.get_image_from_url(url)
        self.after(0, self._apply_art, img, url)

    def _apply_art(self, img, url):
        if self.current_art_url != url:
            return
        if img:
            old_img = self._player_ctk_image
            art = self.player_art_label.winfo_width() or PLAYER_ART_SIZE
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(art, art))
            self._player_ctk_image = ctk_img
            self.player_art_label.configure(image=ctk_img, text="")
            log.debug("Обложка плеера обновлена (%dpx)", art)
        else:
            self._clear_player_art()

    def seek_music(self, value):
        if self._seek_updating or not self._is_playing:
            return
        try:
            pct = float(value) / 100.0
            pos = pct * self.current_duration
            was_paused = self._is_paused
            mixer.music.stop()
            mixer.music.play(start=pos)
            self.current_seek_start = pos
            if was_paused:
                mixer.music.pause()
            log.debug("Seek: %.1f%% -> %.1f сек", pct * 100, pos)
        except Exception as e:
            log.warning("Ошибка seek: %s", e)

    def set_volume(self, value):
        mixer.music.set_volume(float(value))
        log.debug("Громкость: %.2f", float(value))

    def update_seek_bar(self):
        if self._is_playing:
            if mixer.music.get_busy() or self._is_paused:
                pos = self.current_seek_start + mixer.music.get_pos() / 1000.0
                if self.current_duration > 0:
                    pct = min(pos / self.current_duration * 100, 100)
                    self._seek_updating = True
                    self.seek_var.set(pct)
                    self._seek_updating = False
                    self.time_label.configure(
                        text=f"{self._fmt_time(pos)} / {self._fmt_time(self.current_duration)}")
            else:
                self._is_playing = False
                self._is_paused = False
                self._update_play_pause_btn()
                self.current_meta_label.configure(text="")
                self.time_label.configure(text="0:00 / 0:00")
                if self.seek_var.get() != 0:
                    self.seek_var.set(0)
        self.after(1000, self.update_seek_bar)

    @staticmethod
    def _fmt_time(sec):
        m = int(sec // 60)
        s = int(sec % 60)
        return f"{m}:{s:02d}"

    # ─────────── DOWNLOAD ───────────

    def start_download(self, artist, title, img_url):
        log.info("Запуск загрузки: '%s — %s'", artist, title)
        key = (artist, title)
        if key in self._dl_labels:
            return
        frame = ctk.CTkFrame(self._dl_scroll, fg_color="transparent")
        frame.pack(fill="x", pady=1)
        icon = ctk.CTkLabel(frame, text="⬇", font=("Arial", 11), width=16)
        icon.pack(side="left")
        label = ctk.CTkLabel(frame, text=f"{artist[:15]} — {title[:20]}",
                             font=("Arial", 10), anchor="w")
        label.pack(side="left", fill="x", expand=True)
        status = ctk.CTkLabel(frame, text="...", font=("Arial", 8),
                              text_color="gray", width=24)
        status.pack(side="right")
        self._dl_labels[key] = (frame, icon, label, status)
        threading.Thread(target=self.do_download, args=(artist, title, img_url, key), daemon=True).start()

    def do_download(self, artist, title, img_url, key):
        log.info("Загрузка: '%s — %s'", artist, title)
        file_path = logic.download_track(artist, title, img_url)
        if file_path:
            logic.save_to_db(title, artist, img_url, file_path)
            self.after(0, lambda k=key: self._set_dl_status(k, "✅", "Готово"))
            if self._current_view == "library":
                self.after(500, self.show_library)
        else:
            self.after(0, lambda k=key: self._set_dl_status(k, "❌", "Ошибка"))
            log.error("Не удалось скачать '%s — %s'", artist, title)

    def _set_dl_status(self, key, icon_text, status_text=""):
        if key not in self._dl_labels:
            return
        frame, icon, label, status = self._dl_labels[key]
        icon.configure(text=icon_text)
        status.configure(text=status_text)

    def _remove_dl(self, key):
        if key not in self._dl_labels:
            return
        frame, icon, label, status = self._dl_labels[key]
        frame.destroy()
        del self._dl_labels[key]

    def _clear_done_dls(self):
        done_icons = {"✅", "❌"}
        for key in list(self._dl_labels.keys()):
            _, icon, _, _ = self._dl_labels[key]
            if icon.cget("text") in done_icons:
                self._remove_dl(key)


if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()

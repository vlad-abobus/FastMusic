import sqlite3
import requests
import os
import sys
import shutil
import tempfile
import concurrent.futures
from PIL import Image
from io import BytesIO
from deezer_client import DeezerClient
from logger import get_logger

log = get_logger(__name__)

_client = DeezerClient()
_PREVIEW_DIR = os.path.join(tempfile.gettempdir(), "FastMusicPreviews")
os.makedirs(_PREVIEW_DIR, exist_ok=True)


def _get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


_BASE_DIR = _get_base_dir()
_DOWNLOADS_DIR = os.path.join(_BASE_DIR, "downloads")
_DB_PATH = os.path.join(_BASE_DIR, "music_library.db")

# ---- Database ----

def init_db():
    log.info("Инициализация БД")
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tracks
                 (id INTEGER PRIMARY KEY, title TEXT, artist TEXT,
                  album_art TEXT, file_path TEXT)''')
    # wishlist table removed
    conn.commit()
    conn.close()
    log.info("БД инициализирована")

# ---- Library (downloaded tracks) ----

def save_to_db(title, artist, album_art, file_path):
    log.info("Сохранение в библиотеку: '%s — %s' file=%s", artist, title, file_path)
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO tracks (title, artist, album_art, file_path) VALUES (?, ?, ?, ?)",
              (title, artist, album_art, file_path))
    conn.commit()
    conn.close()
    log.info("Трек сохранён в БД")

def delete_from_db(track_id):
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT file_path FROM tracks WHERE id = ?", (track_id,))
    row = c.fetchone()
    if row:
        fp = row[0]
        if os.path.isfile(fp):
            try:
                os.remove(fp)
                log.info("Файл удалён: %s", fp)
            except PermissionError:
                log.warning("Файл занят (воспроизводится?), пропускаем: %s", fp)
    c.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    conn.commit()
    conn.close()
    log.info("Трек id=%d удалён", track_id)

def get_library():
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM tracks")
    rows = list(c.fetchall())
    conn.close()

    # чиним пути: если файл не совпадает по имени с артистом/тайтлом
    _fix_library_paths(rows)

    # удаляем из результата записи где файл пропал (и чистим БД)
    valid = _clean_missing_tracks(rows)

    # заполняем обложки для треков у которых их нет
    _fill_missing_art(valid)

    folder_rows = _scan_and_import_folder(valid)

    # объединяем и убираем дубликаты по file_path
    seen_paths = set()
    result = []
    for r in valid + folder_rows:
        fp = r[4] if len(r) >= 5 else None
        if fp and fp in seen_paths:
            continue
        if fp:
            seen_paths.add(fp)
        result.append(r)

    log.info("Загрузка библиотеки: %d треков (БД %d + из папки %d, дублей убрано)", len(result), len(valid), len(folder_rows))
    return result

def _clean_missing_tracks(rows):
    valid = []
    to_delete = []
    for r in rows:
        if len(r) >= 5 and os.path.isfile(r[4]):
            valid.append(r)
        else:
            tid = r[0] if r else None
            if tid is not None:
                to_delete.append(tid)
    if to_delete:
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        c.executemany("DELETE FROM tracks WHERE id = ?", [(tid,) for tid in to_delete])
        conn.commit()
        conn.close()
        log.info("Библиотека: удалено %d записей (файл не найден)", len(to_delete))
    return valid

def _fix_library_paths(rows):
    fixed = 0
    for i, r in enumerate(rows):
        if len(r) < 5:
            continue
        tid, title, artist, art, fpath = r[:5]
        safe_artist = "".join(c for c in artist if c.isalnum() or c in " _-").strip()
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip()
        expected = os.path.join(_DOWNLOADS_DIR, f"{safe_artist} - {safe_title}.mp3")
        if os.path.isfile(expected) and fpath != expected:
            conn = sqlite3.connect(_DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE tracks SET file_path = ? WHERE id = ?", (expected, tid))
            conn.commit()
            conn.close()
            rows[i] = (tid, title, artist, art, expected) + r[5:]
            fixed += 1
            log.info("Путь исправлен: id=%d '%s' → %s", tid, title, expected)
    if fixed:
        log.info("Исправлено путей: %d", fixed)

def _fill_missing_art(rows):
    updated = 0
    for i, r in enumerate(rows):
        if len(r) < 5:
            continue
        tid, title, artist, art, fpath = r[:5]
        if art:
            continue
        url = _find_album_art(artist, title)
        if url:
            conn = sqlite3.connect(_DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE tracks SET album_art = ? WHERE id = ?", (url, tid))
            conn.commit()
            conn.close()
            rows[i] = (tid, title, artist, url, fpath) + r[5:]
            updated += 1
    if updated:
        log.info("Обложки добавлены: %d треков", updated)

import re as _re

_STOP = {"feat", "ft", "featuring", "the", "a", "an", "of", "and", "to", "in", "on",
         "for", "with", "vs", "live", "edit", "radio", "version", "mix", "remix",
         "extended", "explicit", "clean", "remastered", "remaster", "deluxe"}

def _title_tokens(s):
    s = _re.sub(r'[\(\)\[\]\{\}\,\.\-\–\—\'\"]', ' ', s.lower())
    return {w for w in s.split() if w not in _STOP and len(w) >= 2}

def _title_similarity(t1, t2):
    a = _title_tokens(t1)
    b = _title_tokens(t2)
    if not a or not b:
        return 0
    return len(a & b) / min(len(a), len(b))

def _find_album_art(artist, title):
    try:
        # убираем .mp3 из запроса (бывает после кривого расширения)
        clean_artist = artist
        clean_title = title
        while clean_artist.lower().endswith(".mp3"):
            clean_artist = clean_artist[:-4]
        while clean_title.lower().endswith(".mp3"):
            clean_title = clean_title[:-4]
        results = _client.search_tracks(f"{clean_artist} {clean_title}")
        if results:
            album = results[0].get("album") or {}
            return album.get("cover_medium") or album.get("cover_small") or ""
    except Exception:
        pass
    return ""

def _scan_and_import_folder(existing_rows):
    folder = _DOWNLOADS_DIR
    if not os.path.isdir(folder):
        return []
    # existing: {(artist_lower, title_lower)} + {(artist_lower, title_tokens_set)}
    existing = set()
    for r in existing_rows:
        if len(r) < 3:
            continue
        existing.add((r[2].lower(), r[1].lower()))
    new_items = []
    for f in os.listdir(folder):
        if not f.endswith(".mp3"):
            continue
        fpath = os.path.join(folder, f)
        if os.path.getsize(fpath) < 10000:
            continue
        try:
            from mutagen import File as MFile
            mf = MFile(fpath)
            if mf is None or not hasattr(mf, 'info') or getattr(mf.info, 'length', 0) < 1:
                log.debug("Пропущен битый mp3: %s", f)
                continue
        except Exception:
            log.debug("Пропущен неподдерживаемый файл: %s", f)
            continue
        name = f
        while name.lower().endswith(".mp3"):
            name = name[:-4]
        artist, title = _parse_filename(name)
        if not title:
            title = name
        if not artist:
            artist = "Неизвестно"
        key = (artist.lower(), title.lower())
        if key in existing:
            continue
        # dedup: такой же артист + похожий тайтл → пропускаем
        is_dup = False
        for ea, et in existing:
            if ea == artist.lower() and _title_similarity(title, et) > 0.5:
                is_dup = True
                break
        if is_dup:
            log.info("Пропущен дубликат: '%s — %s'", artist, title)
            existing.add(key)
            continue
        art_url = _find_album_art(artist, title)
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO tracks (title, artist, album_art, file_path) VALUES (?, ?, ?, ?)",
                  (title, artist, art_url, fpath))
        conn.commit()
        new_id = c.lastrowid
        conn.close()
        new_items.append((new_id, title, artist, art_url, fpath))
        existing.add(key)
        log.info("Авто-импорт: '%s — %s' art=%s", artist, title, art_url[:40] if art_url else "нет")
    return new_items

def _parse_filename(name):
    # "Artist - Title" → ("Artist", "Title")
    # "Artist – Title" → ("Artist", "Title")
    # "Artist - Title (feat. ...)" → ("Artist", "Title (feat. ...)")
    m = _re.match(r'^(.+?)\s*[–\-—]\s*(.+)$', name)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # если нет дефиса — считаем всю строку тайтлом
    return None, name.strip()

# Wishlist feature removed (functions and table deleted)

def is_in_library(artist, title):
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, file_path FROM tracks WHERE artist=? AND title=?", (artist, title))
    row = c.fetchone()
    conn.close()
    return row if row else None

def load_all_library():
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT artist, title, file_path FROM tracks")
    lib = {}
    for row in c.fetchall():
        lib[(row[0].lower(), row[1].lower())] = row[2]
    conn.close()
    return lib

# Wishlist helper functions removed


def search_local_by_artist(query):
    """Search local library and downloads for tracks matching artist name.

    Returns list of tuples like DB rows: (id, title, artist, album_art, file_path)
    """
    q = (query or "").lower().strip()
    if not q:
        return []

    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM tracks WHERE LOWER(artist) LIKE ? ORDER BY id DESC", (f"%{q}%,",))
    rows = c.fetchall()
    conn.close()

    # dedupe by file path
    seen = set()
    result = []
    for r in rows:
        if len(r) >= 5 and r[4]:
            seen.add(r[4])
        result.append(r)

    # also scan downloads folder for matching filenames
    if os.path.isdir(_DOWNLOADS_DIR):
        for f in os.listdir(_DOWNLOADS_DIR):
            if not f.lower().endswith('.mp3'):
                continue
            fpath = os.path.join(_DOWNLOADS_DIR, f)
            try:
                if os.path.getsize(fpath) < 10000:
                    continue
            except Exception:
                continue
            name = f
            while name.lower().endswith('.mp3'):
                name = name[:-4]
            artist_parsed, title_parsed = _parse_filename(name)
            if artist_parsed and q in artist_parsed.lower():
                if fpath in seen:
                    continue
                # try to find DB entry for this file
                conn = sqlite3.connect(_DB_PATH)
                c = conn.cursor()
                c.execute("SELECT id, title, artist, album_art, file_path FROM tracks WHERE file_path = ?", (fpath,))
                row = c.fetchone()
                conn.close()
                if row:
                    result.append(row)
                    seen.add(fpath)
                else:
                    art = _find_album_art(artist_parsed, title_parsed)
                    result.append((None, title_parsed, artist_parsed, art, fpath))
                    seen.add(fpath)

    return result

# ---- Download (yt-dlp) ----

def _find_ffmpeg():
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        c = os.path.join(exe_dir, "ffmpeg.exe")
        if os.path.isfile(c):
            return c
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            c = os.path.join(meipass, "ffmpeg.exe")
            if os.path.isfile(c):
                return c
    path = shutil.which("ffmpeg")
    if path:
        return path
    for d in [_BASE_DIR, os.getcwd()]:
        c = os.path.join(d, "ffmpeg.exe")
        if os.path.isfile(c):
            return c
    return None


def _generate_queries(artist, title):
    queries = [f"{artist} - {title}"]
    import re as _re
    clean = _re.sub(r'\([^)]*\)', '', title).strip()
    clean = _re.sub(r'\[[^\]]*\]', '', clean).strip()
    clean = _re.split(r'\s+(?:feat|ft|featuring)\s+', clean, flags=_re.IGNORECASE)[0].strip()
    if clean and clean != title:
        queries.append(f"{artist} - {clean}")
    if len(title) > 30:
        short = title[:30].rsplit(" ", 1)[0] if " " in title[:30] else title[:30]
        queries.append(f"{artist} - {short}")
    words = title.split()
    if len(words) > 3:
        queries.append(f"{artist} - {' '.join(words[:3])}")
    seen = set()
    return [q for q in queries if not (q.lower() in seen or seen.add(q.lower()))]


def _clean_double_ext(folder):
    for f in os.listdir(folder):
        if f.endswith(".mp3.mp3"):
            old = os.path.join(folder, f)
            new = os.path.join(folder, f[:-4])
            try:
                os.rename(old, new)
                log.info("Переименован битый файл: %s → %s", old, new)
            except Exception:
                pass

def download_track(artist, title, img_url=None):
    import yt_dlp

    folder = _DOWNLOADS_DIR
    os.makedirs(folder, exist_ok=True)

    _clean_double_ext(folder)

    safe_artist = "".join(c for c in artist if c.isalnum() or c in " _-").strip()
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    expected_path = os.path.join(folder, f"{safe_artist} - {safe_title}.mp3")

    if os.path.isfile(expected_path) and os.path.getsize(expected_path) > 10000:
        log.info("Файл уже скачан: %s", expected_path)
        return expected_path

    ffmpeg_path = _find_ffmpeg()
    if not ffmpeg_path:
        log.error("ffmpeg не найден — конвертация в mp3 недоступна")
        return None

    queries = _generate_queries(artist, title)
    log.info("Загрузка через yt-dlp: пробуем %d вариантов запроса", len(queries))

    for i, query in enumerate(queries):
        log.info("Поиск %d/%d: '%s'", i + 1, len(queries), query)
        outtmpl = os.path.join(folder, f"{safe_artist} - {safe_title}.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'ffmpeg_location': ffmpeg_path,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'playlist_items': '1',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(query, download=True)
        except Exception as e:
            log.warning("yt-dlp ошибка на запросе '%s': %s", query, e)
            if os.path.isfile(expected_path) and os.path.getsize(expected_path) > 10000:
                log.info("Файл найден после запроса '%s': %s", query, expected_path)
                return _tag_file(expected_path, artist, title, img_url)
            continue

        if os.path.isfile(expected_path) and os.path.getsize(expected_path) > 10000:
            log.info("yt-dlp скачал по запросу '%s': %s", query, expected_path)
            return _tag_file(expected_path, artist, title, img_url)

    log.error("yt-dlp не смог скачать '%s — %s'", artist, title)
    return None


def _tag_file(file_path, artist, title, img_url=None):
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, TIT2, TPE1, APIC
        audio = MP3(file_path)
        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist))
        if img_url:
            try:
                resp = requests.get(img_url, timeout=5)
                if resp.status_code == 200:
                    mime = resp.headers.get("Content-Type", "image/jpeg")
                    audio.tags.add(APIC(encoding=3, mime=mime, type=3, desc='Cover', data=resp.content))
            except Exception:
                pass
        audio.save()
        log.info("Теги записаны: %s", file_path)
    except Exception as e:
        log.warning("Не удалось записать теги: %s", e)
    return file_path


def _find_file(folder, artist, title, fallback=False):
    if not os.path.isdir(folder):
        return None
    import re
    artist_lower = artist.lower().strip()
    title_lower = title.lower().strip()

    # --- слова для точного совпадения ---
    stopwords = {"feat", "ft", "featuring", "the", "a", "an", "of", "and", "to", "in", "on", "for", "with", "vs", "live", "edit", "radio", "version", "mix", "remix", "extended", "explicit", "clean"}
    query_words = set()
    for t in [artist_lower, title_lower]:
        for w in re.split(r'[\s\(\)\[\]\-\–\|\,\/\.\_]+', t):
            w = w.strip().strip("'\"")
            if w and len(w) >= 3 and w not in stopwords:
                query_words.add(w)

    # --- подстроки для нечёткого поиска ---
    # значимые части: полный артист, полный тайтл, части до/после скобок и дефисов
    raw = set()
    raw.add(artist_lower)
    raw.add(title_lower)
    for sep in [r'\(', r'\)', r'\[', r'\]', r'\-', r'\–', r'\/', r'\,' , r'\.', r'\&', r'feat\.', r'ft\.']:
        parts = re.split(sep, title_lower)
        raw.update(p.strip() for p in parts)
    # убираем слишком короткие и стоп-слова
    substrs = {p for p in raw if len(p) >= 5 and p not in stopwords}

    best = None
    best_score = -1
    best_fallback = None
    best_fallback_mtime = 0
    for root, dirs, files in os.walk(folder):
        for f in files:
            if not f.endswith(".mp3"):
                continue
            fpath = os.path.join(root, f)
            if os.path.getsize(fpath) < 10000:
                continue

            # убираем .mp3 из имени для сравнения
            clean_name = f
            while clean_name.lower().endswith(".mp3"):
                clean_name = clean_name[:-4]

            f_lower = clean_name.lower()
            f_words = set(re.split(r'[\s\(\)\[\]\-\–\|\,\/\.\_\']+', f_lower))
            f_stripped = re.sub(r'[\s\(\)\[\]\-\–\|\,\/\.\_\'"]', '', f_lower)

            # 1) совпадение по словам: каждое слово из запроса = +2, артист = +4
            word_score = 0
            for qw in query_words:
                if qw in f_words:
                    word_score += 2
                    if qw in artist_lower:
                        word_score += 2
                # если слово слитно (DaftPunk) — ищем подстроку
                elif len(qw) >= 4 and qw in f_stripped:
                    word_score += 1

            # 2) совпадение кусочков: каждое вхождение = +3
            substr_score = sum(3 for s in substrs if s in f_lower)

            # 3) бонус артист целиком
            artist_bonus = 5 if artist_lower in f_lower else 0

            score = word_score + substr_score + artist_bonus
            if score > 0:
                log.debug("_find_file: '%s' word=%d substr=%d artist=%d total=%d", f, word_score, substr_score, artist_bonus, score)

            if score > best_score:
                best_score = score
                best = fpath

            mt = os.path.getmtime(fpath)
            if mt > best_fallback_mtime:
                best_fallback_mtime = mt
                best_fallback = fpath

    if best and best_score >= 3:
        return best
    if fallback:
        return best_fallback
    return None

# ---- Preview playback ----

def download_preview(url):
    if not url:
        log.warning("download_preview: пустой URL")
        return None
    fname = os.path.join(_PREVIEW_DIR, f"preview_{hash(url)}.mp3")
    if os.path.exists(fname):
        log.debug("preview уже кэширован: %s", fname)
        return fname
    log.info("Загрузка preview: url=%s", url[:80])
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.status_code != 200:
            log.warning("preview: HTTP %d для url=%s", resp.status_code, url[:80])
            return None
        ct = resp.headers.get("Content-Type", "") or ""
        if "audio" not in ct and "octet-stream" not in ct and len(resp.content) < 1000:
            log.warning("preview: неожиданный Content-Type=%s (%d байт)", ct, len(resp.content))
            return None
        with open(fname, "wb") as f:
            f.write(resp.content)
        log.info("preview сохранён: %s (%d байт)", fname, len(resp.content))
        return fname
    except Exception as e:
        log.error("Ошибка загрузки preview: %s", e, exc_info=True)
        return None

def clean_preview_cache():
    if os.path.isdir(_PREVIEW_DIR):
        log.info("Очистка кэша preview: %s", _PREVIEW_DIR)
        shutil.rmtree(_PREVIEW_DIR)

# ---- Images ----

def get_image_from_url(url, size=(50, 50)):
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=5)
        img = Image.open(BytesIO(resp.content))
        log.debug("Изображение загружено: %s (%d байт)", url[:60], len(resp.content))
        return img
    except Exception as e:
        log.warning("Не удалось загрузить изображение %s: %s", url[:60], e)
        return None

def image_bytes_from_url(url):
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=5)
        log.debug("Байты изображения: %s (%d байт)", url[:60], len(resp.content))
        return resp.content
    except Exception as e:
        log.warning("Не удалось получить байты изображения %s: %s", url[:60], e)
        return None

def image_from_bytes(data):
    if not data:
        return None
    try:
        img = Image.open(BytesIO(data))
        log.debug("Изображение создано из байт: %sx%s", img.width, img.height)
        return img
    except Exception as e:
        log.warning("Ошибка создания изображения из байт: %s", e)
        return None

def preload_images(items):
    log.info("Предзагрузка изображений: %d элементов", len(items))
    urls = [_get_item_image_url(item) for item in items]
    ok = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = pool.map(image_bytes_from_url, urls)
    for item, data in zip(items, results):
        item["_img_data"] = data
        if data:
            ok += 1
    log.info("Предзагрузка изображений: %d/%d успешно", ok, len(items))
    return items

def fetch_images_parallel(urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(image_bytes_from_url, urls))

def _get_item_image_url(item):
    t = item.get("_type")
    if t == "track":
        album = item.get("album") or {}
        return album.get("cover_medium") or album.get("cover_small")
    elif t == "album":
        return item.get("cover_medium")
    elif t == "artist":
        return item.get("picture_medium")
    album = item.get("album")
    if album:
        return album.get("cover_medium") or album.get("cover_small")
    return item.get("picture_medium") or item.get("cover_medium")

# ---- Deezer API ----

def search_deezer(query):
    log.info("Поиск треков: '%s'", query)
    return _client.search_tracks(query)

def search_all(query):
    log.info("Поиск всего: '%s'", query)
    return _client.search_all(query)

def search_albums(query):
    log.info("Поиск альбомов: '%s'", query)
    return _client.search_albums(query)

def search_artists(query):
    log.info("Поиск исполнителей: '%s'", query)
    return _client.search_artists(query)

def get_charts():
    log.info("Запрос чартов")
    return _client.get_charts()

def get_artist_top(artist_id):
    log.info("Запрос топ треков artist_id=%d", artist_id)
    return _client.get_artist_top(artist_id)

def get_related_artists(artist_id):
    log.info("Запрос похожих исполнителей artist_id=%d", artist_id)
    return _client.get_related_artists(artist_id)

def get_artist_info(artist_id):
    return _client.get_artist(artist_id)

def get_album_info(album_id):
    return _client.get_album(album_id)

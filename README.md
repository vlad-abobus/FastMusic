# FastMusic — музыкальный плеер

**Русский** | [English](README.en.md)

Клон VK Music: поиск треков через Deezer, скачивание, локальная библиотека, чарты и интернет-радио.
Есть две версии — настольное приложение на Python (CustomTkinter) и веб-версия на React + Express.

## Возможности

- Поиск треков, альбомов и исполнителей (Deezer)
- Чарты Deezer и топ-треки исполнителя, похожие исполнители
- Скачивание треков в локальную библиотеку
- Воспроизведение: play / pause, seek, громкость, горячие клавиши
- Интернет-радио (Radio Browser): популярные станции, поиск по названию, тегу, стране
- Обложки альбомов, история загрузок

## Настольное приложение (Python)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py                # или: .\run-dev.ps1
```

Библиотека хранится в SQLite-базе `music_library.db`, логи — в папке `logs/`.

### Сборка .exe

```powershell
.\build-exe.ps1              # с консолью
.\build-exe.ps1 -Windowed    # без консоли
```

Готовый файл: `dist/FastMusic.exe`. Скрипт сам скачивает `ffmpeg.exe`, если его нет.

## Веб-версия (React + Express)

```bash
npm install
npm run dev                  # http://localhost:3000
```

- `npm run build` — сборка фронтенда и сервера в `dist/`
- `npm run lint` — проверка типов через `tsc --noEmit`

Веб-сервер (`server.ts`) проксирует Deezer и Radio Browser, а локальная библиотека
хранится в `data/library.json`, файлы — в `downloads/`.

## Структура

```
main.py, logic.py, radio_client.py, radio_player.py   настольное приложение
src/, index.html, server.ts                           веб-версия
andrKIVY/                                             мобильная версия (Kivy)
build-exe.ps1, FastMusic.spec                         сборка .exe
```

## Зависимости

- Python: см. `requirements.txt`
- Node: см. `package.json`
- Опционально: токен Deezer в `.env` (скопируйте `.env.example`)

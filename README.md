# FastMusic

**Русский** | [English](README.en.md)

FastMusic — музыкальный плеер с поиском треков через Deezer, скачиванием в локальную
библиотеку, чартами и интернет-радио.

Проект состоит из двух независимых приложений:

- **`desktop/`** — настольный плеер на Python (CustomTkinter, Windows);
- **`android/`** — мобильный плеер на Kivy / KivyMD.

Веб-версия в репозиторий больше не входит: проект развивается только как настольное
и Android-приложение.

## Возможности

- Поиск треков, альбомов и исполнителей через Deezer
- Чарты Deezer, топ-треки исполнителя и похожие исполнители
- Скачивание треков в локальную библиотеку
- Воспроизведение: play / pause, перемотка, громкость, горячие клавиши
- Интернет-радио Radio Browser: популярные станции, поиск по названию, тегу и стране
- Обложки альбомов, очередь загрузок и локальная SQLite-библиотека
- Тёмная тема

## Структура репозитория

```text
.
├── desktop/                     # Настольное приложение (Python + CustomTkinter)
│   ├── main.py                  # Точка входа и интерфейс
│   ├── logic.py                 # Библиотека, загрузки, Deezer
│   ├── deezer_client.py         # Клиент Deezer API
│   ├── radio_client.py          # Клиент Radio Browser
│   ├── radio_player.py          # Воспроизведение радио через ffplay
│   ├── logger.py                # Логирование
│   ├── FastMusic.spec           # Конфигурация PyInstaller
│   ├── favicon.ico              # Иконка приложения
│   ├── requirements.txt         # Python-зависимости
│   └── .env.example             # Пример переменных окружения
│
├── android/                     # Android-приложение (Kivy + KivyMD)
│   ├── main.py                  # Точка входа и интерфейс
│   ├── logic.py                 # Библиотека, загрузки, Deezer
│   ├── audio.py                 # Аудиобэкенды (ffpyplayer / pygame / Kivy)
│   ├── deezer_client.py         # Клиент Deezer API
│   ├── logger.py                # Логирование
│   ├── fastmusic.kv             # Разметка интерфейса Kivy
│   ├── buildozer.spec           # Конфигурация сборки APK
│   ├── requirements.txt         # Зависимости для локального запуска
│   ├── icon.png                 # Иконка приложения
│   ├── presplash.png            # Заставка при запуске
│   └── recipes/                 # Локальные рецепты python-for-android
│
├── README.md                    # Этот файл (русский)
└── README.en.md                 # English README
```

`desktop/` и `android/` — самостоятельные приложения. Общие по смыслу модули
(`logic.py`, `deezer_client.py`, `logger.py`) продублированы намеренно: так каждую
платформу можно собрать и упаковать отдельно, не усложняя сборку общим пакетом.

## Настольное приложение

### Требования

- Python 3.10+
- Windows 10/11
- **ffmpeg** — нужен для скачивания треков в MP3 и воспроизведения радио

Установить ffmpeg можно через Winget:

```powershell
winget install Gyan.FFmpeg
```

Либо положите `ffmpeg.exe` в папку `desktop/` — приложение найдёт его автоматически.

### Запуск

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r desktop\requirements.txt
python desktop\main.py
```

Можно запускать и из папки приложения:

```powershell
cd desktop
python main.py
```

### Данные приложения

При запуске рядом с приложением создаются:

- `desktop/downloads/` — скачанные треки;
- `desktop/music_library.db` — локальная библиотека SQLite;
- `desktop/logs/` — логи.

Эти папки и файлы исключены из Git. У собранного `.exe` данные хранятся рядом
с исполняемым файлом.

### Настройка Deezer

Токен не обязателен, но с ним выше лимиты Deezer API:

```powershell
copy desktop\.env.example desktop\.env
```

Затем укажите `DEEZER_TOKEN` в `desktop/.env`. Токен можно получить на
[developers.deezer.com](https://developers.deezer.com/myapps).

### Сборка `.exe`

```powershell
pip install pyinstaller
cd desktop
pyinstaller FastMusic.spec
```

Готовый файл появится в `desktop/dist/FastMusic.exe`. Если рядом с `FastMusic.spec`
лежит `ffmpeg.exe`, он будет включён в сборку. Консольное окно можно отключить,
заменив в `FastMusic.spec` строку `console=True` на `console=False`.

## Android-приложение

Приложение написано на Kivy / KivyMD. Интерфейс мобильной версии сейчас на
украинском языке. Аудиобэкенд выбирается автоматически: `ffpyplayer` → `pygame` →
`Kivy SoundLoader`; на Android используется встроенный бэкенд Kivy.

### Локальный запуск

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r android\requirements.txt
python android\main.py
```

На Windows для локального запуска может понадобиться ffpyplayer и дополнительные
системные библиотеки. Для проверки интерфейса это не обязательно — приложение
запустится и без аудио.

### Сборка APK

Buildozer работает на Linux. На Windows используйте WSL2 с Ubuntu:

```powershell
wsl --install -d Ubuntu
```

Внутри Ubuntu:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
    autoconf automake libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo6 cmake libffi-dev libssl-dev
pip3 install --user buildozer cython
```

Затем:

```bash
cd /path/to/FastMusic/android
buildozer -v android debug
```

Готовый APK появится в `android/bin/`. Buildozer сам скачает Android SDK, NDK и
остальные зависимости. Локальный рецепт `materialyoucolor` подключён через
`p4a.local_recipes` в `buildozer.spec`.

### Данные на Android

На устройстве библиотека, логи и скачанные треки хранятся во внутреннем хранилище
приложения (`app_storage_path()`), а не в папке проекта.

## Разработка

- Python-код каждого приложения можно проверить без запуска:

  ```bash
  python -m compileall desktop android
  ```

- Логи приложения пишутся в `logs/fastmusic.log` рядом с приложением.
- Скачанные треки и база данных не коммитятся — они перечислены в `.gitignore`.
- Для настольной версии токен Deezer хранится только в `desktop/.env`
  (файл исключён из Git).

## Лицензия

Лицензия в репозитории не указана. Если планируется публичное распространение,
добавьте файл `LICENSE` с подходящей лицензией.

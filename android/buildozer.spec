[app]

title = FastMusic
package.name = fastmusic
package.domain = org.fastmusic

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
source.exclude_dirs = .buildozer,bin,__pycache__,logs,downloads
source.exclude_patterns = *.db,*.log,*.pyc,.env

version = 1.0.0

requirements = python3,kivy,kivymd==1.0.2,httpx,requests,mutagen,deezer-python,python-dotenv,yt-dlp,pillow,pyjnius

orientation = portrait

fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE

android.api = 33
android.minapi = 24
android.targetapi = 33
android.archs = arm64-v8a
android.accept_sdk_license = True

p4a.branch = develop
p4a.local_recipes = ./recipes

log_level = 2

warn_on_root = 0

android.allow_backup = True

presplash.filename = %(source.dir)s/presplash.png
icon.filename = %(source.dir)s/icon.png

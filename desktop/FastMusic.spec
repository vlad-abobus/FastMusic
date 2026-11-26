# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


datas = []
hiddenimports = []
binaries = []

# customtkinter — нужны темы, иконки, шрифты
datas += collect_data_files("customtkinter")
hiddenimports += collect_submodules("customtkinter")

# PIL/Pillow
hiddenimports += ["PIL", "PIL._tkinter_finder"]

# ffmpeg — кладём рядом с exe для конвертации в mp3
_SPEC_DIR = SPECPATH
_ffmpeg_src = os.path.join(_SPEC_DIR, "ffmpeg.exe")
if os.path.isfile(_ffmpeg_src):
    binaries += [(_ffmpeg_src, ".")]

# downlevel — API set DLLs для совместимости с Windows 7/8
_downlevel_dir = r"C:\Windows\System32\downlevel"
if os.path.isdir(_downlevel_dir):
    for f in os.listdir(_downlevel_dir):
        if f.lower().endswith(".dll"):
            src = os.path.join(_downlevel_dir, f)
            binaries += [(src, "downlevel")]

# собственные модули
for mod in ["logic", "logger", "radio_client", "radio_player", "deezer_client"]:
    hiddenimports.append(mod)
    datas += collect_data_files(mod)


a = Analysis(
    [os.path.join(_SPEC_DIR, "main.py")],
    pathex=[_SPEC_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter.test",
        "unittest",
        "pytest",
        "setuptools",
        "pip",
        "distutils",
        "Cython",
        "ipython",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FastMusic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(_SPEC_DIR, "favicon.ico")],
)

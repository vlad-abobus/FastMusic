#!/bin/bash
# Скрипт для збірки APK через WSL + Buildozer
# Запуск: bash build_apk.sh

set -e

echo "=== Встановлення залежностей ==="

sudo apt update
sudo apt install -y \
    python3 python3-pip python3-venv \
    git zip unzip autoconf automake libtool pkg-config \
    zlib1g-dev libncurses-dev \
    cmake libffi-dev libssl-dev \
    adb clang make \
    libltdl-dev libpng-dev libjpeg-dev \
    openjdk-17-jdk

echo "=== Встановлення Buildozer ==="

pip3 install --break-system-packages --upgrade buildozer cython

export PATH="$HOME/.local/bin:$PATH"
export PIP_BREAK_SYSTEM_PACKAGES=1

echo "=== Копіювання проєкту ==="

PROJECT_DIR="$HOME/FastMusic_Android"
mkdir -p "$PROJECT_DIR"

cp -r /mnt/c/Users/Lenovo/Desktop/FastMusic/andrKIVY/* "$PROJECT_DIR/" 2>/dev/null || true
cd "$PROJECT_DIR"

echo "=== Збірка APK ==="
echo "Це займе 15-40 хвилин при першій збірці..."

buildozer android debug

echo ""
echo "=== Готово! ==="
echo "APK знаходиться в: $PROJECT_DIR/bin/"
ls -la bin/*.apk 2>/dev/null || echo "APK не знайдено, перевірте логи"

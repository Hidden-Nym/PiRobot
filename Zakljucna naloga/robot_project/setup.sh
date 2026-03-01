#!/bin/bash
# ============================================================
# Namestitveni skript za Robot projekt - Raspberry Pi 5
# Zaključna naloga
# ============================================================

set -e

echo "============================================"
echo "  Namestitev Robot projekta za RPi 5"
echo "============================================"
echo ""

# Preveri ali smo na Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "[OPOZORILO] Ta skript je namenjen za Raspberry Pi."
    echo "            Nadaljujem vseeno..."
fi

# 1. Posodobi sistem
echo "[1/6] Posodabljam sistem..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Namesti sistemske pakete
echo "[2/6] Nameščam sistemske pakete..."
sudo apt-get install -y \
    python3-full \
    python3-pip \
    python3-venv \
    python3-opencv \
    python3-lgpio \
    python3-pyaudio \
    portaudio19-dev \
    libatlas-base-dev \
    libopenblas-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    v4l-utils \
    flac \
    git

# 3. Ustvari Python virtualno okolje
echo "[3/6] Ustvarjam Python virtualno okolje..."
VENV_DIR="$(dirname "$0")/venv"

if [ -d "$VENV_DIR" ]; then
    echo "         Virtualno okolje že obstaja, preskakujem..."
else
    python3 -m venv --system-site-packages "$VENV_DIR"
fi

# Aktiviraj venv
source "$VENV_DIR/bin/activate"

# 4. Namesti Python pakete
echo "[4/6] Nameščam Python pakete..."
pip install --upgrade pip
pip install \
    opencv-python==4.9.0.80 \
    numpy>=1.26.0 \
    SpeechRecognition>=3.10.0 \
    ultralytics>=8.1.0

# lgpio in PyAudio sta nameščena preko sistemskih paketov (--system-site-packages)

# 5. Prenesi YOLOv8 nano model
echo "[5/6] Prenašam YOLOv8 nano model..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
echo "         YOLOv8n model prenesen."

# 6. Preveri kamero in mikrofon
echo "[6/6] Preverjam kamero in mikrofon..."

# Preveri kamero
if v4l2-ctl --list-devices 2>/dev/null | grep -q "video"; then
    echo "         [OK] USB kamera zaznana."
else
    echo "         [!] USB kamera NI zaznana. Priklopi kamero in poskusi znova."
fi

# Preveri mikrofon
if arecord -l 2>/dev/null | grep -q "card"; then
    echo "         [OK] Mikrofon zaznan."
else
    echo "         [!] Mikrofon NI zaznan. Priklopi mikrofon in poskusi znova."
fi

echo ""
echo "============================================"
echo "  Namestitev končana!"
echo "============================================"
echo ""
echo "Za zagon robota:"
echo "  1. source venv/bin/activate"
echo "  2. python3 main.py"
echo ""
echo "Za testiranje posameznih modulov:"
echo "  python3 motor_control.py"
echo "  python3 ultrasonic_sensor.py"
echo "  python3 camera_vision.py"
echo "  python3 speech_recognition_module.py"
echo ""

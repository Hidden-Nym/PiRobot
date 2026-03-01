"""
Konfiguracija za Robot projekt.
Vse nastavitve so na enem mestu za lažje spreminjanje.
"""

# ============================================================
# GPIO PINI (BCM številčenje)
# ============================================================

# L298N Motor Driver
MOTOR_ENA = 12      # PWM za levi motor (Pin 32)
MOTOR_IN1 = 23      # Levi motor smer 1 (Pin 16)
MOTOR_IN2 = 24      # Levi motor smer 2 (Pin 18)
MOTOR_IN3 = 27      # Desni motor smer 1 (Pin 13)
MOTOR_IN4 = 22      # Desni motor smer 2 (Pin 15)
MOTOR_ENB = 13      # PWM za desni motor (Pin 33)

# HC-SR04 Ultrasonični senzor
ULTRASONIC_TRIG = 17    # Trigger pin (Pin 11)
ULTRASONIC_ECHO = 18    # Echo pin (Pin 12) - POTREBUJE napetostni delilnik!

# ============================================================
# MOTOR PARAMETRI
# ============================================================

PWM_FREQUENCY = 1000    # PWM frekvenca v Hz
MOTOR_SPEED = 60        # Privzeta hitrost (0-100%)
TURN_SPEED = 50         # Hitrost med obračanjem (0-100%)
SLOW_SPEED = 35         # Počasna hitrost za fino približevanje

# ============================================================
# KAMERA PARAMETRI
# ============================================================

CAMERA_INDEX = 0            # USB kamera indeks (običajno 0)
CAMERA_WIDTH = 640          # Resolucija - širina
CAMERA_HEIGHT = 480         # Resolucija - višina
CAMERA_FPS = 30             # Sličic na sekundo

# Pozicija objekta v sliki (tretjine)
FRAME_CENTER_MIN = 0.35    # Levi rob sredine (35% širine)
FRAME_CENTER_MAX = 0.65    # Desni rob sredine (65% širine)

# Minimalna velikost konture (v pikslih) za filtriranje šuma
MIN_CONTOUR_AREA = 300

# ============================================================
# KAMERA OJAČANJE (za slabše kamere)
# ============================================================

CAMERA_ENHANCE = True           # Omogoči programsko ojačanje barv
CAMERA_SATURATION_MULT = 2.0   # Množitelj saturacije (2.0 = dvojna)
CAMERA_BRIGHTNESS_ADD = 30     # Dodana svetlost (0-50)

# ============================================================
# HSV BARVNI RAZPONI
# Znižani pragovi za slabše kamere (S in V: 50 namesto 100)
# H: 0-179, S: 0-255, V: 0-255
# ============================================================

COLOR_RANGES = {
    "rdeca": [
        # Rdeča ima dva razpona v HSV (okoli 0 in okoli 180)
        {"lower": (0, 50, 50), "upper": (10, 255, 255)},
        {"lower": (160, 50, 50), "upper": (179, 255, 255)},
    ],
    "modra": [
        {"lower": (90, 50, 50), "upper": (130, 255, 255)},
    ],
    "zelena": [
        {"lower": (30, 50, 50), "upper": (90, 255, 255)},
    ],
    "rumena": [
        {"lower": (15, 50, 50), "upper": (35, 255, 255)},
    ],
    "siva": [
        # Temno siva: nizka saturacija, nizka-srednja svetlost
        {"lower": (0, 0, 30), "upper": (179, 50, 120)},
    ],
}

# Angleška imena barv → slovensko ime (za preslikavo)
COLOR_NAME_MAP = {
    # Angleščina → slovenščina
    "red": "rdeca",
    "blue": "modra",
    "green": "zelena",
    "yellow": "rumena",
    "gray": "siva",
    "grey": "siva",
    "dark gray": "siva",
    "dark grey": "siva",
    # Slovenščina → slovenščina (za direktno uporabo)
    "rdeca": "rdeca",
    "rdečo": "rdeca",
    "rdecega": "rdeca",
    "rdeča": "rdeca",
    "rdečega": "rdeca",
    "modra": "modra",
    "modro": "modra",
    "modrga": "modra",
    "modri": "modra",
    "zelena": "zelena",
    "zeleno": "zelena",
    "zelenega": "zelena",
    "zeleni": "zelena",
    "rumena": "rumena",
    "rumeno": "rumena",
    "rumenega": "rumena",
    "rumeni": "rumena",
    "siva": "siva",
    "sivo": "siva",
    "sivega": "siva",
    "sivi": "siva",
    "temno siva": "siva",
    "temno sivo": "siva",
}

# Prikazno ime barve (za izpis)
COLOR_DISPLAY_NAMES = {
    "rdeca": "rdeča",
    "modra": "modra",
    "zelena": "zelena",
    "rumena": "rumena",
    "siva": "temno siva",
}

# ============================================================
# OBLIKE
# ============================================================

# Število oglišč → ime oblike
SHAPE_VERTICES = {
    3: "trikotnik",
    4: "kvadrat",     # Tudi kocka (v 2D pogledu je kvadrat)
}
# Krog se prepozna, ko je število oglišč > 6

# Preslikava imen oblik
SHAPE_NAME_MAP = {
    # Angleščina
    "triangle": "trikotnik",
    "square": "kvadrat",
    "cube": "kvadrat",
    "circle": "krog",
    # Slovenščina
    "trikotnik": "trikotnik",
    "kvadrat": "kvadrat",
    "kocka": "kvadrat",
    "kocko": "kvadrat",
    "krog": "krog",
}

SHAPE_DISPLAY_NAMES = {
    "trikotnik": "trikotnik",
    "kvadrat": "kvadrat/kocka",
    "krog": "krog",
}

# ============================================================
# ULTRASONIČNI SENZOR
# ============================================================

ULTRASONIC_TIMEOUT = 0.04       # Timeout za meritev (sekunde)
ULTRASONIC_NUM_SAMPLES = 3      # Število meritev za povprečje
ULTRASONIC_SAMPLE_DELAY = 0.01  # Zamik med meritvami (sekunde)

# ============================================================
# NAVIGACIJA
# ============================================================

TARGET_DISTANCE_CM = 5.0        # Razdalja do objekta za "dotik" (cm)
SEARCH_TURN_DURATION = 0.3      # Trajanje obrata med iskanjem (sekunde)
MAX_SEARCH_ROTATIONS = 12       # Maks. št. obratov pri iskanju (360°)

# P-regulator za krmiljenje smeri
KP_STEERING = 0.8              # Proporcionalni koeficient za korekcijo smeri

# ============================================================
# GOVOR
# ============================================================

SPEECH_LANGUAGE_PRIMARY = "sl-SI"   # Primarni jezik (slovenščina)
SPEECH_LANGUAGE_SECONDARY = "en-US" # Sekundarni jezik (angleščina)
SPEECH_TIMEOUT = 5                  # Čas čakanja na govor (sekunde)
SPEECH_PHRASE_LIMIT = 10            # Maks. dolžina fraze (sekunde)

# ============================================================
# YOLO NASTAVITVE
# ============================================================

YOLO_MODEL = "yolov8n.pt"          # YOLOv8 nano model
YOLO_CONFIDENCE = 0.5              # Minimalna zanesljivost detekcije
YOLO_ENABLED = True                # Omogoči YOLO kot backup

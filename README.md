# Avtonomni robot z vizualnim prepoznavanjem in glasovnimi ukazi

## Zaključna naloga

---

## 1. Uvod

Namen zaključne naloge je izdelava avtonomnega robota, ki na podlagi glasovnih ukazov poišče in se premakne do določenega objekta. Robot s kamero prepozna objekte po barvi in obliki, z ultrasoničnim senzorjem meri razdaljo do ovir, ter z dvema DC motorjema avtonomno navigira do cilja.

### 1.1 Cilji naloge

- Izdelati robota, ki prepozna barvne geometrijske oblike (rdeča kocka, modri trikotnik, itd.)
- Implementirati glasovno upravljanje v slovenščini in angleščini
- Robot se avtonomno premakne do ciljnega objekta in ga dotakne/potisne
- Dokumentirati celoten postopek izdelave

---

## 2. Komponente

### 2.1 Strojna oprema (Hardware)

| Komponenta | Opis |
|---|---|
| **Raspberry Pi 5 (8GB)** | Glavni računalnik robota |
| **USB kamera** | Zajem slike za vizualno prepoznavanje |
| **USB mikrofon** | Zajem govora za glasovne ukaze |
| **2x DC krtačni motor** | Pogon robota (levi in desni) |
| **L298N motor driver** | H-bridge za krmiljenje motorjev |
| **HC-SR04 ultrasonični senzor** | Merjenje razdalje do objektov |
| **2x LED dioda + 2x upor 330Ω** | Vizualni indikator stanja robota |
| **Baterija/napajalnik** | Napajanje motorjev in RPi |

### 2.2 Programska oprema (Software)

| Tehnologija | Namen |
|---|---|
| **Python 3** | Programski jezik |
| **OpenCV** | Računalniški vid - detekcija barv in oblik |
| **YOLOv8** | AI detekcija objektov (backup) |
| **Google Speech-to-Text** | Prepoznavanje govora |
| **lgpio** | Krmiljenje GPIO pinov na RPi 5 |

---

## 3. Vezalni načrt

### 3.1 GPIO povezava

```
Raspberry Pi 5                L298N Motor Driver
─────────────                ──────────────────
GPIO 12 (Pin 32) ──────────── ENA (PWM levi motor)
GPIO 23 (Pin 16) ──────────── IN1 (levi smer 1)
GPIO 24 (Pin 18) ──────────── IN2 (levi smer 2)
GPIO 27 (Pin 13) ──────────── IN3 (desni smer 1)
GPIO 22 (Pin 15) ──────────── IN4 (desni smer 2)
GPIO 13 (Pin 33) ──────────── ENB (PWM desni motor)
GND      (Pin 6)  ──────────── GND
```

```
Raspberry Pi 5                HC-SR04 Senzor
─────────────                ─────────────────
GPIO 17 (Pin 11) ──────────── TRIG
GPIO 18 (Pin 12) ──┐
                    │          ECHO
               [1kΩ]─┤
                    │
               [2kΩ]─┤
                    │
                   GND
5V       (Pin 2)  ──────────── VCC
GND      (Pin 6)  ──────────── GND
```

**POMEMBNO:** ECHO pin HC-SR04 deluje na 5V, Raspberry Pi GPIO pa na 3.3V. Napetostni delilnik z upori 1kΩ in 2kΩ zniža napetost na varnih 3.3V.

```
Raspberry Pi 5                LED indikatorji
─────────────                ────────────────
GPIO 25 (Pin 22) ──[330Ω]──── LED "poslušanje" (+) ──── GND
GPIO 26 (Pin 37) ──[330Ω]──── LED "iskanje" (+) ──────── GND
```

**Vezava LED:** Anodo (daljšo nožico) poveži na upor → GPIO pin, katodo (krajšo) na GND.

### 3.2 Napajanje

- Raspberry Pi 5: USB-C napajalnik (5V/5A) ali power bank
- L298N in motorji: ločen vir napajanja (npr. 4x AA baterije = 6V ali Li-Po baterija 7.4V)
- **GND mora biti skupen** med RPi in L298N!

---

## 4. Struktura programa

```
robot_project/
├── config.py                      # Vse nastavitve (GPIO, barve, parametri)
├── motor_control.py               # Krmiljenje motorjev (L298N)
├── ultrasonic_sensor.py           # Ultrasonični senzor (HC-SR04)
├── camera_vision.py               # Vizualno prepoznavanje (OpenCV + YOLO)
├── speech_recognition_module.py   # Glasovni ukazi (Google Speech API)
├── navigation.py                  # Navigacijska logika
├── led_controller.py              # LED indikatorji stanja
├── main.py                        # Glavni program
├── requirements.txt               # Python knjižnice
├── setup.sh                       # Namestitveni skript
└── dokumentacija.md               # Ta dokument
```

### 4.1 Opis modulov

#### config.py
Centralna konfiguracijska datoteka. Vse nastavitve so na enem mestu: GPIO pini, HSV barvni razponi za detekcijo barv, parametri motorjev (PWM frekvenca, hitrost), nastavitve kamere in navigacijski parametri.

#### motor_control.py
Razred `MotorController` krmili dva DC motorja preko L298N H-bridge driverja. Uporablja knjižnico `lgpio`, ki je podprta na Raspberry Pi 5 (starejši `RPi.GPIO` ni združljiv z RPi 5). Podpira vožnjo naprej, nazaj, zavijanje levo/desno in proporcionalno krmiljenje z različnimi hitrostmi na vsakem motorju.

#### ultrasonic_sensor.py
Razred `UltrasonicSensor` meri razdaljo z ultrasoničnim senzorjem HC-SR04. Pošlje ultrazvočni impulz in izmeri čas, ki ga signal potrebuje za pot do ovire in nazaj. Za večjo natančnost izvede več meritev in vrne povprečje.

#### camera_vision.py
Razred `CameraVision` izvaja vizualno prepoznavanje objektov:

**OpenCV pristop (primarni):**
1. Zajame sliko z USB kamere
2. Pretvori iz BGR v HSV barvni prostor
3. Ustvari barvno masko za ciljno barvo (rdeča, modra, zelena, rumena)
4. Najde konture (obrise) v maski
5. Za vsako konturo določi obliko s štetjem oglišč:
   - 3 oglišča → trikotnik
   - 4 oglišča (razmerje stranic ~1:1) → kvadrat/kocka
   - Več kot 6 oglišč + visoka cirkularnost → krog

**YOLOv8 pristop (backup):**
Če OpenCV ne najde objekta, se uporabi YOLOv8 nano model za splošno detekcijo objektov.

#### speech_recognition_module.py
Razred `SpeechRecognizer` prepoznava glasovne ukaze:
1. Posluša mikrofon
2. Pošlje zvočni posnetek na Google Speech-to-Text API
3. Poskusi najprej slovenščino, nato angleščino
4. Parsira prepoznani tekst v strukturiran ukaz z barvo in obliko

Podprti ukazi:
- Slovenščina: "najdi rdečo kocko", "najdi modri trikotnik"
- Angleščina: "find red cube", "find blue triangle"
- Ustavitev: "ustavi", "stop"
- Pavza/nadaljevanje: "pavza", "nadaljuj"

#### navigation.py
Razred `Navigator` izvaja avtonomno navigacijo:

1. **Iskanje:** Če objekt ni viden, se robot obrača na mestu in išče
2. **Približevanje:** Ko je objekt najden, se mu približa:
   - Uporablja P-regulator (proporcionalno krmiljenje) za korekcijo smeri
   - Če je objekt levo od centra → korigira v levo (in obratno)
   - Neprestano preverja razdaljo z ultrasoničnim senzorjem
3. **Dotik:** Ko je razdalja manjša od 3.5 cm, se ustavi = objekt dotaknjen/potisnjen

#### led_controller.py
Razred `LEDController` krmili dve LED diodi za vizualni prikaz stanja robota:
- **LED poslušanje (pin 25):** sveti ko robot čaka na glasovni ukaz
- **LED iskanje (pin 26):** sveti med avtonomno navigacijo do objekta

#### main.py
Glavni program, ki poveže vse module. Štirje načini delovanja:
- **Hibridni (privzeto):** `python3 main.py` — mikrofon + tipkovnica kot rezerva
- **Glasovni:** `python3 main.py --voice` — samo glasovni ukazi
- **Testni:** `python3 main.py --test` — samo tipkovnica (brez mikrofona)
- **Demo:** `python3 main.py --demo` — takoj poišče rdečo kocko

---

## 5. Algoritem delovanja

### 5.1 Diagram poteka

```
          ┌─────────────┐
          │    START     │
          └──────┬──────┘
                 │
          ┌──────▼──────┐
          │  Čakaj na   │
          │ glasovni    │◄────────────────┐
          │   ukaz      │                 │
          └──────┬──────┘                 │
                 │                        │
          ┌──────▼──────┐     DA   ┌──────┴──────┐
          │ Ukaz =      ├────────► │   USTAVI    │
          │ "ustavi"?   │         └─────────────┘
          └──────┬──────┘
                 │ NE
          ┌──────▼──────┐
          │ Parsaj      │
          │ barvo+obliko│
          └──────┬──────┘
                 │
          ┌──────▼──────┐
          │ Ali vidi    │  DA  ┌─────────────────┐
          │ objekt?     ├─────►│ Približuj se z   │
          └──────┬──────┘      │ P-regulatorjem   │
                 │ NE          └────────┬─────────┘
          ┌──────▼──────┐              │
          │ Obrni se    │       ┌──────▼──────┐
          │ in išči     │       │ Razdalja    │ DA  ┌──────────┐
          │ (360°)      │       │ < 3.5 cm?   ├────►│ USPEH!   │
          └──────┬──────┘       └──────┬──────┘     │ Dotaknil │
                 │                     │ NE         └──────┬───┘
          ┌──────▼──────┐              │                   │
          │ Najden?     │  DA          └───────────┐       │
          │             ├──────►  (ponovi)         │       │
          └──────┬──────┘                          │       │
                 │ NE                              │       │
          ┌──────▼──────┐                          │       │
          │  NEUSPEH    │                          │       │
          │  Ni najden  │                          │       │
          └──────┬──────┘                          │       │
                 │                                 │       │
                 └─────────────────────────────────┘───────┘
                                  │
                           (čakaj naslednji ukaz)
```

### 5.2 P-regulator za krmiljenje smeri

Robot uporablja proporcionalno krmiljenje (P-regulator) za natančno usmerjanje proti objektu:

```
odmik = (pozicija_objekta / širina_slike - 0.5) × 2

korekcija = Kp × odmik × bazna_hitrost

leva_hitrost  = bazna_hitrost + korekcija
desna_hitrost = bazna_hitrost - korekcija
```

Kjer je:
- `odmik`: relativni odmik objekta od centra slike (-1.0 do 1.0)
- `Kp = 0.8`: proporcionalni koeficient
- `bazna_hitrost`: hitrost motorjev (zmanjša se ko je blizu cilja)

---

## 6. Namestitev in uporaba

### 6.1 Predpogoji

- Raspberry Pi 5 z nameščenim Raspberry Pi OS (Bookworm 64-bit)
- USB kamera priključena
- USB mikrofon priključen
- L298N motor driver povezan po vezalnem načrtu (poglavje 3)
- HC-SR04 senzor povezan z napetostnim delilnikom
- Internetna povezava (za Google Speech API in namestitev)

### 6.2 Namestitev

```bash
# 1. Prenesi projekt na RPi
# (kopiraj mapo robot_project na Raspberry Pi)

# 2. Zaženi namestitveni skript
cd robot_project
bash setup.sh

# 3. Aktiviraj virtualno okolje
source venv/bin/activate
```

### 6.3 Testiranje posameznih modulov

```bash
# Test motorjev (robot se premakne naprej, nazaj, levo, desno)
python3 motor_control.py

# Test ultrasoničnega senzorja (izpisuje razdaljo)
python3 ultrasonic_sensor.py

# Test kamere (odpre okno z detekcijo objektov)
python3 camera_vision.py

# Test govora (posluša mikrofon in izpisuje ukaze)
python3 speech_recognition_module.py
```

### 6.4 Zagon robota

```bash
# Aktiviraj virtualno okolje
source venv/bin/activate

# Hibridni način - privzeto (mikrofon + tipkovnica kot rezerva)
python3 main.py

# Samo glasovni ukazi
python3 main.py --voice

# Testni način (samo tipkovnica, brez mikrofona)
python3 main.py --test

# Demo način (takoj poišče rdečo kocko)
python3 main.py --demo

# Demo z določeno barvo in obliko
python3 main.py --demo --color modra --shape trikotnik
```

### 6.5 Nadzor z tmux

Robot teče v tmux seji z imenom `robot`. Uporabne ukaze:

```bash
# Preveri ali robot teče
tmux ls

# Priklopi se na sejo in vidi izhod programa
tmux attach -t robot

# Izhod iz seje brez zaustavitve programa
# Ctrl+B, nato D
```

---

## 7. Kalibracija

### 7.1 HSV barvni razponi

Če robot ne prepozna barv pravilno, je potrebno kalibrirati HSV razpone v `config.py`. Postopek:

1. Zaženi `python3 camera_vision.py`
2. Postavi objekt pred kamero
3. Prilagodi vrednosti `COLOR_RANGES` v `config.py`:
   - **H (Hue):** Odtenek barve (0-179)
   - **S (Saturation):** Nasičenost (0-255) — višja = bolj živa barva
   - **V (Value):** Svetlost (0-255) — višja = svetlejša barva

### 7.2 Hitrost motorjev

Če se robot ne premika naravnost, prilagodi hitrosti v `config.py`:
- `MOTOR_SPEED`: Osnovna hitrost (privzeto 75%)
- `TURN_SPEED`: Hitrost obračanja (privzeto 75%)
- `SLOW_SPEED`: Počasna hitrost za fino približevanje (privzeto 35%)

### 7.3 Razdalja dotika

Prilagodi `TARGET_DISTANCE_CM` v `config.py` glede na dolžino robota (privzeto 3.5 cm).

---

## 8. Odpravljanje napak

| Problem | Rešitev |
|---|---|
| Kamera ne deluje | Preveri USB priklop. Zaženi `v4l2-ctl --list-devices`. |
| Mikrofon ne deluje | Preveri USB priklop. Zaženi `arecord -l`. |
| Motorji se ne premikajo | Preveri L298N povezavo in napajanje motorjev. |
| Razdalja vedno "None" | Preveri TRIG/ECHO povezave in napetostni delilnik. |
| Ne prepozna govora | Preveri internetno povezavo (Google API). |
| Ne vidi barv pravilno | Kalibriraj HSV razpone (poglavje 7.1). |
| Robot zavija namesto naravnost | Prilagodi hitrosti motorjev ali zamenjaj IN1/IN2 pine. |
| LED ne sveti | Preveri vezavo (anoda na GPIO pin, katoda na GND) in upore (330Ω). |

---

## 9. Zaključek

V zaključni nalogi je bil uspešno izdelan avtonomni robot na platformi Raspberry Pi 5, ki združuje računalniški vid (OpenCV + YOLOv8), prepoznavanje govora (Google Speech-to-Text) in avtonomno navigacijo (P-regulator). Robot je sposoben na glasovni ukaz v slovenščini ali angleščini poiskati objekt določene barve in oblike ter se do njega avtonomno premakniti.

Projekt demonstrira praktično uporabo:
- Računalniškega vida za prepoznavanje objektov
- Obdelave govora za upravljanje
- Regulacijske tehnike za navigacijo
- Senzorske tehnologije za zaznavanje okolice
- Programiranja v Pythonu na vgrajenem sistemu

---

*Zaključna naloga | Raspberry Pi 5 Robot*


Ko spremeniš kodo na RPi, samo te 3 ukaze:

```bash
cd /home/matija/robot_project
git add -A
git commit -m "opis spremembe"
git push
```

Če pa spremeniš na **Macu** in hočeš prenesti na RPi:

1. Na Macu: `scp datoteka matija@192.168.1.26:/home/matija/robot_project/`
2. Na RPi: `git add -A && git commit -m "opis" && git push`

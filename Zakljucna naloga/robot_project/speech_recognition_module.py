"""
Prepoznavanje glasovnih ukazov z Google Speech-to-Text API.
Podpira slovenščino in angleščino.
Parsira ukaze v strukturirano obliko {action, color, shape}.
"""

import speech_recognition as sr
import config


class Command:
    """Strukturiran glasovni ukaz."""

    def __init__(self, action, color=None, shape=None, raw_text=""):
        self.action = action        # "najdi", "ustavi", "neznano"
        self.color = color          # Normalizirano ime barve ali None
        self.shape = shape          # Normalizirano ime oblike ali None
        self.raw_text = raw_text    # Izvorni prepoznani tekst

    def __repr__(self):
        color_display = config.COLOR_DISPLAY_NAMES.get(self.color, self.color)
        shape_display = config.SHAPE_DISPLAY_NAMES.get(self.shape, self.shape)
        return (f"Ukaz(akcija={self.action}, barva={color_display}, "
                f"oblika={shape_display}, tekst='{self.raw_text}')")

    @property
    def is_valid(self):
        """Preveri ali je ukaz veljaven za iskanje."""
        return self.action == "najdi" and self.color is not None


class SpeechRecognizer:
    """Prepoznavanje glasovnih ukazov."""

    def __init__(self):
        """Inicializira mikrofon in recognizer."""
        self.recognizer = sr.Recognizer()

        # Prilagodi za okoliški šum
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300

        print("[GOVOR] Inicializiran.")
        print("[GOVOR] Preverjam mikrofon...")

        try:
            with sr.Microphone() as source:
                # Kalibriraj za okoliški šum
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("[GOVOR] Mikrofon OK.")
        except OSError:
            print("[GOVOR] NAPAKA: Mikrofon ni zaznan!")
            print("        Preveri ali je mikrofon priključen.")

    def _parse_command(self, text):
        """
        Parsira prepoznani tekst v strukturiran ukaz.
        Podpira slovenščino in angleščino.
        """
        text_lower = text.lower().strip()
        words = text_lower.split()

        # Preveri ukaz za ustavitev
        stop_words = ["ustavi", "stop", "stoj", "konec", "nehaj"]
        if any(word in words for word in stop_words):
            return Command(action="ustavi", raw_text=text)

        # Preveri ukaz za iskanje
        find_words = ["najdi", "poišči", "poisci", "išči", "isci",
                       "find", "search", "look", "get"]
        action = "neznano"
        for word in find_words:
            if word in words:
                action = "najdi"
                break

        # Poišči barvo v tekstu
        detected_color = None
        for word in words:
            if word in config.COLOR_NAME_MAP:
                detected_color = config.COLOR_NAME_MAP[word]
                break

        # Poišči obliko v tekstu
        detected_shape = None
        for word in words:
            if word in config.SHAPE_NAME_MAP:
                detected_shape = config.SHAPE_NAME_MAP[word]
                break

        # Če smo našli barvo ali obliko, predpostavi akcijo "najdi"
        if (detected_color or detected_shape) and action == "neznano":
            action = "najdi"

        return Command(
            action=action,
            color=detected_color,
            shape=detected_shape,
            raw_text=text,
        )

    def listen(self):
        """
        Posluša mikrofon in vrne prepoznani ukaz.
        Poskusi najprej slovenščino, nato angleščino.

        Returns:
            Command objekt ali None če ni prepoznal govora.
        """
        try:
            with sr.Microphone() as source:
                print("[GOVOR] Poslušam... (govori ukaz)")
                audio = self.recognizer.listen(
                    source,
                    timeout=config.SPEECH_TIMEOUT,
                    phrase_time_limit=config.SPEECH_PHRASE_LIMIT,
                )

            # Poskusi slovenščino
            text = None
            try:
                text = self.recognizer.recognize_google(
                    audio, language=config.SPEECH_LANGUAGE_PRIMARY
                )
                print(f"[GOVOR] Prepoznano (SL): '{text}'")
            except sr.UnknownValueError:
                pass

            # Če slovenščina ni uspela, poskusi angleščino
            if text is None:
                try:
                    text = self.recognizer.recognize_google(
                        audio, language=config.SPEECH_LANGUAGE_SECONDARY
                    )
                    print(f"[GOVOR] Prepoznano (EN): '{text}'")
                except sr.UnknownValueError:
                    print("[GOVOR] Ni prepoznal govora.")
                    return None

            # Parsaj ukaz
            command = self._parse_command(text)
            print(f"[GOVOR] {command}")
            return command

        except sr.WaitTimeoutError:
            print("[GOVOR] Ni zaznal govora (timeout).")
            return None
        except sr.RequestError as e:
            print(f"[GOVOR] Napaka Google API: {e}")
            print("        Preveri internetno povezavo.")
            return None

    def listen_continuous(self, callback):
        """
        Neprekinjeno posluša in kliče callback za vsak prepoznan ukaz.

        Args:
            callback: Funkcija ki sprejme Command objekt.
        """
        print("[GOVOR] Neprekinjeno poslušanje aktivno.")
        while True:
            command = self.listen()
            if command is not None:
                callback(command)
                if command.action == "ustavi":
                    break


# ============================================================
# Test govora (zaženi z: python3 speech_recognition_module.py)
# ============================================================
if __name__ == "__main__":
    print("=== Test prepoznavanja govora ===")
    print("Podprti ukazi:")
    print("  SL: 'najdi rdečo kocko', 'najdi modri trikotnik', 'ustavi'")
    print("  EN: 'find red cube', 'find blue triangle', 'stop'")
    print("")
    print("Pritisni Ctrl+C za izhod.")
    print("")

    recognizer = SpeechRecognizer()

    def on_command(cmd):
        print(f"  -> Prejet ukaz: {cmd}")
        if cmd.is_valid:
            color = config.COLOR_DISPLAY_NAMES.get(cmd.color, cmd.color)
            shape = config.SHAPE_DISPLAY_NAMES.get(cmd.shape, cmd.shape)
            print(f"     Iščem: {color} {shape}")
        elif cmd.action == "ustavi":
            print("     Robot se ustavlja.")
        else:
            print("     Ukaz ni razumljen. Poskusi znova.")
        print("")

    try:
        recognizer.listen_continuous(on_command)
    except KeyboardInterrupt:
        print("\nPrekinjen s Ctrl+C")

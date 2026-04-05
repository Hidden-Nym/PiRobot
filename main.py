#!/usr/bin/env python3
"""
Glavni program za Robot projekt.
Zaključna naloga - Raspberry Pi 5

Uporaba:
    python3 main.py              # Hibridni način (mikrofon + tipkovnica failsafe)
    python3 main.py --test       # Testni način (samo tipkovnica)
    python3 main.py --voice      # Samo glasovni ukazi
    python3 main.py --demo       # Demo: najdi rdečo kocko

Podprti glasovni ukazi:
    SL: "najdi rdečo kocko", "najdi modri trikotnik", "ustavi", "pavza", "nadaljuj"
    EN: "find red cube", "find blue triangle", "stop", "pause", "resume"
"""

import sys
import time
import signal
import select
import threading
import config
from motor_control import MotorController
from camera_vision import CameraVision
from ultrasonic_sensor import UltrasonicSensor
from speech_recognition_module import SpeechRecognizer, Command
from navigation import Navigator


class Robot:
    """Glavni razred ki poveže vse module robota."""

    def __init__(self):
        """Inicializira vse module."""
        print("=" * 50)
        print("  ROBOT - Zaključna naloga")
        print("  Raspberry Pi 5")
        print("=" * 50)
        print("")

        print("Inicializiram module...")
        self.motors = MotorController()
        self.camera = CameraVision()
        self.sensor = UltrasonicSensor()
        self.speech = SpeechRecognizer()
        self.navigator = Navigator(self.motors, self.camera, self.sensor)

        self._running = False
        self._paused = False
        self._nav_thread = None
        self._last_nav_color = None
        self._last_nav_shape = None
        print("")
        print("Vsi moduli inicializirani. Robot pripravljen.")
        print("")

    def _start_navigation(self, color, shape):
        """Zažene navigacijo v ločeni niti, da glavna zanka ostane odzivna."""
        # Ustavi morebitno prejšnjo navigacijo
        if self._nav_thread and self._nav_thread.is_alive():
            self.navigator.stop()
            self._nav_thread.join(timeout=2)

        color_display = config.COLOR_DISPLAY_NAMES.get(color, color)
        shape_display = ""
        if shape:
            shape_display = " " + config.SHAPE_DISPLAY_NAMES.get(shape, shape)

        def nav_task():
            success = self.navigator.navigate_to_object(
                target_color=color,
                target_shape=shape,
            )
            if success:
                print("")
                print(f"[ROBOT] USPEH! {color_display}{shape_display} "
                      f"dosežen in dotaknjen.")
                print("[ROBOT] Premor 5 sekund...")
                time.sleep(5)
            else:
                print("")
                print(f"[ROBOT] NEUSPEH. {color_display}{shape_display} "
                      f"ni bil najden.")
            print("")
            print("Čakam na naslednji ukaz...")
            print("")

        self._nav_thread = threading.Thread(target=nav_task, daemon=True)
        self._nav_thread.start()

    def _handle_command(self, command):
        """
        Obdela ukaz. Navigacija teče v ločeni niti, zato so
        pavza/ustavi/nadaljuj takoj odzivni.
        """
        if command.action == "ustavi":
            print("[ROBOT] Ukaz: USTAVI")
            self._paused = False
            self.navigator.stop()
            return

        if command.action == "pavza":
            self._paused = True
            self.navigator.stop()
            print("[ROBOT] PAVZA. Reci 'nadaljuj' za nadaljevanje.")
            return

        if command.action == "nadaljuj":
            if not self._paused:
                print("[ROBOT] Robot ni na pavzi.")
                return
            self._paused = False
            if self._last_nav_color:
                color_display = config.COLOR_DISPLAY_NAMES.get(
                    self._last_nav_color, self._last_nav_color)
                print(f"[ROBOT] Nadaljujem iskanje: {color_display}")
                self._start_navigation(self._last_nav_color, self._last_nav_shape)
            else:
                print("[ROBOT] Nadaljevanje. Čakam na ukaz...")
            return

        if self._paused:
            print("[ROBOT] Robot je na pavzi. Reci 'nadaljuj' za nadaljevanje.")
            return

        if command.action == "najdi":
            if command.color is None:
                print("[ROBOT] Nisem razumel barve. Poskusi znova.")
                print("        Primer: 'najdi rdečo kocko'")
                return

            color_display = config.COLOR_DISPLAY_NAMES.get(
                command.color, command.color
            )
            shape_display = ""
            if command.shape:
                shape_display = " " + config.SHAPE_DISPLAY_NAMES.get(
                    command.shape, command.shape
                )

            print(f"[ROBOT] Ukaz: Najdi {color_display}{shape_display}")
            print("")

            self._last_nav_color = command.color
            self._last_nav_shape = command.shape
            self._start_navigation(command.color, command.shape)

        else:
            print(f"[ROBOT] Nerazumljen ukaz: '{command.raw_text}'")
            print("        Podprti ukazi: 'najdi [barva] [oblika]', 'ustavi', 'pavza', 'nadaljuj'")

    def run(self):
        """Glavni cikel: posluša glasovne ukaze in jih izvaja."""
        self._running = True
        print("=" * 50)
        print("  NAČIN DELOVANJA: Glasovni ukazi")
        print("  Reci ukaz ali pritisni Ctrl+C za izhod")
        print("=" * 50)
        print("")
        print("Primeri ukazov:")
        print("  SL: 'najdi rdečo kocko'")
        print("  SL: 'najdi modri trikotnik'")
        print("  EN: 'find red cube'")
        print("  EN: 'find blue triangle'")
        print("  Ustavi: 'ustavi' ali 'stop'")
        print("  Pavza:  'pavza' | Nadaljuj: 'nadaljuj'")
        print("")

        while self._running:
            command = self.speech.listen()
            if command is not None:
                self._handle_command(command)
                if command.action == "ustavi":
                    self._running = False

    def run_keyboard(self):
        """
        Testni način: ukazi preko tipkovnice namesto mikrofona.
        Uporabno za testiranje brez mikrofona.
        """
        self._running = True
        print("=" * 50)
        print("  NAČIN DELOVANJA: Tipkovnica (test)")
        print("  Vnesi ukaz ali 'q' za izhod")
        print("=" * 50)
        print("")
        print("Primeri ukazov:")
        print("  'najdi rdeco kocko'")
        print("  'najdi modri trikotnik'")
        print("  'find red cube'")
        print("  'ustavi' ali 'q'")
        print("  'pavza' | 'nadaljuj'")
        print("")

        while self._running:
            try:
                text = input("[VNOS] > ").strip()
                if not text:
                    continue
                if text.lower() in ("q", "quit", "exit"):
                    break

                command = self.speech._parse_command(text)
                print(f"  Parsano: {command}")
                self._handle_command(command)
                if command.action == "ustavi":
                    self._running = False

            except EOFError:
                break

    def run_hybrid(self):
        """
        Hibridni način: poskusi mikrofon, ob napaki ponudi tipkovnico.
        Uporabnik lahko kadarkoli vtipka ukaz med čakanjem na govor.
        """
        self._running = True
        mic_available = True

        # Preveri mikrofon ob zagonu
        try:
            import speech_recognition as sr
            with sr.Microphone() as source:
                pass
        except (OSError, Exception):
            mic_available = False

        print("=" * 50)
        print("  NAČIN DELOVANJA: Hibridni (mikrofon + tipkovnica)")
        if mic_available:
            print("  Mikrofon: ZAZNAN")
        else:
            print("  Mikrofon: NI ZAZNAN (samo tipkovnica)")
        print("  Vtipkaj ukaz kadarkoli ali govori v mikrofon")
        print("  'q' za izhod")
        print("=" * 50)
        print("")
        print("Primeri ukazov:")
        print("  'najdi rdeco kocko'")
        print("  'najdi modri trikotnik'")
        print("  'find red cube'")
        print("  'ustavi' ali 'q'")
        print("  'pavza' | 'nadaljuj'")
        print("")

        while self._running:
            if mic_available:
                # Poskusi mikrofon
                command = self.speech.listen()
                if command is not None:
                    self._handle_command(command)
                    if command.action == "ustavi":
                        self._running = False
                    continue

                # Mikrofon ni ujel govora — ponudi tipkovnico
                print("[TIPKOVNICA] Vtipkaj ukaz ali pritisni Enter za nadaljevanje poslušanja:")
                if select.select([sys.stdin], [], [], 7.0)[0]:
                    try:
                        text = sys.stdin.readline().strip()
                        if not text:
                            continue
                        if text.lower() in ("q", "quit", "exit"):
                            break
                        command = self.speech._parse_command(text)
                        print(f"  [TIPKOVNICA] Parsano: {command}")
                        self._handle_command(command)
                        if command.action == "ustavi":
                            self._running = False
                    except EOFError:
                        break
            else:
                # Mikrofon ni na voljo, samo tipkovnica
                try:
                    text = input("[VNOS] > ").strip()
                    if not text:
                        continue
                    if text.lower() in ("q", "quit", "exit"):
                        break
                    command = self.speech._parse_command(text)
                    print(f"  [TIPKOVNICA] Parsano: {command}")
                    self._handle_command(command)
                    if command.action == "ustavi":
                        self._running = False
                except EOFError:
                    break

    def run_demo(self, color="rdeca", shape="kvadrat"):
        """
        Demo način: takoj poišče objekt brez glasovnih ukazov.

        Args:
            color: Ciljna barva
            shape: Ciljna oblika
        """
        color_display = config.COLOR_DISPLAY_NAMES.get(color, color)
        shape_display = config.SHAPE_DISPLAY_NAMES.get(shape, shape)

        print("=" * 50)
        print(f"  DEMO: Iščem {color_display} {shape_display}")
        print("=" * 50)
        print("")

        success = self.navigator.navigate_to_object(
            target_color=color,
            target_shape=shape,
        )

        if success:
            print(f"\n[DEMO] USPEH! {color_display} {shape_display} dosežen.")
        else:
            print(f"\n[DEMO] NEUSPEH. {color_display} {shape_display} ni najden.")

    def shutdown(self):
        """Varno zaustavi robota in počisti vse module."""
        print("")
        print("Zaustavljam robota...")
        self._running = False
        self.navigator.stop()
        if self._nav_thread and self._nav_thread.is_alive():
            self._nav_thread.join(timeout=2)
        self.motors.cleanup()
        self.camera.cleanup()
        self.sensor.cleanup()
        print("Robot zaustavljen. Nasvidenje!")


def main():
    """Vstopna točka programa."""
    robot = Robot()

    # Nastavi signal handler za Ctrl+C
    def signal_handler(sig, frame):
        robot.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        if "--test" in sys.argv:
            robot.run_keyboard()
        elif "--voice" in sys.argv:
            robot.run()
        elif "--demo" in sys.argv:
            # Preveri ali so podani argumenti za demo
            color = "rdeca"
            shape = "kvadrat"
            for i, arg in enumerate(sys.argv):
                if arg == "--color" and i + 1 < len(sys.argv):
                    color_input = sys.argv[i + 1]
                    if color_input in config.COLOR_NAME_MAP:
                        color = config.COLOR_NAME_MAP[color_input]
                if arg == "--shape" and i + 1 < len(sys.argv):
                    shape_input = sys.argv[i + 1]
                    if shape_input in config.SHAPE_NAME_MAP:
                        shape = config.SHAPE_NAME_MAP[shape_input]
            robot.run_demo(color, shape)
        else:
            robot.run_hybrid()
    finally:
        robot.shutdown()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Glavni program za Robot projekt.
Zaključna naloga - Raspberry Pi 5

Uporaba:
    python3 main.py              # Normalen zagon (glasovni ukazi)
    python3 main.py --test       # Testni način (tipkovnica)
    python3 main.py --demo       # Demo: najdi rdečo kocko

Podprti glasovni ukazi:
    SL: "najdi rdečo kocko", "najdi modri trikotnik", "ustavi"
    EN: "find red cube", "find blue triangle", "stop"
"""

import sys
import signal
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
        print("")
        print("Vsi moduli inicializirani. Robot pripravljen.")
        print("")

    def _handle_command(self, command):
        """
        Obdela glasovni ukaz.

        Args:
            command: Command objekt iz speech recognition modula.
        """
        if command.action == "ustavi":
            print("[ROBOT] Ukaz: USTAVI")
            self.navigator.stop()
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

            # Zaženi navigacijo
            success = self.navigator.navigate_to_object(
                target_color=command.color,
                target_shape=command.shape,
            )

            if success:
                print("")
                print(f"[ROBOT] USPEH! {color_display}{shape_display} "
                      f"dosežen in dotaknjen.")
            else:
                print("")
                print(f"[ROBOT] NEUSPEH. {color_display}{shape_display} "
                      f"ni bil najden.")

            print("")
            print("Čakam na naslednji ukaz...")
            print("")
        else:
            print(f"[ROBOT] Nerazumljen ukaz: '{command.raw_text}'")
            print("        Podprti ukazi: 'najdi [barva] [oblika]', 'ustavi'")

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
        print("")

        while self._running:
            try:
                text = input("[VNOS] > ").strip()
                if not text:
                    continue
                if text.lower() in ("q", "quit", "exit"):
                    break

                # Ročno parsaj ukaz
                command = self.speech._parse_command(text)
                print(f"  Parsano: {command}")
                self._handle_command(command)

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
            robot.run()
    finally:
        robot.shutdown()


if __name__ == "__main__":
    main()

"""
Navigacijska logika robota.
Poveže kamero, motorje in ultrasonični senzor za avtonomno
premikanje do ciljnega objekta.

Algoritem:
1. Poišči objekt s kamero (barva + oblika)
2. Če ni viden → obrni se in išči
3. Če je levo/desno → korigiraj smer (P-regulator)
4. Če je v sredini → vozi naprej
5. Preverjaj razdaljo → ko je blizu, ustavi
"""

import time
import config
from motor_control import MotorController
from camera_vision import CameraVision
from ultrasonic_sensor import UltrasonicSensor


class Navigator:
    """Avtonomna navigacija robota do ciljnega objekta."""

    def __init__(self, motors, camera, sensor, led=None):
        """
        Args:
            motors: MotorController instanca
            camera: CameraVision instanca
            sensor: UltrasonicSensor instanca
            led: LEDController instanca (opcijsko)
        """
        self.motors = motors
        self.camera = camera
        self.sensor = sensor
        self.led = led
        self._running = False

    def _search_for_object(self, target_color, target_shape):
        """
        Išče objekt z obračanjem na mestu.
        Vrne True če je objekt najden, False če ni.
        """
        print("[NAV] Iščem objekt... Obračam se.")

        for i in range(config.MAX_SEARCH_ROTATIONS):
            # Preveri kamero
            obj = self.camera.find_object(target_color, target_shape)
            if obj is not None:
                print(f"[NAV] Objekt najden! {obj}")
                return True

            if not self._running:
                return False

            # Obrni se malo v desno
            self.motors.turn_right(config.TURN_SPEED)
            time.sleep(config.SEARCH_TURN_DURATION)
            self.motors.stop()
            time.sleep(0.1)  # Kratka pavza za stabilizacijo slike

        print("[NAV] Objekt ni najden po polnem obratu.")
        return False

    def _approach_object(self, target_color, target_shape):
        """
        Približa se objektu z uporabo P-regulatorja.
        Vrne True če je dosegel objekt, False če ga je izgubil.
        """
        print("[NAV] Približujem se objektu...")

        lost_count = 0
        max_lost = 30  # Koliko zaporednih okvirjev brez objekta toleriramo

        while self._running:
            # Preveri razdaljo
            distance = self.sensor.get_distance()
            if distance is not None:
                print(f"[NAV] Razdalja: {distance} cm")
                if distance <= config.TARGET_DISTANCE_CM:
                    self.motors.stop()
                    print("[NAV] CILJ DOSEŽEN! Objekt dotaknjen/potisnjen.")
                    return True

            # Poišči objekt
            obj = self.camera.find_object(target_color, target_shape)

            if obj is None:
                lost_count += 1
                if lost_count >= max_lost:
                    self.motors.stop()
                    print("[NAV] Objekt izgubljen!")
                    return False
                # Vozi počasi naprej še malo
                self.motors.forward(config.SLOW_SPEED)
                time.sleep(0.05)
                continue

            lost_count = 0
            offset = obj.offset_from_center  # -1.0 do 1.0

            # P-regulator za krmiljenje
            # Osnovna hitrost + korekcija
            base_speed = config.MOTOR_SPEED

            # Zmanjšaj hitrost ko smo blizu
            if distance is not None and distance < 20:
                base_speed = config.SLOW_SPEED

            correction = config.KP_STEERING * offset * base_speed
            left_speed = base_speed + correction
            right_speed = base_speed - correction

            # Omeji hitrosti
            left_speed = max(-100, min(100, left_speed))
            right_speed = max(-100, min(100, right_speed))

            self.motors.steer(left_speed, right_speed)
            time.sleep(0.05)  # 20 Hz regulacijska zanka

        self.motors.stop()
        return False

    def navigate_to_object(self, target_color, target_shape=None):
        """
        Glavni navigacijski algoritem.
        Poišče objekt in se premakne do njega.

        Args:
            target_color: Ime barve (npr. "rdeca")
            target_shape: Ime oblike (npr. "trikotnik") ali None za karkoli

        Returns:
            True če je dosegel objekt, False sicer.
        """
        self._running = True
        if self.led:
            self.led.searching_on()

        color_display = config.COLOR_DISPLAY_NAMES.get(target_color, target_color)
        shape_display = ""
        if target_shape:
            shape_display = " " + config.SHAPE_DISPLAY_NAMES.get(target_shape, target_shape)
        print(f"[NAV] Cilj: {color_display}{shape_display}")

        # 1. Najprej preveri ali objekt že vidi
        obj = self.camera.find_object(target_color, target_shape)

        if obj is None:
            # 2. Išči z obračanjem
            found = self._search_for_object(target_color, target_shape)
            if not found:
                print("[NAV] Ne najdem objekta. Nalogo prekinjam.")
                self.motors.stop()
                return False

        # 3. Približaj se objektu
        success = self._approach_object(target_color, target_shape)

        self.motors.stop()
        if self.led:
            self.led.searching_off()
        return success

    def stop(self):
        """Ustavi navigacijo."""
        self._running = False
        self.motors.stop()
        if self.led:
            self.led.searching_off()
        print("[NAV] Navigacija ustavljena.")


# ============================================================
# Test navigacije (zaženi z: python3 navigation.py)
# ============================================================
if __name__ == "__main__":
    print("=== Test navigacije ===")
    print("Robot bo iskal rdečo kocko.")
    print("Pritisni Ctrl+C za ustavitev.")
    print("")

    motors = MotorController()
    camera = CameraVision()
    sensor = UltrasonicSensor()
    nav = Navigator(motors, camera, sensor)

    try:
        success = nav.navigate_to_object(
            target_color="rdeca",
            target_shape="kvadrat"
        )
        if success:
            print("=== Uspeh! Objekt dosežen. ===")
        else:
            print("=== Neuspeh. Objekt ni bil najden. ===")

    except KeyboardInterrupt:
        print("\nPrekinjen s Ctrl+C")
    finally:
        nav.stop()
        motors.cleanup()
        camera.cleanup()
        sensor.cleanup()

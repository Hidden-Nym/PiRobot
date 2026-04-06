"""
Merjenje razdalje z ultrasoničnim senzorjem HC-SR04.
Uporablja lgpio knjižnico za Raspberry Pi 5.

POMEMBNO: ECHO pin mora imeti napetostni delilnik (5V → 3.3V)!
Uporabi dva upora: 1kΩ in 2kΩ.
  ECHO ---[1kΩ]---+---[2kΩ]--- GND
                   |
                GPIO pin
"""

import time
import lgpio
import config


class UltrasonicSensor:
    """Meri razdaljo z ultrasoničnim senzorjem HC-SR04."""

    def __init__(self):
        """Inicializira TRIG (izhod) in ECHO (vhod) pine."""
        self.chip = lgpio.gpiochip_open(0)

        lgpio.gpio_claim_output(self.chip, config.ULTRASONIC_TRIG, 0)
        lgpio.gpio_claim_input(self.chip, config.ULTRASONIC_ECHO)

        # Počakaj da se senzor stabilizira
        time.sleep(0.1)
        print("[SENZOR] Ultrasonični senzor inicializiran.")

    def _single_measurement(self):
        """
        Izvede eno meritev razdalje.
        Vrne razdaljo v centimetrih ali None če meritev ni uspela.
        """
        # Pošlji 10µs trigger pulz
        lgpio.gpio_write(self.chip, config.ULTRASONIC_TRIG, 0)
        time.sleep(0.002)
        lgpio.gpio_write(self.chip, config.ULTRASONIC_TRIG, 1)
        time.sleep(0.00001)  # 10 mikrosekund
        lgpio.gpio_write(self.chip, config.ULTRASONIC_TRIG, 0)

        # Čakaj na začetek ECHO signala (prehod na HIGH)
        timeout_start = time.time()
        while lgpio.gpio_read(self.chip, config.ULTRASONIC_ECHO) == 0:
            if time.time() - timeout_start > config.ULTRASONIC_TIMEOUT:
                return None  # Timeout
        pulse_start = time.time()

        # Čakaj na konec ECHO signala (prehod na LOW)
        timeout_start = time.time()
        while lgpio.gpio_read(self.chip, config.ULTRASONIC_ECHO) == 1:
            if time.time() - timeout_start > config.ULTRASONIC_TIMEOUT:
                return None  # Timeout
        pulse_end = time.time()

        # Izračunaj razdaljo
        # Zvok potuje 343 m/s, razdalja = čas * hitrost / 2 (tja in nazaj)
        pulse_duration = pulse_end - pulse_start
        distance_cm = (pulse_duration * 34300) / 2

        # Filtriraj nerealne meritve
        if distance_cm < 2 or distance_cm > 400:
            return None

        return round(distance_cm, 1)

    def get_distance(self):
        """
        Izmeri razdaljo s povprečenjem več meritev.
        Vrne razdaljo v cm ali None če meritev ni uspela.
        """
        measurements = []

        for _ in range(config.ULTRASONIC_NUM_SAMPLES):
            dist = self._single_measurement()
            if dist is not None:
                measurements.append(dist)
            time.sleep(config.ULTRASONIC_SAMPLE_DELAY)

        if not measurements:
            return None

        # Vrni povprečje veljavnih meritev
        return round(sum(measurements) / len(measurements), 1)

    def cleanup(self):
        """Počisti GPIO pine."""
        lgpio.gpiochip_close(self.chip)
        print("[SENZOR] GPIO počiščen.")


# ============================================================
# Test senzorja (zaženi z: python3 ultrasonic_sensor.py)
# ============================================================
if __name__ == "__main__":
    print("=== Test ultrasoničnega senzorja ===")
    print("Pritisni Ctrl+C za izhod.")
    print("")

    sensor = UltrasonicSensor()

    try:
        while True:
            distance = sensor.get_distance()
            if distance is not None:
                print(f"Razdalja: {distance} cm")
            else:
                print("Razdalja: meritev ni uspela")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nPrekinjen s Ctrl+C")
    finally:
        sensor.cleanup()
#test commit
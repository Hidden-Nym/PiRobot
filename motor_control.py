"""
Krmiljenje motorjev preko L298N motor driverja.
Uporablja lgpio knjižnico, ki je podprta na Raspberry Pi 5.
"""

import time
import lgpio
import config


class MotorController:
    """Krmili dva DC motorja preko L298N H-bridge driverja."""

    def __init__(self):
        """Inicializira GPIO pine in PWM za motorje."""
        self.chip = lgpio.gpiochip_open(0)

        # Nastavi smerne pine kot izhode
        for pin in [config.MOTOR_IN1, config.MOTOR_IN2,
                     config.MOTOR_IN3, config.MOTOR_IN4]:
            lgpio.gpio_claim_output(self.chip, pin, 0)

        # Nastavi PWM pine za hitrost
        lgpio.gpio_claim_output(self.chip, config.MOTOR_ENA, 0)
        lgpio.gpio_claim_output(self.chip, config.MOTOR_ENB, 0)

        self._speed = config.MOTOR_SPEED
        print("[MOTORJI] Inicializirani.")

    def _set_pwm(self, pin, duty_cycle):
        """Nastavi PWM na pinu z dano dutycycle (0-100)."""
        duty_cycle = max(0, min(100, int(duty_cycle)))
        lgpio.tx_pwm(self.chip, pin, config.PWM_FREQUENCY, duty_cycle)

    def _set_left_motor(self, forward=True):
        """Nastavi smer levega motorja."""
        if forward:
            lgpio.gpio_write(self.chip, config.MOTOR_IN1, 1)
            lgpio.gpio_write(self.chip, config.MOTOR_IN2, 0)
        else:
            lgpio.gpio_write(self.chip, config.MOTOR_IN1, 0)
            lgpio.gpio_write(self.chip, config.MOTOR_IN2, 1)

    def _set_right_motor(self, forward=True):
        """Nastavi smer desnega motorja."""
        if forward:
            lgpio.gpio_write(self.chip, config.MOTOR_IN3, 1)
            lgpio.gpio_write(self.chip, config.MOTOR_IN4, 0)
        else:
            lgpio.gpio_write(self.chip, config.MOTOR_IN3, 0)
            lgpio.gpio_write(self.chip, config.MOTOR_IN4, 1)

    def set_speed(self, speed):
        """Nastavi hitrost motorjev (0-100%)."""
        self._speed = max(0, min(100, speed))

    def forward(self, speed=None):
        """Vozi naravnost naprej."""
        s = speed if speed is not None else self._speed
        self._set_left_motor(forward=True)
        self._set_right_motor(forward=True)
        self._set_pwm(config.MOTOR_ENA, s)
        self._set_pwm(config.MOTOR_ENB, s)

    def backward(self, speed=None):
        """Vozi naravnost nazaj."""
        s = speed if speed is not None else self._speed
        self._set_left_motor(forward=False)
        self._set_right_motor(forward=False)
        self._set_pwm(config.MOTOR_ENA, s)
        self._set_pwm(config.MOTOR_ENB, s)

    def turn_left(self, speed=None):
        """Zavij levo (levi motor nazaj, desni naprej)."""
        s = speed if speed is not None else config.TURN_SPEED
        self._set_left_motor(forward=False)
        self._set_right_motor(forward=True)
        self._set_pwm(config.MOTOR_ENA, s)
        self._set_pwm(config.MOTOR_ENB, s)

    def turn_right(self, speed=None):
        """Zavij desno (levi motor naprej, desni nazaj)."""
        s = speed if speed is not None else config.TURN_SPEED
        self._set_left_motor(forward=True)
        self._set_right_motor(forward=False)
        self._set_pwm(config.MOTOR_ENA, s)
        self._set_pwm(config.MOTOR_ENB, s)

    def steer(self, left_speed, right_speed):
        """
        Krmili motorja z različnima hitrostma za proporcionalno krmiljenje.
        Pozitivne vrednosti = naprej, negativne = nazaj.
        """
        # Levi motor
        if left_speed >= 0:
            self._set_left_motor(forward=True)
            self._set_pwm(config.MOTOR_ENA, min(100, abs(left_speed)))
        else:
            self._set_left_motor(forward=False)
            self._set_pwm(config.MOTOR_ENA, min(100, abs(left_speed)))

        # Desni motor
        if right_speed >= 0:
            self._set_right_motor(forward=True)
            self._set_pwm(config.MOTOR_ENB, min(100, abs(right_speed)))
        else:
            self._set_right_motor(forward=False)
            self._set_pwm(config.MOTOR_ENB, min(100, abs(right_speed)))

    def stop(self):
        """Ustavi oba motorja."""
        lgpio.gpio_write(self.chip, config.MOTOR_IN1, 0)
        lgpio.gpio_write(self.chip, config.MOTOR_IN2, 0)
        lgpio.gpio_write(self.chip, config.MOTOR_IN3, 0)
        lgpio.gpio_write(self.chip, config.MOTOR_IN4, 0)
        self._set_pwm(config.MOTOR_ENA, 0)
        self._set_pwm(config.MOTOR_ENB, 0)

    def cleanup(self):
        """Počisti GPIO pine."""
        self.stop()
        lgpio.gpiochip_close(self.chip)
        print("[MOTORJI] GPIO počiščen.")


# ============================================================
# Test motorjev (zaženi z: python3 motor_control.py)
# ============================================================
if __name__ == "__main__":
    print("=== Test motorjev ===")
    motors = MotorController()

    try:
        print("Naprej (2s)...")
        motors.forward()
        time.sleep(2)

        print("Ustavi (1s)...")
        motors.stop()
        time.sleep(1)

        print("Nazaj (2s)...")
        motors.backward()
        time.sleep(2)

        print("Ustavi (1s)...")
        motors.stop()
        time.sleep(1)

        print("Levo (1s)...")
        motors.turn_left()
        time.sleep(1)

        print("Ustavi (1s)...")
        motors.stop()
        time.sleep(1)

        print("Desno (1s)...")
        motors.turn_right()
        time.sleep(1)

        print("Ustavi.")
        motors.stop()
        print("=== Test končan ===")

    except KeyboardInterrupt:
        print("\nPrekinjen s Ctrl+C")
    finally:
        motors.cleanup()

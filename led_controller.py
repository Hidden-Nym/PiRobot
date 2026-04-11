"""
Krmiljenje LED indikatorjev stanja robota.

LED_LISTENING (pin 25): sveti ko robot posluša glasovni ukaz
LED_SEARCHING (pin 26): sveti ko robot išče/navigira do objekta
"""

import lgpio
import config


class LEDController:
    """Krmili dve LED diodi za vizualni prikaz stanja robota."""

    def __init__(self):
        """Inicializira GPIO pine za LED."""
        self._chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self._chip, config.LED_LISTENING, 0)
        lgpio.gpio_claim_output(self._chip, config.LED_SEARCHING, 0)
        print("[LED] Inicializirani.")

    def listening_on(self):
        """Prižgi LED za poslušanje."""
        lgpio.gpio_write(self._chip, config.LED_LISTENING, 1)

    def listening_off(self):
        """Ugasni LED za poslušanje."""
        lgpio.gpio_write(self._chip, config.LED_LISTENING, 0)

    def searching_on(self):
        """Prižgi LED za iskanje."""
        lgpio.gpio_write(self._chip, config.LED_SEARCHING, 1)

    def searching_off(self):
        """Ugasni LED za iskanje."""
        lgpio.gpio_write(self._chip, config.LED_SEARCHING, 0)

    def all_off(self):
        """Ugasni obe LED."""
        lgpio.gpio_write(self._chip, config.LED_LISTENING, 0)
        lgpio.gpio_write(self._chip, config.LED_SEARCHING, 0)

    def cleanup(self):
        """Ugasni LED in počisti GPIO."""
        self.all_off()
        lgpio.gpiochip_close(self._chip)
        print("[LED] GPIO počiščen.")

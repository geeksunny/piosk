from enum import StrEnum, Enum
from pathlib import Path

from gpiozero import LightSensor

from kiosk_gpio.config import CONFIG
from kiosk_gpio.led import LedInstructionProvidingThread


class Brightness(Enum):
    ON = 0
    OFF = 1
    MAX = CONFIG['brightness']['AUTO_MAXIMUM']
    MIN = CONFIG['brightness']['AUTO_MINIMUM']


class Backlight(StrEnum):
    DEFAULT = "rpi_backlight"
    RPI_0 = "10-0045"
    RPI5_0 = "4-0045"
    RPI5_1 = "6-0045"

    @property
    def path(self) -> Path:
        return Path('/sys/class/backlight/', str(self.value))

    @property
    def brightness(self) -> Path:
        return self.path / 'brightness'

    @property
    def power(self) -> Path:
        return self.path / 'bl_power'


class BrightnessControlThread(LedInstructionProvidingThread):

    def __init__(self):
        super(BrightnessControlThread, self).__init__()
        self._gpio_lightsensor = LightSensor(CONFIG['PIN_LIGHTSENSOR'])
        self._

    def run(self):
        while True:

        pass
        # TODO: auto brightness, monitor lightsensor reading and change backlight level accordingly.
        # TODO: manual brightness, cycle through steps
        # TODO: Double click button to swap between modes.
        #  manual mode: Fade LED down with brightness down steps. step on each click.
        #    Step count and values can be declared in config file.
        #  auto mode: Quick pulse of LED when activated.
        #  mode / value change: LED turns on to the representing state for 1 second.
        #    (customized in config?)


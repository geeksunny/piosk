from enum import StrEnum, Enum
from pathlib import Path
from threading import Event

from gpiozero import LightSensor

from kiosk_gpio.config import CONFIG
from kiosk_gpio.led import LedInstructionProvidingThread


class Brightness(Enum):
    ON = 0
    OFF = 1
    MAX = CONFIG['brightness']['AUTO_MAXIMUM']
    MIN = CONFIG['brightness']['AUTO_MINIMUM']


def _read_value(path: Path):
    with path.open('r') as f:
        return f.read()


def _write_value(path: Path, value):
    with path.open('w') as f:
        f.write(str(value))


class Backlight(StrEnum):
    DEFAULT = "rpi_backlight"
    RPI_0 = "10-0045"
    RPI5_0 = "4-0045"
    RPI5_1 = "6-0045"

    @classmethod
    def detect_backlight(cls):
        items: list[Backlight] = list(map(lambda c: c.value, cls))
        for item in items:
            if item.path.exists():
                return item
        raise RuntimeError("Could not determine backlight type.")

    @property
    def path(self) -> Path:
        return Path('/sys/class/backlight/', str(self.value))

    @property
    def brightness(self) -> Path:
        return self.path / 'brightness'

    @property
    def brightness_value(self) -> int:
        return int(_read_value(self.brightness))

    @brightness_value.setter
    def brightness_value(self, value):
        _write_value(self.brightness, value)

    @property
    def power(self) -> Path:
        return self.path / 'bl_power'

    @property
    def power_value(self) -> Brightness:
        return Brightness.ON if int(_read_value(self.power)) == Brightness.ON else Brightness.OFF

    @power_value.setter
    def power_value(self, value):
        _write_value(self.power, value)


GPIO_LIGHTSENSOR = LightSensor(CONFIG['PIN_LIGHTSENSOR'])


class AutoBrightnessThread(LedInstructionProvidingThread):

    def __init__(self, event: Event):
        super(AutoBrightnessThread, self).__init__()
        self._event = event
        self._backlight = Backlight.detect_backlight()
        self._brightness_value = self._backlight.brightness_value

        self._sensor_reading = 0.0
        self._auto_range = CONFIG['brightness']['AUTO_MAXIMUM'] - CONFIG['brightness']['AUTO_MINIMUM']
        self._auto_minimum = CONFIG['brightness']['AUTO_MINIMUM']
        self._auto_step = self._auto_range / CONFIG['brightness']['AUTO_STEP_COUNT']

    def _set_brightness(self, brightness_value: float):
        if brightness_value is not None and self._brightness_value != brightness_value:
            self._brightness_value = self._backlight.brightness_value = brightness_value

    def get_auto_brightness(self) -> float | None:
        sensor_reading = GPIO_LIGHTSENSOR.value
        if self._sensor_reading == sensor_reading:
            return None
        self._sensor_reading = sensor_reading
        new_brightness = self._auto_range * sensor_reading
        # Adjust value to the nearest multiple of `self._auto_step.
        new_brightness = self._auto_step * round(new_brightness / self._auto_step)
        return new_brightness + self._auto_minimum

    def run(self):
        while True:
            self._set_brightness(self.get_auto_brightness())
            self._event.wait(CONFIG['brightness']['POLL_TIME_SECONDS'])
            if self._event.is_set() is True:
                break



THREAD_AUTO_BRIGHTNESS: AutoBrightnessThread = AutoBrightnessThread()
THREAD_EVENT: Event = Event()


def start_auto_brightness():
    global THREAD_AUTO_BRIGHTNESS
    if THREAD_AUTO_BRIGHTNESS is None or not THREAD_AUTO_BRIGHTNESS.is_alive():
        THREAD_AUTO_BRIGHTNESS = AutoBrightnessThread(THREAD_EVENT)
        THREAD_AUTO_BRIGHTNESS.start()


def stop_auto_brightness():
    THREAD_EVENT.set()

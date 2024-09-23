import time
from enum import StrEnum, Enum
from pathlib import Path
from threading import Event, Lock

from easing_functions.easing import EasingBase, LinearInOut
from gpiozero import LightSensor

from piosk.config import CONFIG
from piosk.led import LedInstructionProvidingThread
from piosk.motion import wake_motion_sensor


class Brightness(Enum):
    ON = 0
    OFF = 1


def _read_value(path: Path):
    with path.open('r') as f:
        return f.read()


def _write_value(path: Path, value):
    with path.open('w') as f:
        f.write(str(value))


__current_brightness = -1


class Backlight(StrEnum):
    DEFAULT = "rpi_backlight"
    RPI_0 = "10-0045"
    RPI5_0 = "4-0045"
    RPI5_1 = "6-0045"

    @classmethod
    def detect_backlight(cls):
        items: list[Backlight] = list(map(lambda c: c, cls))
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
        global __current_brightness
        __current_brightness = int(_read_value(self.brightness))
        return __current_brightness

    @brightness_value.setter
    def brightness_value(self, value: int):
        global __current_brightness
        if isinstance(value, int) and 0 <= value <= 255 and value != __current_brightness:
            _write_value(self.brightness, value)
            __current_brightness = value

    def set_brightness_smoothed(self, value: int, ease_cls: type[EasingBase]):
        # TODO: Should this have a background option?
        current_value = self.brightness_value
        easing = ease_cls(current_value, value, CONFIG['brightness']['SMOOTH_DURATION_SECONDS'])
        delay = CONFIG['brightness']['SMOOTH_DURATION_SECONDS'] / CONFIG['brightness']['SMOOTH_FPS']
        frame_count = CONFIG['brightness']['SMOOTH_DURATION_SECONDS'] * CONFIG['brightness']['SMOOTH_FPS']
        global __current_brightness
        for i in range(frame_count):
            val = easing(i)
            if __current_brightness != val:
                self.brightness_value = val
            time.sleep(delay)

    @property
    def power(self) -> Path:
        return self.path / 'bl_power'

    @property
    def power_value(self) -> Brightness:
        return Brightness.ON if int(_read_value(self.power)) == Brightness.ON else Brightness.OFF

    @power_value.setter
    def power_value(self, value):
        _write_value(self.power, value)


_BACKLIGHT = Backlight.detect_backlight()
_BACKLIGHT_LOCK = Lock()
GPIO_LIGHTSENSOR = LightSensor(CONFIG['PIN_LIGHTSENSOR'])


class AutoBrightnessThread(LedInstructionProvidingThread):

    def __init__(self, event: Event):
        super(AutoBrightnessThread, self).__init__()
        self._event = event
        with _BACKLIGHT_LOCK:
            self._brightness_value = _BACKLIGHT.brightness_value
        self._sensor_reading = -1.0
        self._smooth = CONFIG['brightness']['SMOOTH']
        self._auto_range = CONFIG['brightness']['AUTO_MAXIMUM'] - CONFIG['brightness']['AUTO_MINIMUM']
        self._auto_minimum = CONFIG['brightness']['AUTO_MINIMUM']
        self._auto_step = self._auto_range / CONFIG['brightness']['AUTO_STEP_COUNT']

    def _set_brightness(self, brightness_value: float):
        if brightness_value is not None and self._brightness_value != brightness_value:
            with _BACKLIGHT_LOCK:
                self._brightness_value = int(round(brightness_value))
                if self._smooth is True:
                    # TODO: Make the easing method configurable
                    _BACKLIGHT.set_brightness_smoothed(self._brightness_value, LinearInOut)
                self._brightness_value = _BACKLIGHT.brightness_value = brightness_value

    def get_auto_brightness(self) -> float | None:
        sensor_reading = GPIO_LIGHTSENSOR.value
        if self._sensor_reading == sensor_reading:
            return None
        self._sensor_reading = sensor_reading
        new_brightness = self._auto_range * sensor_reading
        # Adjust value to the nearest multiple of `self._auto_step.`
        new_brightness = self._auto_step * round(new_brightness / self._auto_step)
        return round(new_brightness + self._auto_minimum)

    def run(self):
        while True:
            self._set_brightness(self.get_auto_brightness())
            self._event.wait(CONFIG['brightness']['POLL_TIME_SECONDS'])
            if self._event.is_set() is True:
                break

        # TODO: auto brightness, monitor lightsensor reading and change backlight level accordingly.
        # TODO: manual brightness, cycle through steps
        # TODO: Double click button to swap between modes.
        #  manual mode: Fade LED down with brightness down steps. step on each click.
        #    Step count and values can be declared in config file.
        #  auto mode: Quick pulse of LED when activated.
        #  mode / value change: LED turns on to the representing state for 1 second.
        #    (customized in config?)


_THREAD_EVENT: Event = Event()
_THREAD_AUTO_BRIGHTNESS: AutoBrightnessThread = AutoBrightnessThread(_THREAD_EVENT)


def start_auto_brightness():
    global _THREAD_AUTO_BRIGHTNESS
    if _THREAD_AUTO_BRIGHTNESS is None or not _THREAD_AUTO_BRIGHTNESS.is_alive():
        _THREAD_AUTO_BRIGHTNESS = AutoBrightnessThread(_THREAD_EVENT)
        _THREAD_AUTO_BRIGHTNESS.start()


def stop_auto_brightness():
    _THREAD_EVENT.set()


def set_manual_brightness(val: int, smooth: bool = False, ease_cls: type[EasingBase] = LinearInOut):
    with _BACKLIGHT_LOCK:
        if smooth is True:
                _BACKLIGHT.set_brightness_smoothed(val, ease_cls)
        else:
            _BACKLIGHT.brightness_value = val


def set_screen_power(state: Brightness):
    with _BACKLIGHT_LOCK:
        _BACKLIGHT.power_value = state


def turn_screen_on():
    with _BACKLIGHT_LOCK:
        _BACKLIGHT.power_value = Brightness.ON


def turn_screen_off():
    with _BACKLIGHT_LOCK:
        _BACKLIGHT.power_value = Brightness.OFF
    wake_motion_sensor()


__manual_step_index: int = 0
__manual_steps: list[int] = CONFIG['brightness']['MANUAL_STEPS']


def set_next_manual_step(smooth: bool = False):
    global __manual_step_index
    with _BACKLIGHT_LOCK:
        __manual_step_index += 1
        if __manual_step_index >= len(__manual_steps):
            __manual_step_index = 0
        if smooth is True:
            _BACKLIGHT.set_brightness_smoothed(__manual_steps[__manual_step_index], LinearInOut)
        else:
            _BACKLIGHT.brightness_value = __manual_steps[__manual_step_index]

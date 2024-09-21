import subprocess
from enum import Enum

from kiosk_gpio.brightness import Brightness, set_screen_power
from kiosk_gpio.led import LedInstructionProvidingThread
from kiosk_gpio.util import log


class ScreensaverEvent(Enum):
    NONE = 0
    ACTIVATED = 1
    DEACTIVATED = 2


class ScreensaverThread(LedInstructionProvidingThread):

    def run(self):
        process = subprocess.Popen(["xscreensaver-command", "--watch"], stdout=subprocess.PIPE)
        while process.poll() is None:
            line = process.stdout.readline()
            result = self.process_event(line.decode("utf-8"))
            if result is ScreensaverEvent.ACTIVATED:
                log("Screensaver activated. Turn LED on.")
                self._led_on()
                set_screen_power(Brightness.OFF)
            elif result is ScreensaverEvent.DEACTIVATED:
                log("Screensaver deactivated. Turn LED off.")
                self._led_off()
                set_screen_power(Brightness.ON)
            else:
                pass  # Nothing to do here.

    def process_event(self, text: str) -> ScreensaverEvent:
        return ScreensaverEvent.DEACTIVATED if text.find("UNBLANK") > -1 \
            else ScreensaverEvent.ACTIVATED if text.find("BLANK") > -1 \
            else ScreensaverEvent.NONE

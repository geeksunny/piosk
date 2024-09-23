import subprocess
from enum import Enum

from kiosk_gpio.brightness import turn_screen_off, turn_screen_on
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
                turn_screen_off()
            elif result is ScreensaverEvent.DEACTIVATED:
                log("Screensaver deactivated. Turn LED off.")
                self._led_off()
                turn_screen_on()
            else:
                pass  # Nothing to do here.

    def process_event(self, text: str) -> ScreensaverEvent:
        return ScreensaverEvent.DEACTIVATED if text.find("UNBLANK") > -1 \
            else ScreensaverEvent.ACTIVATED if text.find("BLANK") > -1 \
            else ScreensaverEvent.NONE


_SCREENSAVER_THREAD: ScreensaverThread


def start_screensaver_thread():
    _SCREENSAVER_THREAD = ScreensaverThread()
    _SCREENSAVER_THREAD.start()


def join_screensaver_thread():
    _SCREENSAVER_THREAD.join()

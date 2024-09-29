import subprocess
import time
from enum import Enum

from piosk.brightness import turn_screen_off, turn_screen_on
from piosk.config import CONFIG
from piosk.led import LedInstructionProvidingThread
from piosk.util import log


class ScreensaverEvent(Enum):
    NONE = 0
    ACTIVATED = 1
    DEACTIVATED = 2


class ScreensaverThread(LedInstructionProvidingThread):

    def run(self):
        process = subprocess.Popen(
            ["xscreensaver-command", "--display",
             CONFIG['screensaver']['DISPLAY'], "--watch"],
            stdout=subprocess.PIPE
        )
        while process.poll() is None:
            line = process.stdout.readline()
            result = self.process_event(line.decode("utf-8"))
            if result is ScreensaverEvent.ACTIVATED:
                log("Screensaver activated. Turn LED on.")
                self._led_on()
                # TODO: Parse screen fade value from .xscreensaver config file. Use for power-off delay for fade.
                #  (Add 0.5 seconds to delay so fade animation can complete.)
                time.sleep(1.5)
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
    global _SCREENSAVER_THREAD
    _SCREENSAVER_THREAD = ScreensaverThread()
    _SCREENSAVER_THREAD.start()


def join_screensaver_thread():
    global _SCREENSAVER_THREAD
    _SCREENSAVER_THREAD.join()


def activate_screensaver():
    """
    Engage the screensaver and put the display to sleep.
    """
    process = subprocess.Popen(
        ["xscreensaver-command", "--display",
         CONFIG['screensaver']['DISPLAY'], "--activate"],
        stdout=subprocess.PIPE
    )


def deactivate_screensaver():
    """
    Wake the display if the screensaver is activated.
    """
    process = subprocess.Popen(
        ["xscreensaver-command", "--display",
         CONFIG['screensaver']['DISPLAY'], "--deactivate"],
        stdout=subprocess.PIPE
    )

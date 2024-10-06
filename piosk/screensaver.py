import subprocess
import time
from enum import Enum
from threading import Lock

import piosk.brightness
from piosk.config import CONFIG
from piosk.led import LedInstructionProvidingThread
from piosk.util import log


class ScreensaverEvent(Enum):
    NONE = 0
    ACTIVATED = 1
    DEACTIVATED = 2


_CURRENT_STATUS: ScreensaverEvent = ScreensaverEvent.DEACTIVATED
_STATUS_LOCK = Lock()


def update_status(status: ScreensaverEvent):
    global _CURRENT_STATUS
    with _STATUS_LOCK:
        _CURRENT_STATUS = status


class ScreensaverThread(LedInstructionProvidingThread):

    def run(self):
        process = subprocess.Popen(
            ["xscreensaver-command", "--display", CONFIG['screensaver']['DISPLAY'], "--watch"],
            stdout=subprocess.PIPE
        )
        while process.poll() is None:
            line = process.stdout.readline()
            result = self.process_event(line.decode("utf-8"))
            if result is ScreensaverEvent.ACTIVATED:
                log("Screensaver activated. Turn LED on.")
                self._led_on()
                update_status(result)
                # TODO: Parse screen fade value from .xscreensaver config file. Use for power-off delay for fade.
                #  (Add 0.5 seconds to delay so fade animation can complete.)
                time.sleep(1.5)
                piosk.brightness.turn_screen_off()
            elif result is ScreensaverEvent.DEACTIVATED:
                log("Screensaver deactivated. Turn LED off.")
                self._led_off()
                update_status(result)
                piosk.brightness.turn_screen_on()
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


def get_status() -> ScreensaverEvent:
    with _STATUS_LOCK:
        return _CURRENT_STATUS


def activate_screensaver():
    """
    Engage the screensaver and put the display to sleep.
    """
    if get_status() != ScreensaverEvent.ACTIVATED:
        subprocess.Popen(
            ["xscreensaver-command", "--display", CONFIG['screensaver']['DISPLAY'], "--activate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )


def deactivate_screensaver():
    """
    Wake the display if the screensaver is activated.
    """
    # TODO: Should this try to poke the screensaver to reset the idle time?
    #  In case it goes to sleep while pressing buttons.
    if get_status() != ScreensaverEvent.DEACTIVATED:
        subprocess.Popen(
            ["xscreensaver-command", "--display", CONFIG['screensaver']['DISPLAY'], "--deactivate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

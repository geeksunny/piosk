#!/usr/bin/env python
import os
import subprocess
import sys
from datetime import datetime
from enum import Enum
from threading import Thread

from gpiozero import MotionSensor

from kiosk_gpio.button import ButtonThread
from kiosk_gpio.config import CONFIG
from kiosk_gpio.led import LedInstructionProvidingThread


def log(message: str):
    print(f'{datetime.timestamp(datetime.now())} :: {message}')


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
                self._led_on()
                log("Screensaver activated. Turn LED on.")
            elif result is ScreensaverEvent.DEACTIVATED:
                self._led_off()
                log("Screensaver deactivated. Turn LED off.")
            else:
                pass  # Nothing to do here.

    def process_event(self, text: str) -> ScreensaverEvent:
        return ScreensaverEvent.DEACTIVATED if text.find("UNBLANK") > -1 \
            else ScreensaverEvent.ACTIVATED if text.find("BLANK") > -1 \
            else ScreensaverEvent.NONE


class MotionSensorThread(Thread):

    def __init__(self):
        super(MotionSensorThread, self).__init__()
        self._gpio_motionsensor = MotionSensor(CONFIG['PIN_MOTIONSENSOR'])

    def run(self):
        # TODO: If screen is off and motion sensor picks up activity, wake screen.
        pass


def main():
    ssaver = ScreensaverThread()
    button = ButtonThread()
    # brightness = BrightnessControlThread()
    # motion_sensor = MotionSensorThread()

    ssaver.start()
    button.start()
    # brightness.start()
    # motion_sensor.start()

    ssaver.join()
    button.join()
    # brightness.join()
    # motion_sensor.join()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)

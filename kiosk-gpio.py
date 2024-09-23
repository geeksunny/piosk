#!/usr/bin/env python
import os
import sys
from threading import Thread

from gpiozero import MotionSensor

from kiosk_gpio.button import ButtonThread
from kiosk_gpio.config import CONFIG
from kiosk_gpio.screensaver import ScreensaverThread


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

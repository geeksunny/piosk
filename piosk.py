#!/usr/bin/env python
import os
import sys

from piosk.brightness import start_auto_brightness, turn_screen_on
from piosk.button import start_button_thread, join_button_thread
from piosk.config import CONFIG
from piosk.led import GPIO_LED
from piosk.motion import start_motion_sensor_thread, join_motion_sensor_thread
from piosk.screensaver import start_screensaver_thread, join_screensaver_thread


def main():
    # TODO: LightSensor functionality is broken: https://github.com/gpiozero/gpiozero/issues/1135
    #  Automatic brightness is currently unsupported, untested, and not fully implemented.

    start_screensaver_thread()
    start_button_thread()
    start_motion_sensor_thread()
    if CONFIG['brightness']['AUTO_ENABLED'] is True:
        start_auto_brightness()

    join_screensaver_thread()
    join_button_thread()
    join_motion_sensor_thread()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        turn_screen_on()
        GPIO_LED.off()
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)

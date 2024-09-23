#!/usr/bin/env python
import os
import sys

from piosk.brightness import start_auto_brightness
from piosk.button import start_button_thread, join_button_thread
from piosk.config import CONFIG
from piosk.motion import start_motion_sensor_thread, join_motion_sensor_thread
from piosk.screensaver import start_screensaver_thread, join_screensaver_thread


def main():
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
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)

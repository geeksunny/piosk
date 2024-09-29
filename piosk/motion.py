import time
from threading import Thread, Event

from gpiozero import MotionSensor

from piosk.config import CONFIG
from piosk.screensaver import deactivate_screensaver

_DISPLAY_SLEEPING: bool = False
_MOTION_EVENT: Event = Event()


class MotionSensorThread(Thread):

    def __init__(self, event):
        super(MotionSensorThread, self).__init__()
        self._gpio_motion_sensor = MotionSensor(CONFIG['PIN_MOTIONSENSOR'])
        self._event = event

    def run(self):
        while True:
            # This thread will be awoken when the screen has been turned off.
            self._event.wait()
            time.sleep(15)  # wait a short period before activating the motion sensor.
            self._gpio_motion_sensor.wait_for_active()
            deactivate_screensaver()
            self._event.clear()


_MOTION_THREAD: MotionSensorThread(_MOTION_EVENT)


def start_motion_sensor_thread():
    _MOTION_THREAD = MotionSensorThread(_MOTION_EVENT)
    _MOTION_THREAD.start()


def wake_motion_sensor():
    _MOTION_EVENT.set()


def join_motion_sensor_thread():
    _MOTION_THREAD.join()

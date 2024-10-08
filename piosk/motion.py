import time
from threading import Thread, Event

from gpiozero import MotionSensor

from piosk.config import CONFIG
from piosk.screensaver import deactivate_screensaver
from piosk.util import log

_GPIO_MOTIONSENSOR = MotionSensor(CONFIG['PIN_MOTIONSENSOR'])
_DISPLAY_SLEEPING: bool = False
_MOTION_EVENT: Event = Event()


class MotionSensorThread(Thread):

    def __init__(self, event):
        super(MotionSensorThread, self).__init__()
        self._event = event

    def run(self):
        while True:
            # This thread will be awoken when the screen has been turned off.
            log('Motion sensor sleeping.')
            self._event.wait()
            log(f"Motion sensor will wake up in {CONFIG['motion']['WAKE_DELAY_SECONDS']} seconds.")
            time.sleep(CONFIG['motion']['WAKE_DELAY_SECONDS'])  # wait a short period before activating the motion sensor.
            log('Motion sensor waking up.')
            _GPIO_MOTIONSENSOR.wait_for_active()
            log('Motion sensor detected movement. Waking screen.')
            deactivate_screensaver()
            self._event.clear()


_MOTION_THREAD: MotionSensorThread(_MOTION_EVENT)


def start_motion_sensor_thread():
    log('Starting Motion thread.')
    _MOTION_THREAD = MotionSensorThread(_MOTION_EVENT)
    _MOTION_THREAD.start()


def wake_motion_sensor():
    _MOTION_EVENT.set()


def join_motion_sensor_thread():
    _MOTION_THREAD.join()

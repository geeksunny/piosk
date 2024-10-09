import time
from threading import Thread, Event

from gpiozero import MotionSensor

from piosk.config import CONFIG
from piosk.screensaver import poke_screensaver, get_status, ScreensaverEvent
from piosk.util import log

_GPIO_MOTIONSENSOR = MotionSensor(CONFIG['PIN_MOTIONSENSOR'])
_DISPLAY_SLEEPING: bool = False
_MOTION_SLEEP_EVENT: Event = Event()
_MOTION_CANCEL_EVENT: Event = Event()


class MotionSensorThread(Thread):

    def __init__(self, sleep_event: Event, cancel_event: Event):
        super(MotionSensorThread, self).__init__()
        self._sleep_event = sleep_event
        self._cancel_event = cancel_event

    def run(self):
        while True:
            # This thread will be awoken when the screen has been turned off.
            log('Motion sensor sleeping.')
            self._sleep_event.wait()
            log(f"Motion sensor will wake up in {CONFIG['motion']['WAKE_DELAY_SECONDS']} seconds.")
            self._cancel_event.wait(CONFIG['motion']['WAKE_DELAY_SECONDS'])  # wait a short period before activating the motion sensor.
            if not self._cancel_event.is_set():
                log('Motion sensor waking up.')
                _GPIO_MOTIONSENSOR.wait_for_active()
                log('Motion sensor detected movement. Waking screen.')
                poke_screensaver()
            else:
                log('Screensaver was woken up. Skipping motion monitoring.')
            self._sleep_event.clear()
            self._cancel_event.clear()


_MOTION_THREAD: MotionSensorThread


def start_motion_sensor_thread():
    log('Starting Motion thread.')
    global _MOTION_THREAD
    _MOTION_THREAD = MotionSensorThread(_MOTION_SLEEP_EVENT, _MOTION_CANCEL_EVENT)
    _MOTION_THREAD.start()


def join_motion_sensor_thread():
    _MOTION_THREAD.join()


def wake_motion_sensor():
    _MOTION_SLEEP_EVENT.set()


def cancel_motion_monitoring():
    if _MOTION_SLEEP_EVENT.is_set() and not _MOTION_CANCEL_EVENT.is_set():
        log('Flagging motion thread for cancellation.')
        _MOTION_CANCEL_EVENT.set()


import time
from threading import Thread, Event

from gpiozero import MotionSensor

from kiosk_gpio.brightness import set_screen_power, Brightness
from kiosk_gpio.config import CONFIG


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
            set_screen_power(Brightness.ON)
            self._event.clear()


_MOTION_THREAD: MotionSensorThread(_MOTION_EVENT)


def start_motion_sensor_thread():
    _MOTION_THREAD = MotionSensorThread(_MOTION_EVENT)
    _MOTION_THREAD.start()

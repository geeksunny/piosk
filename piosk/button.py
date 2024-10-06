import time
from threading import Event

from easing_functions import ExponentialEaseIn
from gpiozero import Button

import piosk.screensaver
from piosk.brightness import set_next_manual_step
from piosk.config import CONFIG
from piosk.led import LedInstructionProvidingThread, BlinkSequenceEvent


class ButtonThread(LedInstructionProvidingThread):

    def __init__(self):
        super(ButtonThread, self).__init__()
        self._event = Event()
        self._gpio_button = Button(CONFIG['PIN_BUTTON'])
        self._gpio_button.hold_time = CONFIG['button']['MIN_HOLD_TIME_SECONDS']
        self._hold_start: float | None = None

        def when_pressed():
            self._led_on()
            piosk.screensaver.deactivate_screensaver()

        self._gpio_button.when_pressed = when_pressed

        def when_held():
            self._hold_start = time.time()
            # Begin LED strobe
            events = (BlinkSequenceEvent(1, 0, (1.0 - self._gpio_button.held_time), easing=ExponentialEaseIn),)
            reset = BlinkSequenceEvent(0)
            strobe = BlinkSequenceEvent(1, 0, 1, easing=ExponentialEaseIn)
            for i in range(0, int(round((CONFIG['button']['MAX_HOLD_TIME_SECONDS'] - 1)))):
                events += (reset, strobe)
            self._led_sequence(events, 0)

        self._gpio_button.when_held = when_held

        def when_released():
            self._led_off()
            if self._hold_start is None:
                set_next_manual_step()
            else:
                time_held = time.time() - self._hold_start
                self._hold_start = None
                if time_held < CONFIG['button']['MAX_HOLD_TIME_SECONDS']:
                    print('TODO: Switch between auto and manual brightness modes.')
                else:
                    print(f"TODO: EXECUTE `{CONFIG['shutdown']['SCRIPT_CMD']}`")

        self._gpio_button.when_released = when_released

    def stop(self):
        self._event.set()

    def run(self):
        # Keep thread alive for button callbacks.
        self._event.wait()


_BUTTON_THREAD: ButtonThread


def start_button_thread():
    _BUTTON_THREAD = ButtonThread()
    _BUTTON_THREAD.start()


def join_button_thread():
    _BUTTON_THREAD.join()

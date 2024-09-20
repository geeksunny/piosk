import time

from easing_functions import ExponentialEaseIn
from gpiozero import Button

from kiosk_gpio.brightness import set_next_manual_step
from kiosk_gpio.config import CONFIG
from kiosk_gpio.led import LedInstructionProvidingThread, BlinkSequenceEvent


class ButtonThread(LedInstructionProvidingThread):

    def __init__(self):
        super(ButtonThread, self).__init__()
        self._gpio_button = Button(CONFIG['PIN_BUTTON'])
        self._is_pressed = False
        self._last_state_change = None
        self._is_led_active = False

    def _set_state(self, new_value: bool):
        if self._is_pressed != new_value:
            self._is_pressed = new_value
            self._last_state_change = time.time()

    def _time_held(self):
        return time.time() - self._last_state_change

    def run(self):
        while True:
            if self._is_pressed is False:
                # Check for new press
                if self._gpio_button.is_pressed is True:
                    self._set_state(True)
            else:  # if self.is_pressed is True:
                if self._gpio_button.is_pressed is False:
                    self._led_off()
                    self._is_led_active = False
                    self._set_state(False)
                elif self._is_led_active is not True:
                    if self._time_held() >= CONFIG['button']['MIN_HOLD_TIME_SECONDS']:
                        self._is_led_active = True
                        event = BlinkSequenceEvent(1, 0, 1, easing=ExponentialEaseIn)
                        events = (BlinkSequenceEvent(1, 0, (1.0 - self._time_held()), easing=ExponentialEaseIn),)
                        for i in range(0, CONFIG['button']['MAX_HOLD_TIME_SECONDS'] - 1):
                            events += (event,)
                        self._led_sequence(events, 0)
                    else:
                        self._led_on()
                        set_next_manual_step()
                else:
                    if self._time_held() >= CONFIG['button']['MAX_HOLD_TIME_SECONDS']:
                        self._led_on()
                        print(f'TODO: EXECUTE `{CONFIG['shutdown']['SCRIPT_CMD']}`')

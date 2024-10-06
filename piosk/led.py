from dataclasses import dataclass
from itertools import cycle, chain, repeat
from threading import Thread

from easing_functions.easing import EasingBase, LinearInOut
from gpiozero import PWMLED
from gpiozero.threads import GPIOThread

from .config import CONFIG


@dataclass
class BlinkSequenceEvent:
    value: float
    duration: float = 0.0
    fade_time: float = 0.0
    fps: int = 25
    easing: type[EasingBase] = LinearInOut


class SequencedPWMLED(PWMLED):

    def sequence(self, events: tuple[BlinkSequenceEvent, ...] | BlinkSequenceEvent,
                 initial_value: float | None = None, n: int | None = 1, background: bool = True):
        """
        Perform a sequence of LED value changes. Based on the logic found in PWMOutputDevice.blink().

        :param events: A tuple of BlinkSequenceEvent objects representing the sequence of value changes.
        :param initial_value: Initial value to set LED to before performing any fade actions, or None to use the
                currently set value.
        :param n: Number of times to repeat the sequence, or None to perform indefinitely until another thread
                sets a new value.
        :param background: If true, the sequence will operate in a background thread. If False, the calling thread
                will be blocked.
        """
        self._stop_blink()
        if isinstance(events, BlinkSequenceEvent):
            events = (events,)
        self._blink_thread = GPIOThread(
            self._sequenced_blink_device,
            (events, initial_value, n)
        )
        self._blink_thread.start()
        if not background:
            self._blink_thread.join()
            self._blink_thread = None

    def _sequenced_blink_device(self, events: tuple[BlinkSequenceEvent, ...] | BlinkSequenceEvent,
                                initial_value: float | None = None, n: int | None = 1):
        """
        Perform a sequence of LED value changes. Based on the logic found in PWMOutputDevice._blink_device().

        :param events: A tuple of BlinkSequenceEvent objects representing the sequence of value changes.
        :param initial_value: Initial value to set LED to before performing any fade actions, or None to use the
                currently set value.
        :param n: Number of times to repeat the sequence, or None to perform indefinitely until another thread
                sets a new value.
        """
        if n is not None and n <= 0:
            return
        sequence = []
        prev_value = initial_value if initial_value is not None else self.value
        if isinstance(events, BlinkSequenceEvent):
            events = (events,)
        for event in events:
            value_steps = []
            delay = None
            if event.fade_time > 0 and prev_value != event.value:
                frame_count = int(event.fps * event.fade_time)
                delay = 1 / event.fps
                easing = event.easing(prev_value, event.value, frame_count)
                for i in range(frame_count):
                    value = easing(i)
                    value_steps.append(value)
            sequence.append((delay, value_steps))
            sequence.append((event.duration, (event.value,)))
            prev_value = event.value
        sequence = (
            cycle(sequence) if n is None else
            chain.from_iterable(repeat(sequence, n))
        )
        breaking = False
        for delay, values in sequence:
            for value in values:
                self._write(value)
                if self._blink_thread.stopping.wait(delay):
                    breaking = True
                    break
            if breaking is True:
                break


GPIO_LED = SequencedPWMLED(CONFIG['PIN_PWM_LED'])


class LedInstructionProvidingThread(Thread):

    def _led_sequence(self, events: tuple[BlinkSequenceEvent, ...] | BlinkSequenceEvent,
                      initial_value: float | None = None, n: int | None = 1):
        GPIO_LED.sequence(events, initial_value, n, background=True)

    def _led_on(self, on_time: float | None = None, fade_time: float = 0, value: float = CONFIG['led']['LED_MAX']):
        n = 1 if on_time is not None and on_time > 0 else None
        GPIO_LED.sequence(BlinkSequenceEvent(value, on_time, fade_time), n=n, background=True)

    def _led_off(self, off_time: float | None = None, fade_time: float = 0):
        n = 1 if off_time is not None and off_time > 0 else None
        GPIO_LED.sequence(BlinkSequenceEvent(0, off_time, fade_time), n=n, background=True)

    def _led_blink(self, on_time: float | None = None, off_time: float | None = None,
                   led_on_value: float = CONFIG['led']['LED_MAX'], led_off_value: float = 0.0,
                   n: int = None):
        events = (
            BlinkSequenceEvent(led_on_value, on_time),
            BlinkSequenceEvent(led_off_value, off_time)
        )
        GPIO_LED.sequence(events, n=n, background=True)

    def _led_pulse(self, on_time: float | None = None, off_time: float | None = None,
                   fade_time_on: float = 0, fade_time_off: float = 0,
                   high_value: float = CONFIG['led']['LED_MAX'], low_value: float = CONFIG['led']['LED_MIN'],
                   n: int = None):  # TODO: stay_on: bool = False
        events = (
            BlinkSequenceEvent(high_value, on_time, fade_time_on),
            BlinkSequenceEvent(low_value, off_time, fade_time_off)
        )
        GPIO_LED.sequence(events, n=n, background=True)

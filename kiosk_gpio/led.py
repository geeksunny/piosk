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
        if n <= 0:
            return
        sequence = []
        prev_value = initial_value if initial_value is not None else self.value
        if isinstance(events, BlinkSequenceEvent):
            events = (events,)
        for event in events:
            value_steps = []
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
        for delay, values in sequence:
            for value in values:
                self._write(value)
                if self._blink_thread.stopping.wait(delay):
                    break


# class LedOperation(Enum):
#     ON = 1
#     OFF = 2
#     PULSE = 3
#     BLINK = 4
#     TOGGLE = 5
#
#     def create(self, on_time: float | None = None, off_time: float | None = False,
#                fade_time_on: float = 0, fade_time_off: float = 0,
#                led_min: float = CONFIG['led']['LED_MIN'], led_max: float = CONFIG['led']['LED_MAX'], n: int = 1,
#                initial_value: float = None, stay_on: bool = False):
#         return LedInstruction(self, on_time, off_time, fade_time_on, fade_time_off, led_min, led_max, n, initial_value, stay_on)
#
#
# @dataclass
# class LedInstruction:
#     operation: LedOperation
#     on_time: float | None = None
#     off_time: float | None = None
#     fade_time_on: float = 0
#     fade_time_off: float = 0
#     led_min: float = CONFIG['led']['LED_MIN']
#     led_max: float = CONFIG['led']['LED_MAX']
#     n: int = 1
#     initial_value: float | None = None
#     stay_on: bool = False
#
#
# class LedThread(Thread):
#
#     def __init__(self):
#         super(LedThread, self).__init__()
#         self._gpio_led = SequencedPWMLED(CONFIG['PIN_PWM_LED'])
#         self._current_operation: LedInstruction | None = None
#         self._next_operation_time = 0
#
#     def _get_next_operation(self):
#         global LED_INSTRUCTION_QUEUE
#         if not LED_INSTRUCTION_QUEUE.empty():
#             result = LED_INSTRUCTION_QUEUE.get(False)
#             LED_INSTRUCTION_QUEUE.task_done()
#             return result
#         else:
#             return None
#
#     def _perform_turn_on(self):
#         self._gpio_led.sequence(
#             BlinkSequenceEvent(self._current_operation.led_max, self._current_operation.on_time,
#                                self._current_operation.fade_time_on),
#             self._current_operation.initial_value, self._current_operation.n
#         )
#
#     def _perform_turn_off(self):
#         pass
#
#     def _perform_pulse(self):
#         pass
#
#     def _perform_blink(self):
#         pass
#
#     def _perform_toggle(self):
#         pass
#
#     def run(self):
#         while True:
#             if time.time() >= self._next_operation_time:
#                 # todo: perform next op
#                 pass
#                 if self._current_operation.operation is LedOperation.ON:
#                     self._perform_turn_on(True)
#                 elif self._current_operation.operation is LedOperation.OFF:
#                     self._perform_turn_off(True)
#                 elif self._current_operation.operation is LedOperation.PULSE:
#                     self._perform_pulse(True)
#                 elif self._current_operation.operation is LedOperation.BLINK:
#                     self._perform_blink(True)
#                 elif self._current_operation.operation is LedOperation.TOGGLE:
#                     self._perform_toggle(True)
#                 # todo: any clean up needed here?
#             else:
#                 next_op = self._get_next_operation()
#                 if next_op is not None:
#                     # todo: perform next op
#                     if next_op.operation is LedOperation.ON:
#                         self._perform_turn_on()
#                     elif next_op.operation is LedOperation.OFF:
#                         self._perform_turn_off()
#                     elif next_op.operation is LedOperation.PULSE:
#                         self._perform_pulse()
#                     elif next_op.operation is LedOperation.BLINK:
#                         self._perform_blink()
#                     elif next_op.operation is LedOperation.TOGGLE:
#                         self._perform_toggle()
#                     # TODO: set next op time, set current op value
#
#
# class LedInstructionProvidingThread(Thread):
#
#     def _led_on(self, on_time: float | None = None, fade_time: float = 0):
#         global LED_INSTRUCTION_QUEUE
#         LED_INSTRUCTION_QUEUE.put(LedOperation.ON.create(on_time=on_time, fade_time_on=fade_time))
#
#     def _led_off(self, off_time: float | None = None, fade_time: float = 0):
#         global LED_INSTRUCTION_QUEUE
#         LED_INSTRUCTION_QUEUE.put(LedOperation.OFF.create(off_time=off_time, fade_time_off=fade_time))
#
#     def _led_pulse(self, on_time: float | None = None, off_time: float | None = None,
#                    fade_time_on: float = 0, fade_time_off: float = 0,
#                    n: int = None, stay_on: bool = False):
#         global LED_INSTRUCTION_QUEUE
#         LED_INSTRUCTION_QUEUE.put(LedOperation.PULSE.create(on_time, off_time, fade_time_on, fade_time_off, n=n, stay_on=stay_on))
#
#     # todo: Implement blink and toggle operations


GPIO_LED = SequencedPWMLED(CONFIG['PIN_PWM_LED'])


class LedInstructionProvidingThread(Thread):


    def _led_sequence(self, events: tuple[BlinkSequenceEvent, ...] | BlinkSequenceEvent,
                      initial_value: float | None = None, n: int | None = 1):
        GPIO_LED.sequence(events, initial_value, n, background=True)

    def _led_on(self, on_time: float | None = None, fade_time: float = 0, value: float = CONFIG['led']['LED_MAX']):
        n = 1 if on_time > 0 else None
        GPIO_LED.sequence(BlinkSequenceEvent(value, on_time, fade_time), n=n, background=True)

    def _led_off(self, off_time: float | None = None, fade_time: float = 0):
        n = 1 if off_time > 0 else None
        GPIO_LED.sequence(BlinkSequenceEvent(0, off_time, fade_time), n=n, background=True)

    def _led_pulse(self, on_time: float | None = None, off_time: float | None = None,
                   fade_time_on: float = 0, fade_time_off: float = 0,
                   high_value: float = CONFIG['led']['LED_MAX'], low_value: float = CONFIG['led']['LED_MIN'],
                   n: int = None):  # TODO: stay_on: bool = False
        events = (
            BlinkSequenceEvent(high_value, on_time, fade_time_on),
            BlinkSequenceEvent(low_value, off_time, fade_time_off)
        )
        GPIO_LED.sequence(events, n=n, background=True)

    # todo: Implement blink and toggle operations

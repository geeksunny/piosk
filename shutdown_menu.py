#!/usr/bin/python3
import pathlib
import tkinter as tk
from threading import Thread, Event

import pygubu

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "shutdown_menu.ui"


class CounterThread(Thread):

    def __init__(self, group=..., target=..., name=..., args=..., kwargs=..., *, daemon=..., event: Event=None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self._event = event

    def run(self):
        super().run()
        # TODO: set counter variable starting at CONFIG['shutdown']['TIMEOUT'], reducing by 1 every second.
        self._event.wait(1)
        if self._event.is_set() is True:
            # TODO: Cancel timeout, close the window
            pass


class ShutdownMenuApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow: tk.Toplevel = builder.get_object("toplevel1", master)
        # Dialog window
        self.dialog = builder.get_object("dialog1", self.mainwindow)
        self.dialog_header = builder.get_variable("operation_value")
        self.dialog_countdown = builder.get_variable("countdown_value")

        builder.connect_callbacks(self)

    def run(self):
        self.mainwindow.mainloop()

    def on_reboot(self):
        self.dialog_header.set('Rebooting')
        self.dialog.run()
        # TODO: Start countdown thread; call the reboot shell command.

    def on_halt(self):
        self.dialog_header.set('Shutting Down')
        self.dialog.run()
        # TODO: Start countdown thread; call the halt shell command

    def on_cancel(self):
        self.mainwindow.destroy()

    def on_cancel_operation(self):
        self.dialog.close()


if __name__ == "__main__":
    app = ShutdownMenuApp()
    app.run()

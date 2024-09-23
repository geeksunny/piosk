#!/usr/bin/python3
import pathlib
import tkinter as tk
from threading import Thread, Event

import pygubu

from piosk.config import CONFIG


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

    def center(self, event):
        wm_min = self.mainwindow.wm_minsize()
        wm_max = self.mainwindow.wm_maxsize()
        screen_w = self.mainwindow.winfo_screenwidth()
        screen_h = self.mainwindow.winfo_screenheight()
        """ `winfo_width` / `winfo_height` at this point return `geometry` size if set. """
        x_min = min(screen_w, wm_max[0],
                    max(self.main_w, wm_min[0],
                        self.mainwindow.winfo_width(),
                        self.mainwindow.winfo_reqwidth()))
        y_min = min(screen_h, wm_max[1],
                    max(self.main_h, wm_min[1],
                        self.mainwindow.winfo_height(),
                        self.mainwindow.winfo_reqheight()))
        x = screen_w - x_min
        y = screen_h - y_min
        self.mainwindow.geometry(f"{x_min}x{y_min}+{x // 2}+{y // 2}")
        self.mainwindow.unbind("<Map>", self.center_map)

    def run(self):
        """ If `width` and `height` are set for the main widget,
        this is the only time TK returns them. """
        self.main_w = self.mainwindow.winfo_reqwidth()
        self.main_h = self.mainwindow.winfo_reqheight()
        self.center_map = self.mainwindow.bind("<Map>", self.center)

        self.mainwindow.mainloop()

    def display_dialog(self, title: str, cmd: str):
        self.dialog_header.set(title)
        self.dialog.run()
        print(f'TODO: Start countdown of {CONFIG['shutdown']['TIMEOUT']}')
        print(f'TODO: Call shell command: {cmd}')

    def on_reboot(self):
        self.display_dialog('Rebooting', 'sudo reboot')

    def on_halt(self):
        self.display_dialog('Shutting Down', 'sudo halt')

    def on_cancel(self):
        self.mainwindow.destroy()

    def on_cancel_operation(self):
        self.dialog.close()


if __name__ == "__main__":
    app = ShutdownMenuApp()
    app.run()

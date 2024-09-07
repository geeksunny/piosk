#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk


# TODO:
#  - Set window title
#  - Adjust visual styles:
#     * change all text to Dejavu-Sans font,
#     * Make buttons have bigger padding for easy touchscreen use. Space them out a little more?

class ShutdownMenuApp:
    def __init__(self, master=None):
        # build ui
        toplevel1 = tk.Tk() if master is None else tk.Toplevel(master)
        toplevel1.configure(height=200, width=200)
        toplevel1.resizable(False, False)
        self.frame_main = ttk.Frame(toplevel1, name="frame_main")
        self.frame_main.configure(height=200, width=200)
        label1 = ttk.Label(self.frame_main)
        label1.configure(font="{DejaVu Sans} 16 {}", text='Shut Down Menu')
        label1.grid(column=0, pady=8, row=0)
        self.frame_buttons = ttk.Frame(self.frame_main, name="frame_buttons")
        self.frame_buttons.configure(height=200, width=200)
        self.button_reboot = ttk.Button(
            self.frame_buttons, name="button_reboot")
        self.button_reboot.configure(text='Reboot')
        self.button_reboot.grid(column=0, padx=8, row=0)
        self.button_reboot.configure(command=self.on_reboot)
        self.button_halt = ttk.Button(self.frame_buttons, name="button_halt")
        self.button_halt.configure(text='Shut Down')
        self.button_halt.grid(column=1, padx=8, row=0)
        self.button_halt.configure(command=self.on_halt)
        self.button_cancel = ttk.Button(
            self.frame_buttons, name="button_cancel")
        self.button_cancel.configure(text='Cancel')
        self.button_cancel.grid(column=3, padx=8, row=0)
        self.button_cancel.configure(command=self.on_cancel)
        self.frame_buttons.grid(column=0, padx=8, pady=16, row=2)
        self.frame_main.grid(column=0, row=0)

        # Main widget
        self.mainwindow = toplevel1

    def run(self):
        self.mainwindow.mainloop()

    def on_reboot(self):
        pass

    def on_halt(self):
        pass

    def on_cancel(self):
        pass


if __name__ == "__main__":
    app = ShutdownMenuApp()
    app.run()

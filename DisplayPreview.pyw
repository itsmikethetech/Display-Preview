import tkinter as tk
from tkinter import ttk, messagebox, Menu
import threading
import time
import mss
import numpy as np
import cv2
from screeninfo import get_monitors  # Import the function directly
from pygetwindow import getWindowsWithTitle
from win32api import EnumDisplaySettings
from win32con import ENUM_CURRENT_SETTINGS, ENUM_REGISTRY_SETTINGS
from PIL import Image, ImageTk

class DisplayPreview:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title("Display Preview")
        self.root.geometry('1280x720')
        self.selected_monitor_index = 0
        self.selected_framerate = 60 

        self.monitors = get_monitors()  # Use the correct method to fetch monitors
        if len(self.monitors) == 0:
            messagebox.showerror("Error", "No monitors found.")
            return

        # Use static refresh rates
        self.refresh_rates = [1, 15, 30, 40, 60, 70, 90, 120, 144, 165]
        self.cursor_visible = True
        self.preview_running = True
        self.is_fullscreen = False

        self.init_ui()

        self.preview_running = True
        threading.Thread(target=self._update_preview_thread, daemon=True).start()

        self.root.bind("<Configure>", self.resize_preview)
        self.cursor_visible = True
        self.cursor_image = Image.open("cursor.png")
        self.cursor_image = self.cursor_image.convert("RGBA")
        self.set_icon()

        self.root.bind("<Escape>", self.toggle_fullscreen)
        self.root.bind("<Alt-Return>", self.toggle_fullscreen)

        self.is_fullscreen = False

    def init_ui(self):
        menu_bar = Menu(self.root)

        monitor_menu = Menu(menu_bar, tearoff=0)
        for i, monitor in enumerate(self.monitors):
            monitor_menu.add_command(label=f"Monitor {i + 1}: ({monitor.width}x{monitor.height})",
                                     command=lambda i=i: self.change_monitor(i))
        menu_bar.add_cascade(label="Monitor", menu=monitor_menu)

        framerate_menu = Menu(menu_bar, tearoff=0)
        for rate in self.refresh_rates:
            framerate_menu.add_command(label=f"{rate} FPS",
                                       command=lambda rate=rate: self.change_framerate(rate))
        menu_bar.add_cascade(label="Framerate", menu=framerate_menu)

        menu_bar.add_command(label="Toggle Cursor", command=self.toggle_cursor)
        menu_bar.add_command(label="Toggle Fullscreen (Alt+Return)", command=self.toggle_fullscreen)

        self.root.config(menu=menu_bar)

        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.grid(row=1, column=0, columnspan=7, pady=5, padx=10, sticky="nsew")
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def set_icon(self):
        self.root.iconbitmap('video.ico')

    def toggle_cursor(self):
        self.cursor_visible = not self.cursor_visible

    def change_framerate(self, framerate):
        self.selected_framerate = framerate

    def change_monitor(self, monitor_index):
        self.selected_monitor_index = monitor_index

    def _update_preview_thread(self):
        with mss.mss() as sct:
            while self.preview_running:
                try:
                    if self.selected_monitor_index < len(sct.monitors) - 1:
                        monitor = sct.monitors[self.selected_monitor_index + 1]
                        screenshot = np.array(sct.grab(monitor))
                        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGBA2RGB)
                        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
                        frame_width = self.preview_frame.winfo_width()
                        frame_height = self.preview_frame.winfo_height()

                        if frame_width > 0 and frame_height > 0:
                            height, width, _ = screenshot.shape
                            scale = min(frame_width / width, frame_height / height)
                            new_width = int(width * scale)
                            new_height = int(height * scale)

                            screenshot = cv2.resize(screenshot, (new_width, new_height), interpolation=cv2.INTER_AREA)

                        if self.cursor_visible:
                            cursor_x, cursor_y = self.root.winfo_pointerxy()
                            cursor_x = cursor_x - monitor['left']
                            cursor_y = cursor_y - monitor['top']
                            x_scale = new_width / monitor['width']
                            y_scale = new_height / monitor['height']
                            preview_cursor_x = int(cursor_x * x_scale)
                            preview_cursor_y = int(cursor_y * y_scale)
                            preview_cursor_x = min(max(0, preview_cursor_x), new_width - 1)
                            preview_cursor_y = min(max(0, preview_cursor_y), new_height - 1)
                            self.draw_cursor(screenshot, preview_cursor_x, preview_cursor_y)

                        tk_image = ImageTk.PhotoImage(image=Image.fromarray(screenshot))
                        self.root.after(0, self._update_preview_label, tk_image)

                    # Adjust the sleep time based on the selected framerate
                    time.sleep(1 / self.selected_framerate)
                except tk.TclError:
                    break

    def draw_cursor(self, image, x, y):
        cursor_width, cursor_height = self.cursor_image.size
        left = max(0, x - cursor_width // 2)
        top = max(0, y - cursor_height // 2)
        right = min(x + cursor_width // 2, image.shape[1])
        bottom = min(y + cursor_height // 2, image.shape[0])
        image_pil = Image.fromarray(image)
        image_pil.paste(self.cursor_image, (left, top), self.cursor_image)
        image[:] = np.array(image_pil)

    def _update_preview_label(self, tk_image):
        if self.preview_running:
            self.preview_label.config(image=tk_image)
            self.preview_label.image = tk_image

    def resize_preview(self, event):
        if self.preview_running:
            self.preview_label.update_idletasks()

    def close_preview(self):
        self.preview_running = False
        self.preview_label.config(image='')  # Remove image
        self.preview_label.image = None

    def on_closing(self):
        self.close_preview()
        self.root.quit()
        self.root.destroy()

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.root.attributes("-fullscreen", True)
            monitor = self.monitors[self.selected_monitor_index]
            self.root.geometry(f"{monitor.width}x{monitor.height}+{monitor.left}+{monitor.top}")
        else:
            self.root.attributes("-fullscreen", False)
            self.root.geometry('1280x720')

if __name__ == "__main__":
    root = tk.Tk()
    app = DisplayPreview(root)
    root.mainloop()

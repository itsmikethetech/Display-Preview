import tkinter as tk
from tkinter import ttk, messagebox
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
from ttkthemes import ThemedTk

class DisplayPreview:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title("Display Preview")
        self.root.geometry('1280x720')

        # Initial theme setup

        # Theme mapping
        self.theme_map = {
            "arc": "Arc Theme", "black": "Dark Theme", "blue": "Blue Theme", "clearlooks": "Clearlooks Theme",
            "equilux": "Equilux Theme", "radiance": "Radiance Theme", "scidblue": "Scidblue Theme", "winxpblue": "WinXP Blue Theme",
            "adapta": "Adapta Theme", "aquativo": "Aquativo Theme", "elegance": "Elegance Theme",
            "itft1": "ITFT1 Theme", "keramik": "Keramik Theme", "kroc": "Kroc Theme", "plastik": "Plastik Theme",
            "smog": "Smog Theme", "yaru": "Yaru Theme"
        }
        self.reverse_theme_map = {v: k for k, v in self.theme_map.items()}  # Reverse map for theme selection

        self.current_theme = "black"
        self.root.set_theme(self.current_theme)
        self.root.configure(bg=self.get_current_theme_bg_color())

        self.monitors = get_monitors()  # Use the correct method to fetch monitors
        if len(self.monitors) == 0:
            messagebox.showerror("Error", "No monitors found.")
            return

        # Use static refresh rates
        self.refresh_rates = [1, 15, 30, 40, 60, 70, 90, 120, 144, 165]

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
        # Monitor selection
        self.monitor_label = ttk.Label(self.root, text="Monitor:")
        self.monitor_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.monitor_combo = ttk.Combobox(self.root, values=[f"Monitor {i+1}: ({monitor.width}x{monitor.height})"
                                                            for i, monitor in enumerate(self.monitors)],
                                        width=25)
        self.monitor_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.monitor_combo.current(0)
        self.monitor_combo.bind("<<ComboboxSelected>>", self.on_monitor_change)

        # Framerate selection
        self.framerate_label = ttk.Label(self.root, text="Framerate:")
        self.framerate_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.framerate_combo = ttk.Combobox(self.root, values=[str(rate) for rate in self.refresh_rates],
                                            width=10)
        self.framerate_combo.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        self.framerate_combo.set("60")

        # Theme selection
        self.theme_label = ttk.Label(self.root, text="Select Theme:")
        self.theme_label.grid(row=0, column=4, padx=10, pady=5, sticky="e")
        # Use the display names for the theme combo
        self.theme_combo = ttk.Combobox(self.root, values=list(self.theme_map.values()), width=20)
        self.theme_combo.grid(row=0, column=5, padx=10, pady=5, sticky="w")
        self.theme_combo.set(self.theme_map[self.current_theme])  # Set default theme
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)

        # Show cursor checkbox
        self.show_cursor_var = tk.BooleanVar(value=True)
        self.show_cursor_checkbox = ttk.Checkbutton(self.root, text="Show Cursor", variable=self.show_cursor_var, command=self.toggle_cursor)
        self.show_cursor_checkbox.grid(row=0, column=6, padx=10, pady=5, sticky="ne")

        # Preview Frame
        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.grid(row=1, column=0, columnspan=7, pady=5, padx=10, sticky="nsew")
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def set_icon(self):
        self.root.iconbitmap('video.ico')

    def toggle_cursor(self):
        self.cursor_visible = self.show_cursor_var.get()

    def on_monitor_change(self, event):
        pass

    def on_theme_change(self, event):
        selected_display_name = self.theme_combo.get()
        selected_theme = self.reverse_theme_map.get(selected_display_name, self.current_theme)
        self.current_theme = selected_theme
        self.root.set_theme(selected_theme)
        self.root.configure(bg=self.get_current_theme_bg_color())

    def get_current_theme_bg_color(self):
        theme_colors = {
            "arc": "#F0F0F0", "black": "#424242", "blue": "#6699cc", "clearlooks": "#efebe7",
            "equilux": "#464646", "radiance": "#f6f4f2", "scidblue": "#eff0f1", "winxpblue": "#eff0f1",
            "adapta": "#fafbfc", "aquativo": "#eff0f1", "elegance": "#d8d8d8",
            "itft1": "#daeffd", "keramik": "#cccccc", "kroc": "#fcb64f", "plastik": "#efefef",
            "smog": "#e7eaf0", "yaru": "#f5f6f7"
        }
        return theme_colors.get(self.current_theme, "#fafbfc")

    def _update_preview_thread(self):
        with mss.mss() as sct:
            while self.preview_running:
                try:
                    monitor_index = self.monitor_combo.current()
                    if monitor_index < len(sct.monitors) - 1:
                        monitor = sct.monitors[monitor_index + 1]
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
                    selected_framerate = int(self.framerate_combo.get())
                    time.sleep(1 / selected_framerate)
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
            monitor = self.monitors[self.monitor_combo.current()]
            self.root.geometry(f"{monitor.width}x{monitor.height}+{monitor.left}+{monitor.top}")
        else:
            self.root.attributes("-fullscreen", False)
            self.root.geometry('1280x720')

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = DisplayPreview(root)
    root.mainloop()

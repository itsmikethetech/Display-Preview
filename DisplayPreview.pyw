import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import mss
import numpy as np
import cv2
from screeninfo import get_monitors
from PIL import Image, ImageTk
import pyautogui

class DisplayPreview:
    def __init__(self, root):
        self.root = root

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title("Display Preview")
        root.geometry('1280x720')

        self.monitors = self.get_monitors()
        if len(self.monitors) == 0:
            messagebox.showerror("Error", "No monitors found.")
            return

        self.init_ui()

        self.preview_running = True
        threading.Thread(target=self._update_preview_thread, daemon=True).start()

    def init_ui(self):
        self.monitor_label = ttk.Label(self.root, text="Monitor:")
        self.monitor_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        
        self.monitor_combo = ttk.Combobox(self.root, values=[
            f"Monitor {i+1}: ({monitor.width}x{monitor.height})"
            for i, monitor in enumerate(self.monitors)
        ], width=25)
        self.monitor_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.monitor_combo.current(0)
        self.monitor_combo.config(state="readonly")

        self.cursor_var = tk.BooleanVar(value=True)
        self.cursor_check = ttk.Checkbutton(self.root, text="Show Cursor", variable=self.cursor_var)
        self.cursor_check.grid(row=0, column=2, padx=10, pady=5)

        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.grid(row=1, column=0, columnspan=3, pady=5, padx=10, sticky="nsew")
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def _update_preview_thread(self):
        with mss.mss() as sct:
            while self.preview_running:
                try:
                    monitor_index = self.monitor_combo.current()
                    if monitor_index < len(sct.monitors) - 1:
                        monitor = sct.monitors[monitor_index + 1]
                        
                        screenshot = np.array(sct.grab(monitor))
                        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2RGB)
                        
                        if self.cursor_var.get():
                            cursor_x, cursor_y = pyautogui.position()
                            cursor_x -= monitor["left"]
                            cursor_y -= monitor["top"]
                            if 0 <= cursor_x < screenshot.shape[1] and 0 <= cursor_y < screenshot.shape[0]:
                                cv2.circle(screenshot, (cursor_x, cursor_y), 10, (0, 0, 255), -1)
                        
                        frame_width = self.preview_frame.winfo_width()
                        frame_height = self.preview_frame.winfo_height()

                        if frame_width > 0 and frame_height > 0:
                            height, width, _ = screenshot.shape
                            scale = min(frame_width / width, frame_height / height)
                            new_width = int(width * scale)
                            new_height = int(height * scale)
                            screenshot = cv2.resize(screenshot, (new_width, new_height), interpolation=cv2.INTER_AREA)

                        tk_image = ImageTk.PhotoImage(image=Image.fromarray(screenshot))
                        self.root.after(0, self._update_preview_label, tk_image)

                    time.sleep(0.0167)
                except tk.TclError:
                    break

    def _update_preview_label(self, tk_image):
        if self.preview_running:
            self.preview_label.config(image=tk_image)
            self.preview_label.image = tk_image

    def on_closing(self):
        self.preview_running = False
        self.root.destroy()

    def get_monitors(self):
        return get_monitors()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DisplayPreview(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

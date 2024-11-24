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
        self.root.title("Display Preview")
        self.root.geometry('1280x720')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.cursor_image = cv2.imread("cursor.png", cv2.IMREAD_UNCHANGED)  # Load cursor image with alpha channel
        if self.cursor_image is None:
            messagebox.showerror("Error", "Cursor image 'cursor.png' not found.")
            self.root.destroy()
            return

        self.monitors = get_monitors()
        if not self.monitors:
            messagebox.showerror("Error", "No monitors found.")
            self.root.destroy()
            return

        self.preview_running = True
        self._build_ui()
        threading.Thread(target=self._update_preview_thread, daemon=True).start()

    def _build_ui(self):
        ttk.Label(self.root, text="Monitor:").grid(row=0, column=0, padx=10, pady=5, sticky="e")

        monitor_options = [f"Monitor {i+1}: ({m.width}x{m.height})" for i, m in enumerate(self.monitors)]
        self.monitor_combo = ttk.Combobox(self.root, values=monitor_options, state="readonly", width=25)
        self.monitor_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.monitor_combo.current(0)

        self.cursor_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.root, text="Show Cursor", variable=self.cursor_var).grid(row=0, column=2, padx=10, pady=5)

        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def _update_preview_thread(self):
        with mss.mss() as sct:
            while self.preview_running:
                try:
                    monitor = sct.monitors[self.monitor_combo.current() + 1]
                    screenshot = np.array(sct.grab(monitor))
                    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2RGB)

                    if self.cursor_var.get():
                        self._overlay_cursor(screenshot, monitor)

                    self._resize_and_update_preview(screenshot)
                    time.sleep(0.0167)
                except Exception:
                    break

    def _overlay_cursor(self, screenshot, monitor):
        cursor_x, cursor_y = pyautogui.position()
        cx, cy = cursor_x - monitor["left"], cursor_y - monitor["top"]

        # Ensure cursor is within monitor bounds
        if 0 <= cx < monitor["width"] and 0 <= cy < monitor["height"]:
            h, w, _ = self.cursor_image.shape
            x1, y1 = max(0, cx - w // 2), max(0, cy - h // 2)
            x2, y2 = min(screenshot.shape[1], x1 + w), min(screenshot.shape[0], y1 + h)

            # Adjust the cursor image dimensions to fit within bounds
            cursor_x1, cursor_y1 = 0, 0
            cursor_x2, cursor_y2 = x2 - x1, y2 - y1
            if x1 < 0:
                cursor_x1 -= x1
                x1 = 0
            if y1 < 0:
                cursor_y1 -= y1
                y1 = 0

            # Extract ROI from screenshot and overlay the cursor
            roi = screenshot[y1:y2, x1:x2]
            cursor_alpha = self.cursor_image[cursor_y1:cursor_y2, cursor_x1:cursor_x2, 3] / 255.0
            for c in range(3):  # Blend the cursor image channels
                roi[:, :, c] = (1 - cursor_alpha) * roi[:, :, c] + cursor_alpha * self.cursor_image[cursor_y1:cursor_y2, cursor_x1:cursor_x2, c]
            screenshot[y1:y2, x1:x2] = roi


    def _resize_and_update_preview(self, screenshot):
        frame_w, frame_h = self.preview_frame.winfo_width(), self.preview_frame.winfo_height()
        if frame_w > 0 and frame_h > 0:
            scale = min(frame_w / screenshot.shape[1], frame_h / screenshot.shape[0])
            new_size = (int(screenshot.shape[1] * scale), int(screenshot.shape[0] * scale))
            screenshot = cv2.resize(screenshot, new_size, interpolation=cv2.INTER_AREA)

            tk_image = ImageTk.PhotoImage(Image.fromarray(screenshot))
            self.root.after(0, self._update_preview_label, tk_image)

    def _update_preview_label(self, tk_image):
        if self.preview_running:
            self.preview_label.config(image=tk_image)
            self.preview_label.image = tk_image

    def on_closing(self):
        self.preview_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DisplayPreview(root)
    root.mainloop()

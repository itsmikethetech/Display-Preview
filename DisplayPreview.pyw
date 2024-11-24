import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import mss
import numpy as np
import cv2
from screeninfo import get_monitors
from PIL import Image, ImageTk

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
        self.root.bind("<Configure>", self.resize_preview)
        self.cursor_visible = True
        self.cursor_image = Image.open("cursor.png") 
        self.cursor_image = self.cursor_image.convert("RGBA") 
        self.show_cursor_var = tk.BooleanVar(value=True)
        self.show_cursor_checkbox = ttk.Checkbutton(self.root, text="Show Cursor", variable=self.show_cursor_var, command=self.toggle_cursor)
        self.show_cursor_checkbox.grid(row=2, column=0, columnspan=2, pady=10)
        self.set_icon()

    def init_ui(self):
        self.monitor_label = ttk.Label(self.root, text="Monitor:")
        self.monitor_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.monitor_combo = ttk.Combobox(self.root, values=[f"Monitor {i+1}: ({monitor.width}x{monitor.height})"
                                                            for i, monitor in enumerate(self.monitors)],
                                           width=25)
        self.monitor_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.monitor_combo.current(0)
        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.grid(row=1, column=0, columnspan=2, pady=5, padx=10, sticky="nsew")
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def set_icon(self):
        self.root.iconbitmap('video.ico')

    def toggle_cursor(self):
        self.cursor_visible = self.show_cursor_var.get()

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

                    time.sleep(0.0167)
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
        self.preview_label.config(image='')
        self.preview_label.image = None

    def on_closing(self):
        self.close_preview()
        self.root.quit()
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
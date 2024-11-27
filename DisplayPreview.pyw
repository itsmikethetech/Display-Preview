import tkinter as tk
from tkinter import ttk, messagebox, Menu
import threading
import time
import dxcam
import numpy as np
import cv2
from screeninfo import get_monitors
from PIL import Image, ImageTk

class DisplayPreview:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title("Display Preview")
        self.root.geometry('1280x720')
        self.selected_monitor_index = 0
        self.selected_framerate = 30

        self.monitors = get_monitors()
        if len(self.monitors) == 0:
            messagebox.showerror("Error", "No monitors found.")
            return

        self.refresh_rates = [1, 10, 15, 30, 40, 60]
        self.cursor_visible = True
        self.preview_running = True
        self.is_fullscreen = False

        self.init_ui()
        self.camera = dxcam.create(output_idx=self.selected_monitor_index)
        threading.Thread(target=self._update_preview_thread, daemon=True).start()

        self.root.bind("<Configure>", self.resize_preview)
        self.cursor_image = Image.open("cursor.png")
        self.cursor_image = self.cursor_image.convert("RGBA")
        self.set_icon()

        self.root.bind("<Escape>", self.toggle_fullscreen)
        self.root.bind("<Alt-Return>", self.toggle_fullscreen)

    def init_ui(self):
        self.menu_bar = Menu(self.root)

        monitor_menu = Menu(self.menu_bar, tearoff=0)
        for i, monitor in enumerate(self.monitors):
            monitor_menu.add_command(label=f"Monitor {i + 1}: ({monitor.width}x{monitor.height})",
                                     command=lambda i=i: self.change_monitor(i))
        self.menu_bar.add_cascade(label="Monitor", menu=monitor_menu)

        framerate_menu = Menu(self.menu_bar, tearoff=0)
        for rate in self.refresh_rates:
            framerate_menu.add_command(label=f"{rate} FPS",
                                       command=lambda rate=rate: self.change_framerate(rate))
        self.menu_bar.add_cascade(label="Framerate", menu=framerate_menu)

        self.menu_bar.add_command(label="Toggle Cursor", command=self.toggle_cursor)
        self.menu_bar.add_command(label="Toggle Fullscreen (ESC)", command=self.toggle_fullscreen)

        self.root.config(menu=self.menu_bar)

        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.grid(row=1, column=0, columnspan=7, pady=0, padx=10, sticky="nsew")
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
        self.camera = dxcam.create(output_idx=self.selected_monitor_index)

    def _update_preview_thread(self):
        while self.preview_running:
            try:
                frame = self.camera.grab()
                if frame is not None:
                    # Remove the BGR to RGB conversion
                    frame_width = self.preview_frame.winfo_width()
                    frame_height = self.preview_frame.winfo_height()

                    if frame_width > 0 and frame_height > 0:
                        height, width, _ = frame.shape
                        scale = min(frame_width / width, frame_height / height)
                        new_width = int(width * scale)
                        new_height = int(height * scale)

                        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

                    if self.cursor_visible:
                        cursor_x, cursor_y = self.root.winfo_pointerxy()
                        monitor = self.monitors[self.selected_monitor_index]
                        cursor_x -= monitor.x
                        cursor_y -= monitor.y
                        x_scale = new_width / monitor.width
                        y_scale = new_height / monitor.height
                        preview_cursor_x = int(cursor_x * x_scale)
                        preview_cursor_y = int(cursor_y * y_scale)
                        preview_cursor_x = min(max(0, preview_cursor_x), new_width - 1)
                        preview_cursor_y = min(max(0, preview_cursor_y), new_height - 1)
                        self.draw_cursor(frame, preview_cursor_x, preview_cursor_y)

                    # Convert directly to a Tkinter-compatible image
                    tk_image = ImageTk.PhotoImage(image=Image.fromarray(frame))
                    self.root.after(0, self._update_preview_label, tk_image)

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
        self.preview_label.config(image="")  # Remove image
        self.preview_label.image = None
        self.camera.stop()

    def on_closing(self):
        self.close_preview()
        self.root.quit()
        self.root.destroy()

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.root.attributes("-fullscreen", True)
            monitor = self.monitors[self.selected_monitor_index]
            self.root.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
            self.root.config(menu="")  # Hide the menu bar
        else:
            self.root.attributes("-fullscreen", False)
            self.root.geometry("1280x720")
            self.root.config(menu=self.menu_bar)  # Show the menu bar

if __name__ == "__main__":
    root = tk.Tk()
    app = DisplayPreview(root)
    root.mainloop()

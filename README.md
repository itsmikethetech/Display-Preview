# Display Preview App

Simple application to preview your display outputs, including displays created using the Virtual Display Driver or IndirectDisplayDriver. It allows users to preview a selected monitor's display, toggle cursor visibility, and adjust the refresh rate of the preview. It supports fullscreen mode and dynamically resizes the preview based on window adjustments.

The application captures monitor screens using the **mss** library, processes the images with **OpenCV**, and displays them in a **tkinter** GUI. It also overlays a customizable cursor icon onto the preview.

[![image](https://github.com/user-attachments/assets/3594f096-ed02-46a3-80da-d23a366c036f)](https://github.com/itsmikethetech/Display-Preview/releases)

# Instructions

1. Download from the **[latest releases](https://github.com/itsmikethetech/Display-Preview/releases)**.
2. Extract **DisplayPreview.zip**
3. Run **DisplayPreview.exe**

# Features

> [!TIP]
> Press **Escape** or **Alt + Enter** to enter/exit fullscreen mode.

- **Monitor Selection:**
Users can select from multiple monitors connected to their system.
Each monitor's resolution is displayed in the menu.
- **Framerate Adjustment:**
Options for refresh rates include 1, 10, 15, 30, 40, and 60 frames per second (FPS).
- **Cursor Visibility:**
A toggle to show or hide the cursor in the monitor preview.
- **Fullscreen Mode:**
Toggle fullscreen mode using the menu or keyboard shortcuts (Escape or Alt + Enter).
- **Dynamic Resizing:**
Preview automatically resizes when the application window is resized.
- **Icon and Menu Bar:**
Includes a custom icon (video.ico) and user-friendly menu options for all features.

# Python Dependencies
> [!WARNING]
> These are **only** required if running the Python script.
> These are **automatically included** with the built **executable**.

- **tkinter**: For GUI components.
- **mss**: For screen capturing.
- **numpy**: For image array manipulation.
- **cv2** (OpenCV): For image processing and resizing.
- **Pillow**: For handling images.
- **screeninfo**: For monitor resolution and positioning.

# Python Instructions
1. Install Python (version 3.8 or higher is recommended).
2. Install the required libraries using pip:
    - **pip install mss numpy opencv-python pillow screeninfo**
3. Place the following required files in the same directory as the script:
    - cursor.png: Custom cursor image.
    - video.ico: Application icon.
4. Run the script from the terminal or a Python IDE:
    - **python display_preview.py**

# Thanks

Executable built using **PyInstaller**.

This script is heavily influenced and inspired by **LexTrack's MiniScreenRecorder**. I essentially reverse engineered his MiniScreenRecorder script to get the preview window, then added features from there. This project helped me learn a TON!

https://github.com/lextrack/MiniScreenRecorder (MIT)


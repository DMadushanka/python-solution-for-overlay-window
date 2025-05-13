Window Embedding Overlay
This Python application allows users to embed external application windows into a custom overlay window with additional features like resizing, rounded corners, and transparency. It is designed for Windows operating systems and leverages the tkinter library for the GUI and Windows API for window manipulation.

Features:
Embed External Windows: Select and embed any open window into the overlay.
Customizable Overlay: Adjust the size, border radius, and transparency of the overlay.
Keyboard Shortcuts:
R: Hide the title bar and border of the overlay.
T: Show the title bar and border of the overlay.
Drag and Move: Drag the overlay window when the title bar is hidden.
Dynamic Window List: Refresh and display all currently open windows for selection.
Rounded Corners: Apply rounded corners to the overlay window.
Transparency: Set partial transparency for the overlay.
Technologies Used:
Python Libraries:
tkinter: For the graphical user interface.
pygetwindow: To retrieve a list of open windows.
ctypes: For interacting with the Windows API.
win32gui, win32con, win32api: For advanced window manipulation.
Windows API: To manage window styles, embedding, and keyboard events.
Requirements:
Operating System: Windows
Python Version: 3.8 or higher
Dependencies:
pygetwindow
pywin32
How to Use:
Run the application.
Select a window from the list of open windows.
Customize the overlay settings (size, border radius, etc.).
Click "Embed Window" to embed the selected window into the overlay.
Use the provided shortcuts or buttons to manage the overlay.
Disclaimer:
This application is designed for Windows only and may not work on other operating systems.

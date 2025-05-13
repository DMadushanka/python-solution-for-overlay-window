import tkinter as tk
from tkinter import ttk, messagebox
import pygetwindow as gw
import win32gui
import win32con
import win32api
import platform
import ctypes
import sys
from ctypes import wintypes

# Set up Windows API functions
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Define the window procedure type
WNDPROC = ctypes.CFUNCTYPE(
    ctypes.c_int, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM
)

class EmbeddedWindowOverlay:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Embedding Overlay")
        self.root.geometry("500x500")
        
        # Add window procedure variables
        self.old_wndproc = None
        self.wndproc = None
        
        # Configure theme colors
        self.bg_color = "green"
        self.fg_color = "#ECEFF4"
        self.accent_color = "#88C0D0"
        self.button_bg = "#4C566A"
        self.button_fg = "#ECEFF4"
        self.button_active_bg = "#5E81AC"
        
        # Configure root window style
        self.root.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure ttk styles
        self.style.configure('TLabel', 
                           background=self.bg_color,
                           foreground=self.fg_color,
                           font=('Segoe UI', 10))
        
        self.style.configure('TButton',
                           background=self.button_bg,
                           foreground=self.button_fg,
                           font=('Segoe UI', 9),
                           padding=5)
        
        self.style.map('TButton',
                      background=[('active', self.button_active_bg)],
                      foreground=[('active', self.fg_color)])
        
        self.style.configure('TEntry',
                           fieldbackground=self.button_bg,
                           foreground=self.fg_color,
                           insertcolor=self.fg_color)
        
        self.style.configure('TFrame',
                           background=self.bg_color)
        
        self.target_hwnd = None
        self.overlay_window = None
        self.embedded = False
        self.os_name = platform.system()
        self.title_visible = True
        
        self.create_widgets()
        self.refresh_windows()
        
        self.root.bind('r', self.hide_title_bar)
        self.root.bind('t', self.show_title_bar)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="1. Select Window to Embed:", font=('Segoe UI', 11, 'bold')).pack(pady=5)
        
        # Custom styled listbox
        self.window_listbox = tk.Listbox(main_frame, 
                                       height=10,
                                       bg=self.button_bg,
                                       fg=self.fg_color,
                                       selectbackground=self.accent_color,
                                       selectforeground=self.fg_color,
                                       font=('Segoe UI', 9),
                                       relief=tk.FLAT,
                                       highlightthickness=1,
                                       highlightbackground=self.accent_color)
        self.window_listbox.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        
        ttk.Button(main_frame, text="Refresh Windows", command=self.refresh_windows).pack(pady=10)
        
        ttk.Label(main_frame, text="2. Overlay Settings:", font=('Segoe UI', 11, 'bold')).pack(pady=5)
        
        size_frame = ttk.Frame(main_frame)
        size_frame.pack(pady=5)
        
        ttk.Label(size_frame, text="Width:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="800")
        ttk.Entry(size_frame, textvariable=self.width_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(size_frame, text="Height:").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value="600")
        ttk.Entry(size_frame, textvariable=self.height_var, width=5).pack(side=tk.LEFT, padx=5)

        radius_frame = ttk.Frame(main_frame)
        radius_frame.pack(pady=5)

        ttk.Label(radius_frame, text="Border Radius:").pack(side=tk.LEFT)
        self.radius_var = tk.StringVar(value="40")
        ttk.Entry(radius_frame, textvariable=self.radius_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # Action buttons with custom styling
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)
        
        ttk.Button(button_frame, text="Embed Window", command=self.embed_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Release Window", command=self.release_window).pack(side=tk.LEFT, padx=5)
        
        # Keyboard shortcuts section
        shortcuts_frame = ttk.Frame(main_frame)
        shortcuts_frame.pack(pady=10)
        
        ttk.Label(shortcuts_frame, text="Keyboard Shortcuts:", font=('Segoe UI', 10, 'bold')).pack()
        ttk.Label(shortcuts_frame, text="R - Hide Title Bar/Border | T - Show Title Bar/Border").pack()
    
    def hide_title_bar(self, event=None):
        if self.overlay_window:
            self.overlay_window.overrideredirect(True)
            self.title_visible = False

            hwnd = int(self.overlay_window.winfo_id())
            style = ctypes.windll.user32.GetWindowLongA(hwnd, win32con.GWL_STYLE)
            new_style = style & ~win32con.WS_BORDER & ~win32con.WS_DLGFRAME
            ctypes.windll.user32.SetWindowLongA(hwnd, win32con.GWL_STYLE, new_style)
            ctypes.windll.user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER |
                win32con.SWP_FRAMECHANGED
            )

            # Enable dragging functionality
            self.overlay_window.bind("<ButtonPress-1>", self.start_drag)
            self.overlay_window.bind("<B1-Motion>", self.do_drag)

    def start_drag(self, event):
        """Capture the initial position of the mouse and window."""
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def do_drag(self, event):
        """Move the window based on mouse movement."""
        x = self.overlay_window.winfo_x() + (event.x - self._drag_start_x)
        y = self.overlay_window.winfo_y() + (event.y - self._drag_start_y)
        self.overlay_window.geometry(f"+{x}+{y}")
    
    def show_title_bar(self, event=None):
        if self.overlay_window:
            self.overlay_window.overrideredirect(False)
            self.title_visible = True
            
            hwnd = int(self.overlay_window.winfo_id())
            style = ctypes.windll.user32.GetWindowLongA(hwnd, win32con.GWL_STYLE)
            new_style = style | win32con.WS_BORDER | win32con.WS_DLGFRAME
            ctypes.windll.user32.SetWindowLongA(hwnd, win32con.GWL_STYLE, new_style)
            ctypes.windll.user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | 
                win32con.SWP_FRAMECHANGED
            )
    
    def refresh_windows(self):
        self.window_listbox.delete(0, tk.END)
        try:
            if self.os_name == "Windows":
                windows = gw.getAllTitles()
                for window in windows:
                    if window and window.strip():
                        self.window_listbox.insert(tk.END, window)
            else:
                messagebox.showerror("Error", "This feature currently only works on Windows")
        except Exception as e:
            messagebox.showerror("Error", f"Could not get windows: {str(e)}")
    
    def embed_window(self):
        if self.embedded:
            messagebox.showwarning("Warning", "A window is already embedded")
            return
            
        selection = self.window_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a window first")
            return
            
        window_title = self.window_listbox.get(selection[0])
        
        try:
            self.target_hwnd = win32gui.FindWindow(None, window_title)
            if not self.target_hwnd:
                messagebox.showerror("Error", "Window not found")
                return
                
            try:
                width = int(self.width_var.get())
                height = int(self.height_var.get())
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for width and height")
                return
                
            self.create_overlay_window(width, height)
            self.set_parent_window()
            self.embedded = True
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not embed window: {str(e)}")
    
    def create_overlay_window(self, width, height):
        if self.overlay_window:
            self.overlay_window.destroy()
            
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.title("Embedded Window Overlay")
        self.overlay_window.geometry(f"{width}x{height}")
        self.overlay_window.attributes("-topmost", True)
        self.overlay_window.attributes("-transparentcolor", self.bg_color)
        self.overlay_window.attributes("-alpha", 1.4)  # Set partial transparency (80% opacity)
        
        # Configure overlay window style
        self.overlay_window.configure(bg=self.bg_color)
        
        # Make sure the window can receive keyboard focus
        self.overlay_window.focus_force()
        
        hwnd = int(self.overlay_window.winfo_id())
        ctypes.windll.user32.SetWindowLongA(
            hwnd, 
            win32con.GWL_EXSTYLE,
            win32con.WS_EX_TOOLWINDOW
        )

        # Apply rounded corners
        try:
            radius = int(self.radius_var.get())
        except ValueError:
            radius = 40  # default
        hRgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, width, height, radius, radius)
        ctypes.windll.user32.SetWindowRgn(hwnd, hRgn, True)

        # Custom styled close button
        close_btn = ttk.Button(self.overlay_window, 
                             text="×", 
                             command=self.release_window,
                             width=3,
                             style='Close.TButton')
        
        # Configure close button style
        self.style.configure('Close.TButton',
                           background=self.button_bg,
                           foreground=self.fg_color,
                           font=('Segoe UI', 12, 'bold'),
                           padding=2)
        
        self.style.map('Close.TButton',
                      background=[('active', '#E06C75')],
                      foreground=[('active', self.fg_color)])
        
        close_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
    
    def set_parent_window(self):
        try:
            overlay_hwnd = int(self.overlay_window.winfo_id())
            style = win32gui.GetWindowLong(self.target_hwnd, win32con.GWL_STYLE)
            
            if style & win32con.WS_POPUP:
                win32gui.SetWindowLong(self.target_hwnd, win32con.GWL_STYLE, style & ~win32con.WS_POPUP)
            
            win32gui.SetWindowLong(self.target_hwnd, win32con.GWL_STYLE, style | win32con.WS_CHILD)
            win32gui.SetParent(self.target_hwnd, overlay_hwnd)
            
            overlay_rect = win32gui.GetWindowRect(overlay_hwnd)
            overlay_width = overlay_rect[2] - overlay_rect[0] - 10
            overlay_height = overlay_rect[3] - overlay_rect[1] - 10
            
            win32gui.MoveWindow(self.target_hwnd, 0, 0, overlay_width, overlay_height, True)
            win32gui.BringWindowToTop(self.target_hwnd)
            
            # Set up keyboard handling
            self.setup_keyboard_handling()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to embed window: {str(e)}")
            self.release_window()

    def setup_keyboard_handling(self):
        def forward_key(event):
            if not self.target_hwnd or not win32gui.IsWindow(self.target_hwnd):
                return
            
            # Get the virtual key code
            vk = win32api.VkKeyScan(event.char) if event.char else event.keysym_num
            
            # Create the lparam value
            scan_code = user32.MapVirtualKeyW(vk, 0)
            lparam = (scan_code << 16) | 1  # Add repeat count
            
            if event.type == tk.EventType.KeyPress:
                # Send key down
                win32gui.SendMessage(self.target_hwnd, win32con.WM_KEYDOWN, vk, lparam)
                # Send character if it's a printable character
                if event.char:
                    win32gui.SendMessage(self.target_hwnd, win32con.WM_CHAR, ord(event.char), lparam)
            elif event.type == tk.EventType.KeyRelease:
                # Send key up
                win32gui.SendMessage(self.target_hwnd, win32con.WM_KEYUP, vk, lparam)
            
            return "break"

        # Bind keyboard events
        self.overlay_window.bind('<KeyPress>', forward_key)
        self.overlay_window.bind('<KeyRelease>', forward_key)
        
        # Make sure the overlay window can receive keyboard focus
        self.overlay_window.focus_set()
    
    def release_window(self):
        # Remove window subclassing if it exists
        if self.old_wndproc:
            overlay_hwnd = int(self.overlay_window.winfo_id())
            user32.SetWindowLongPtrW(
                overlay_hwnd,
                win32con.GWL_WNDPROC,
                self.old_wndproc
            )
            self.old_wndproc = None
            self.wndproc = None

        if self.target_hwnd and self.embedded:
            try:
                style = win32gui.GetWindowLong(self.target_hwnd, win32con.GWL_STYLE)
                win32gui.SetWindowLong(self.target_hwnd, win32con.GWL_STYLE, style & ~win32con.WS_CHILD)
                win32gui.SetParent(self.target_hwnd, 0)
                win32gui.MoveWindow(self.target_hwnd, 100, 100, 800, 600, True)
                win32gui.BringWindowToTop(self.target_hwnd)
            except Exception as e:
                print(f"Error releasing window: {str(e)}")
            self.embedded = False
            self.target_hwnd = None
        
        if self.overlay_window:
            hwnd = int(self.overlay_window.winfo_id())
            ctypes.windll.user32.SetWindowRgn(hwnd, 0, True)  # Reset rounded region
            self.overlay_window.destroy()
            self.overlay_window = None
    
    def on_close(self):
        # Ensure window subclassing is removed
        if self.old_wndproc:
            overlay_hwnd = int(self.overlay_window.winfo_id())
            user32.SetWindowLongPtrW(
                overlay_hwnd,
                win32con.GWL_WNDPROC,
                self.old_wndproc
            )
        self.release_window()
        self.root.destroy()

if __name__ == "__main__":
    if platform.system() != "Windows":
        messagebox.showerror("Error", "This application only works on Windows")
        sys.exit(1)
        
    root = tk.Tk()
    app = EmbeddedWindowOverlay(root)
    root.mainloop()

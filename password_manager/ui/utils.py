import ctypes
import ctypes.wintypes


def apply_dark_titlebar(widget):
    try:
        hwnd = int(widget.winId())
        DWMWA_CAPTION_COLOR = 35
        # #1e1e2e → COLORREF (BGR): R=0x1e, G=0x1e, B=0x2e
        color = ctypes.c_int(0x2E1E1E)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_CAPTION_COLOR,
            ctypes.byref(color), ctypes.sizeof(color)
        )
    except Exception:
        pass

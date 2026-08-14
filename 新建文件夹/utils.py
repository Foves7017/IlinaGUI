import ctypes
from ctypes import wintypes
from uuid import uuid4, UUID
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from FovesConfig import ConfigLoader

from globals import APP_CONFIG_PATH, AppConfig

dwmapi = ctypes.WinDLL("dwmapi")

# 原型：HRESULT DwmSetWindowAttribute(HWND, DWORD, LPCVOID, DWORD)
DwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute
DwmSetWindowAttribute.argtypes = [
    wintypes.HWND,
    ctypes.c_uint,     # dwAttribute
    ctypes.c_void_p,   # pvAttribute
    ctypes.c_uint,     # cbAttribute
]
DwmSetWindowAttribute.restype = ctypes.HRESULT

# 枚举值（Win11 22000+）
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR     = 36
DWMWA_BORDER_COLOR   = 34
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_COLOR_DEFAULT  = 0xFFFFFFFF


def set_titlebar_color(hwnd, caption=None, text=None, border=None):
    """caption/text/border 传 COLORREF (0x00bbggrr) 或 None 表示不改"""
    def _set(attr, color):
        val = ctypes.c_uint(color)
        hr = DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val), ctypes.sizeof(val))
        if hr != 0:  # S_OK == 0
            raise ctypes.WinError(hr)
    if caption is not None:
        _set(DWMWA_CAPTION_COLOR, caption)
    if text is not None:
        _set(DWMWA_TEXT_COLOR, text)
    if border is not None:
        _set(DWMWA_BORDER_COLOR, border)

NULL_UUID = UUID('00000000-0000-0000-0000-000000000000')

def generate_uuid() -> UUID:
    """ 生成一个 UUID，只保证不等于 NULL_UUID，不保证不重复 """
    res = uuid4()
    while res == NULL_UUID:
        res = uuid4()
    return res
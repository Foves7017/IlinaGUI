from typing import Literal

import ctypes
from pydantic import BaseModel
from ctypes.wintypes import HWND, INT

from utils import config_dir, app_dir

SEGOE_FLUENT_ICON_MIN = chr(0xE921)
SEGOE_FLUENT_ICON_MAX = chr(0xE922)
SEGOE_FLUENT_ICON_RESTORE = chr(0xE923)
SEGOE_FLUENT_ICON_CLOSE = chr(0xE8BB)
SEGOE_FLUENT_ICON_RELOAD = chr(0xE72C)
# https://learn.microsoft.com/zh-cn/windows/apps/design/iconography/segoe-fluent-icons-font

CONFIG_PATH = config_dir()/'window_base.json'
BACKGROUND_QML_PATH = str(app_dir()/'window_base/background.qml')
WINDOWBASE_QSS_PATH = str(app_dir()/'window_base/window_base.qss')
WINDOWBASE_YAML_PATH = str(app_dir()/'window_base/window_base.yaml')

class WindowConfig(BaseModel):
    """ 窗口配置 """
    edge_board: int = 5  # 用于边界拖动的宽度
    window_state: str = ''  # 保存窗口状态
    window_maxed: bool = False  # 窗口是否最大化
    default_size: tuple[int, int] = (1440, 960)  # 默认窗口尺寸
    tooltip_duration: int = 1000  # 浮动信息的等待时间（MS）

class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth",    INT),
        ("cxRightWidth",   INT),
        ("cyTopHeight",    INT),
        ("cyBottomHeight", INT),
    ]

class MSG(ctypes.Structure):
    """Windows MSG 结构体，用于 nativeEvent 解析"""
    _fields_ = [
        ("hwnd",    ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam",  ctypes.c_ulonglong),
        ("lParam",  ctypes.c_longlong),
        ("time",    ctypes.c_uint),
        ("pt_x",    ctypes.c_long),
        ("pt_y",    ctypes.c_long),
    ]

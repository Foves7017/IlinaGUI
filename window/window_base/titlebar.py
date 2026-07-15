from FovesConfig import ConfigLoader

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy

from layout.formatter import Formatter
from .consts import *
from .title_label import TitleLabel

class TitlebarButton(QPushButton):
    def __init__(self, text: str, button_width: int, tooltip: str|None=None, parent=None):
        super().__init__(parent)
        self.setObjectName('TitleBarButton')
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding
        )
        self.setFixedWidth(button_width)
        self.setText(text)

        if tooltip:
            self.setToolTip(tooltip)
            self.setToolTipDuration(ConfigLoader(CONFIG_PATH, WindowConfig).readonly().tooltip_duration)

class TitlebarMaxButton(TitlebarButton):
    """ 触发 Snap 的最大化按钮 """
    def __init__(self, text: str, button_width: int, tooltip: str | None = None, parent=None):
        super().__init__(text, button_width, tooltip, parent)
        # 定时器，延迟后触发（为了 Snap Layouts 菜单）
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(ConfigLoader(CONFIG_PATH, WindowConfig).readonly().tooltip_duration)  
        self._hover_timer.timeout.connect(self._trigger_snap_layout)
    
    def enterEvent(self, event):
        self._hover_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_timer.stop()
        super().leaveEvent(event)

    def _trigger_snap_layout(self):
        """模拟 Win + Z"""
        VK_LWIN = 0x5B
        VK_Z    = 0x5A
        KEYEVENTF_KEYUP = 0x0002

        ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)           # Win 按下
        ctypes.windll.user32.keybd_event(VK_Z,    0, 0, 0)           # Z 按下
        ctypes.windll.user32.keybd_event(VK_Z,    0, KEYEVENTF_KEYUP, 0)  # Z 松开
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)  # Win 松开

class Titlebar(QWidget):
    close_button_pushed = Signal()
    max_button_pushed = Signal()
    min_button_pushed = Signal()

    def __init__(self, formatter: Formatter):
        super().__init__()

        self.setFixedHeight(formatter.titlebar_height)
        self.setObjectName('TitleBar')
        self.setContentsMargins(0, 0, 0, 0)

        # 窗口是否最大化的标志
        self._is_max: bool = False

        # 标题栏
        self.titlelabel = TitleLabel()

        # 关闭按钮
        self.close_button = TitlebarButton(SEGOE_FLUENT_ICON_CLOSE, formatter.titlebar_height, '关闭')
        self.close_button.setObjectName('TitleBarClose')

        # 最大化/还原按钮
        self.max_button = TitlebarMaxButton(SEGOE_FLUENT_ICON_MAX, formatter.titlebar_height)

        # 最小化按钮
        self.min_button = TitlebarButton(SEGOE_FLUENT_ICON_MIN, formatter.titlebar_height, '最小化')

        # 重载样式按钮
        self.reload_button = TitlebarButton(SEGOE_FLUENT_ICON_RELOAD, formatter.titlebar_height, '重新加载样式')

        # 布局
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.titlelabel)
        self._layout.addStretch(1)
        self._layout.addWidget(self.reload_button)
        self._layout.addWidget(self.min_button)
        self._layout.addWidget(self.max_button)
        self._layout.addWidget(self.close_button)

        # 信号
        self.close_button.pressed.connect(self.close_button_pushed.emit)
        self.max_button.pressed.connect(self.max_button_pushed.emit)
        self.min_button.pressed.connect(self.min_button_pushed.emit)
        self.reload_button.pressed.connect(formatter.reload)

    @property
    def is_max(self) -> bool:
        return self._is_max

    @is_max.setter
    def is_max(self, new_value: bool):
        self._is_max = new_value
        if self._is_max:
            self.max_button.setText(SEGOE_FLUENT_ICON_RESTORE)
        else:
            self.max_button.setText(SEGOE_FLUENT_ICON_MAX)
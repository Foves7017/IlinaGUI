from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtQuickWidgets import QQuickWidget

from .consts import *
from layout.formatter import Formatter

class ActiveBar(QQuickWidget):
    """ 活动栏，类似 VSCode 最左侧的 
    
    这个组件只应该做两件事：

    1. 添加 Icon 显示
    2. 在用户点击 Icon 的时候发出信号

    永远不要让这个组件 “自己查找有哪些图标应该显示”

    """

    clicked_button = Signal(str)

    def __init__(self, formatter: Formatter):
        super().__init__()
        self.setClearColor(Qt.GlobalColor.transparent)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding
        )

        self.setFixedWidth(formatter.active_bar_width)

        self.icons: list[tuple[str, QIcon]] = []  # 存放按钮和名称

        self.rootContext().setContextProperty('backend', self)
    
    def add_icon(self, name: str, icon: QIcon):
        self.icons.append((name, icon))
    
    
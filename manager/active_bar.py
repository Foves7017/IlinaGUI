from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal, Property, Slot
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtQuickWidgets import QQuickWidget

from .consts import *

from globals import get_theme_manager

class ActiveBar(QQuickWidget):
    """ 活动栏，类似 VSCode 最左侧的 
    
    这个组件只应该做两件事：

    1. 添加 Icon 显示
    2. 在用户点击 Icon 的时候发出信号

    永远不要让这个组件 "自己查找有哪些图标应该显示"

    """

    button_clicked = Signal(str)

    def __init__(self, icons: dict[str, str]={}):
        super().__init__()
        self.setClearColor(Qt.GlobalColor.transparent)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding
        )

        self.setFixedWidth(get_theme_manager().active_bar_width)

        self._icons: dict[str, str] = icons

        self.rootContext().setContextProperty('backend', self)

    @Property(dict)
    def icons(self):
        return self._icons

    @Property(list, constant=True)
    def icon_keys(self):
        """ 返回图标键的列表，供 QML Repeater 遍历 """
        return list(self._icons.keys())

    @Slot(str)
    def trigger_clicked(self, key: str):
        """ QML 按钮点击时调用，转发为 clicked_button 信号 """
        self.button_clicked.emit(key)

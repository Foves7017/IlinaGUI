from uuid import UUID
from typing import Callable

from PySide6.QtCore import Qt, QUrl, Signal, Property, Slot
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtQuickWidgets import QQuickWidget

from globals import app_path
from ilina_app import app_instance

class ActiveBar(QQuickWidget):
    """ 活动栏，类似 VSCode 最左侧的 
    
    这个组件只应该做两件事：

    1. 添加 Icon 显示
    2. 在用户点击 Icon 的时候发出信号

    永远不要让这个组件 "自己查找有哪些图标应该显示"

    """

    button_clicked = Signal(str)
    # setting_button_clicked = Signal()

    def __init__(self):
        super().__init__()

        # 设置宽度
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding
        )
        self.setFixedWidth(app_instance().theme_manager.active_bar_width)

        # 设置图标
        self._icons: dict[str, str] = {
            info.name: info.active_bar_chara
            for info in app_instance().plugin_manager.plugins.values()
            if info.active_bar_chara
        }

        # 设置 QML
        self.setClearColor(Qt.GlobalColor.transparent)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
        app_instance().theme_manager.add_qml_widget(self, app_path()/'main_window'/'active_bar.qml', 'active_bar')
        self.rootContext().setContextProperty('backend', self)

    @Property(dict, constant=True)
    def icons(self):
        return self._icons

    @Property(str, constant=True)
    def setting_chara(self):
        return chr(60052)

    @Property(list, constant=True)
    def icon_keys(self):
        """ 返回图标键的列表，供 QML Repeater 遍历 """
        return list(self._icons.keys())
from pathlib import Path
from logging import getLogger

from FovesConfig import ConfigLoader

from PySide6.QtCore import Qt, QByteArray, QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6QtAds import CDockManager, CDockWidget, DockWidgetArea

from .consts import *

from globals import get_workspace, get_theme_manager, get_dock_manager
from .active_bar import ActiveBar
from .dock_manager import DockManager
from plugins.plugin_manager import PluginManager
from window_base.window_base import WindowBase

class Manager(WindowBase):
    def __init__(self, argv: list[str]):
        super().__init__()

        self.log = getLogger('Manager')
        
        self.log.info(f'工作区路径：{get_workspace()}')

        # 设置标题
        self.titlebar.titlelabel.label = get_workspace().stem
        self.titlebar.titlelabel.setDisabled(True)
        self.setWindowTitle(get_workspace().stem + ' - Ilina GUI')

        # 初始化插件系统
        self.plugin_manager = PluginManager()

        get_theme_manager().add_yaml(MANAGER_YAML_PATH)

        # 设置右侧的 docker
        CDockManager.setConfigFlag(CDockManager.FloatingContainerHasWidgetTitle, False)
        self.dock_manager = get_dock_manager()
        get_theme_manager().add_qss_widget(self.dock_manager, DOCK_MANAGER_QSS_PATH)
        self.dock_manager.setProperty('mainWindow', 'true')
        # self.titlebar.reload_button.pressed.connect(lambda: self.dock_manager.create_dock('file_manager'))

        # 设置左侧的活动栏
        self.active_bar = ActiveBar(self.plugin_manager.name_to_icon_chara)
        get_theme_manager().add_qml_widget(self.active_bar, ACTIVEBAR_QML_PATH)
        self.active_bar.button_clicked.connect(self.dock_manager.create_dock)

        # 设置内容 widget
        self.content = QWidget()
        self.content_layout = QHBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addWidget(self.active_bar)
        self.content_layout.addWidget(self.dock_manager)
        self.root_layout.addWidget(self.content)

    def showEvent(self, event: QShowEvent) -> None:
        # QTimer.singleShot(0, self.dock_manager.load_saved_dock)
        self.dock_manager.load_saved_dock()
        return super().showEvent(event)

    def _on_close(self):
        with ConfigLoader(MANAGER_CONFIG_PATH, ManagerConfig) as config:
            config.dock_state = self.dock_manager.saveState().toBase64().data().decode()
        self.dock_manager.close.emit()
        self.dock_manager.save_created_docks()
        return super()._on_close()
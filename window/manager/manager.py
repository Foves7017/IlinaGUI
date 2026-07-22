from pathlib import Path
from logging import getLogger

from FovesConfig import ConfigLoader

from PySide6.QtCore import Qt, QByteArray, QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6QtAds import CDockManager, CDockWidget, DockWidgetArea

from .consts import *
from .active_bar import ActiveBar
from .dock_manager import DockManager
from global_consts import *
from plugins.plugin_manager import PluginManager
from window.window_base.titlebar import TitlebarButton
from window.window_base.window_base import WindowBase

class Manager(WindowBase):
    def __init__(self, argv: list[str]):
        super().__init__()

        self.log = getLogger('Manager')

        # 从 sys.argv 中提取工作目录
        config = ConfigLoader(CONFIG_PATH, AppConfig).readonly()
        self.workspace: Path = Path(config.latest_workspace or config.default_workspace)
        if len(argv) > 1:
            path = Path(argv[1])
            if path.is_dir():
                self.workspace = path
            elif path.is_file():
                self.workspace = path.parent
        
        self.log.info(f'工作区路径：{self.workspace}')

        # 设置标题
        self.titlebar.titlelabel.label = self.workspace.stem
        self.titlebar.titlelabel.setDisabled(True)
        self.setWindowTitle(self.workspace.stem + ' - Ilina GUI')

        # 初始化插件系统
        self.plugin_manager = PluginManager(self.formatter)

        # 设置右侧的 docker
        CDockManager.setConfigFlag(CDockManager.FloatingContainerHasWidgetTitle, False)
        self.dock_manager = DockManager(self.workspace, self.plugin_manager, self.formatter)
        self.formatter.add_qss_widget(self.dock_manager, DOCK_MANAGER_QSS_PATH)
        self.dock_manager.setProperty('mainWindow', 'true')
        # self.titlebar.reload_button.pressed.connect(lambda: self.dock_manager.create_dock('file_manager'))

        # 设置左侧的活动栏
        self.active_bar = ActiveBar(self.formatter, self.plugin_manager.name_to_icon_chara)
        self.formatter.add_qml_widget(self.active_bar, ACTIVEBAR_QML_PATH)
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
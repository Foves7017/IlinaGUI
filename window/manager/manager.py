from pathlib import Path
from logging import getLogger

from FovesConfig import ConfigLoader

from PySide6.QtCore import Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6QtAds import CDockManager, CDockWidget, DockWidgetArea

from .consts import *
from .dock_manager import DockManager
from .active_bar import ActiveBar
from global_consts import *
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

        # 设置内容 widget
        self.content = QWidget()
        self.content_layout = QHBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.addWidget(self.content)

        # 设置左侧的活动栏
        self.active_bar = ActiveBar(self.formatter)
        self.content_layout.addWidget(self.active_bar)
        self.formatter.add_qml_widget(self.active_bar, ACTIVEBAR_QML_PATH)

        # 设置右侧的 docker
        self.dock_manager = DockManager()
        self.content_layout.addWidget(self.dock_manager)
        self.formatter.add_qss_widget(self.dock_manager, SPLITTER_QSS_PATH)

        label = QLabel("Hello, QtAds!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dock = CDockWidget("我的面板")
        dock.setWidget(label)

        label1 = QLabel("Hello, QtAds!")
        label1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dock1 = CDockWidget("我的面板1")
        dock1.setWidget(label1)

        self.dock_manager.addDockWidget(
            DockWidgetArea.LeftDockWidgetArea, dock1
        )

        self.dock_manager.addDockWidget(
            DockWidgetArea.LeftDockWidgetArea, dock
        )
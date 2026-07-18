from pathlib import Path
from logging import getLogger

from FovesConfig import ConfigLoader

from PySide6.QtCore import Qt, QByteArray, QTimer
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
        self.formatter.add_qss_widget(self.dock_manager, DOCK_MANAGER_QSS_PATH)

        for i in range(10):
            label1 = QLabel(f"Hello, QtAds! {i}")
            label1.setAlignment(Qt.AlignmentFlag.AlignCenter)

            dock1 = CDockWidget(f"我的面板 {i}")
            dock1.setWidget(label1)

            self.dock_manager.addDockWidget(
                DockWidgetArea.LeftDockWidgetArea, dock1
            )
        
        # 从配置中恢复 dock 状态（延迟到事件循环就绪后执行，避免 showEvent 时 container 未就绪）
        config = ConfigLoader(MANAGER_CONFIG_PATH, ManagerConfig).readonly()
        if config.dock_state.encode():
            QTimer.singleShot(0, lambda ctx=config: (
                self.dock_manager.restoreState(
                    QByteArray.fromBase64(ctx.dock_state.encode())
                )
            ))
    
    def _on_close(self):
        with ConfigLoader(MANAGER_CONFIG_PATH, ManagerConfig) as config:
            config.dock_state = self.dock_manager.saveState().toBase64().data().decode()
        self.dock_manager.close.emit()
        return super()._on_close()
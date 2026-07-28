import logging
from uuid import uuid4, UUID
from pathlib import Path
from FovesConfig import ConfigLoader

from PySide6.QtCore import Signal, QByteArray, QTimer
from PySide6.QtWidgets import QWidget
from PySide6QtAds import CDockManager, CDockWidget, DockWidgetArea

from .consts import *
from plugins.consts import InitParam
from layout.formatter import Formatter
from plugins.plugin_manager import PluginManager
from window.window_base.window_base_dock import WindowBaseII

class DockManager(CDockManager):
    close = Signal()

    def __init__(self, 
                 workspace: Path, 
                 plugin_manager: PluginManager,
                 formatter: Formatter,
                 ):
        super().__init__()
        self.log = logging.getLogger('Dock 管理器')

        self.floatingWidgetCreated.connect(self._on_floating_created)

        self.workspace = workspace
        self.plugin_manager = plugin_manager
        self.initparam = InitParam(
            workspace=workspace.as_posix(),
            open_file=None,
            formatter=formatter,
            plugin_manager=plugin_manager,
            uuid=None,
            dock_manager=self,
        )

        self.created_docks: dict[UUID, str] = {}

        self.log.info(f'初始化完成')
    
    def _on_floating_created(self, container):
        container.setParent(None)

        layout = container.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        base = WindowBaseII(container)
        self.close.connect(base.close)
        self.close.connect(container.close)
        layout.addWidget(base)

        inner = layout.takeAt(0)
        inner.widget().setProperty('mainWindow', 'false')
        base.root_layout.addWidget(inner.widget())
        base.titlebar.titlelabel.label = self.workspace.stem

    def _on_dock_close(self, uuid: UUID):
        self.log.info(f'移除面板：{uuid}')
        del self.created_docks[uuid]

    def create_dock(self, 
                    plugin_name: str, 
                    uuid: UUID|None=None,
                    open_file: str|None=None,
                    ):
        """ 根据指定的插件名创建一个面板 """
        self.log.info(f'尝试创建面板：{plugin_name}')
        if uuid is None:
            uuid = uuid4()
        
        widget_t = self.plugin_manager.get_widget_type_by_name(plugin_name)

        self.initparam.uuid = uuid
        self.initparam.open_file = open_file

        if widget_t is not None:
            print(self.initparam)
            widget = widget_t(self.initparam) # pyright: ignore[reportArgumentType, reportCallIssue]
            dock = CDockWidget(self.plugin_manager.get_display_name_by_name(plugin_name))
            dock.setWidget(widget)
            dock.setObjectName(str(uuid))
            dock.closed.connect(lambda: self._on_dock_close(uuid))
            self.addDockWidget(DockWidgetArea.LeftDockWidgetArea, dock)
            self.log.info(f'创建成功 {id(dock)=} {uuid=}')
            self.created_docks[uuid] = plugin_name
        else:
            self.log.warning(f'创建面板 {plugin_name} 失败，未获取到类型')
    
    def load_saved_dock(self):
        config = ConfigLoader(MANAGER_CONFIG_PATH, ManagerConfig).readonly()
        for uuid, name in config.created_docks.items():
            self.create_dock(name, uuid)

        if config.dock_state.encode():
            QTimer.singleShot(0, lambda ctx=config: (
                self.restoreState(
                    QByteArray.fromBase64(ctx.dock_state.encode())
                )
            ))
    
    def save_created_docks(self):
        with ConfigLoader(MANAGER_CONFIG_PATH, ManagerConfig) as config:
            config.created_docks = self.created_docks

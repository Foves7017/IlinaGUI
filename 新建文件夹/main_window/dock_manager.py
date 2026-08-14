import logging
from uuid import UUID

from pydantic import BaseModel
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6QtAds import CDockManager, CDockWidget, DockWidgetArea

from .background import BackgroundLayer
from ilina_app import app_instance
from globals import app_path, DockInfo
from utils import generate_uuid, set_titlebar_color

class DockManager(CDockManager):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log = logging.getLogger('Dock管理器')

        self.floatingWidgetCreated.connect(self._on_floating_created)

        app_instance().theme_manager.add_qss_widget(self, app_path()/'main_window'/'dock_manager.qss', 'dock_manager')

        self.floating_windows = {}

        self.log.info(f'初始化完成')
        

    @Slot()
    def _on_floating_created(self, container):
        uuid = generate_uuid()
        self.floating_windows[uuid] = container

        container.setParent(None)
        
        layout = container.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        base = BackgroundLayer(container)
        # self.close.connect(base.close)
        # self.close.connect(container.close)
        layout.addWidget(base)

        inner = layout.takeAt(0)
        inner.widget().setProperty('mainWindow', 'false')
        base.root_layout.addWidget(inner.widget())
        app_instance().theme_manager.add_qss_widget(inner.widget(), app_path()/'main_window'/'dock_manager.qss', f'inner_{uuid}')

        app_instance().theme_manager.reload()

    def create_dock(self, info: DockInfo, content_widget: QWidget):
        dock = CDockWidget(info.plugin_display_name)
        dock.setWidget(content_widget)
        dock.setObjectName(str(info.uuid))
        # dock.closed.connect(lambda: self._on_dock_close(uuid))
        self.addDockWidget(DockWidgetArea.RightDockWidgetArea, dock)
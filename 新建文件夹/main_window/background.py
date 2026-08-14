from PySide6.QtCore import Slot
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtQuickWidgets import QQuickWidget

from utils import set_titlebar_color, generate_uuid
from globals import app_path
from ilina_app import app_instance

class BackgroundLayer(QQuickWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.root_layout = QHBoxLayout(self)        
        self.root_layout.setSpacing(0)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        app_instance().theme_manager.add_qml_widget(self, app_path()/'main_window'/'background.qml', f'background_{str(generate_uuid())}')
        app_instance().theme_manager.theme_reloaded.connect(self.on_theme_reloaded)
        app_instance().theme_manager.reload_qml([self.objectName()])

    @Slot()
    def on_theme_reloaded(self):
        set_titlebar_color(self.window().winId(), app_instance().theme_manager.window_titlebar_background_color)
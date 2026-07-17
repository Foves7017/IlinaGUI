from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6QtAds import CDockManager

from window.window_base.window_base_II import WindowBaseII

class DockManager(CDockManager):
    def __init__(self):
        super().__init__()
        self.floatingWidgetCreated.connect(self._on_floating_created)
    
    def _on_floating_created(self, container: QWidget):

        container.setParent(None)
        
        layout = container.layout()
        base = WindowBaseII(container)
        layout.addWidget(base)

        inner = layout.takeAt(0)
        base.root_layout.addWidget(inner.widget())
        
        

        container.installEventFilter(base)

    
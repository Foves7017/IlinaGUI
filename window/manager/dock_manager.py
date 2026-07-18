from PySide6.QtCore import Signal
from PySide6QtAds import CDockManager

from window.window_base.window_base_dock import WindowBaseII

from PySide6.QtCore import Qt

class DockManager(CDockManager):
    close = Signal()

    def __init__(self):
        super().__init__()
        self.floatingWidgetCreated.connect(self._on_floating_created)
    
    def _on_floating_created(self, container):
        container.setParent(None)

        layout = container.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        base = WindowBaseII(container)
        self.close.connect(base.close)
        self.close.connect(container.close)
        layout.addWidget(base)

        inner = layout.takeAt(0)
        base.root_layout.addWidget(inner.widget())
        
        # container.installEventFilter(base)
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTextEdit

class MarkdownBrowser(QTextEdit):
    hotkey_cancel = Signal()
    hotkey_save = Signal()
    hotkey_save_invoke = Signal()
    def __init__(self):
        super().__init__()
        # 去掉滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 高度随内容自适应
        self.document().documentLayout().documentSizeChanged.connect(
            lambda size: self.setFixedHeight(int(size.height()))
        )
        self.setEnabled(False)
    
    def setMarkdown(self, markdown: str) -> None:
        markdown = markdown.replace('\n', '\n\n')
        return super().setMarkdown(markdown)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Escape,):
            self.hotkey_cancel.emit()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:  
                    self.hotkey_save_invoke.emit()
                else:
                    self.hotkey_save.emit()
        return super().keyPressEvent(event)

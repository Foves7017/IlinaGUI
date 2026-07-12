from FovesConfig import ConfigLoader
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTextEdit

from utils import app_dir
from ..types import WindowConfig

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
        self.__expand: bool = True
        self.document().documentLayout().documentSizeChanged.connect(self.check_height)
        self.setEnabled(False)
        # 从设置中读取自动折叠高度备用
        self.max_collapse_height = ConfigLoader(app_dir()/'configs'/'window.json', WindowConfig).readonly().max_collapse_height

    @property
    def expand(self) -> bool:
        return self.__expand

    @expand.setter
    def expand(self, new_value: bool):
        self.__expand = new_value
        self.check_height(self.document().size())

    def check_height(self, size):
        if self.__expand:
            self.setFixedHeight(int(size.height()))
        else:
            self.setFixedHeight(min(size.height(), self.max_collapse_height))

    def setMarkdown(self, markdown: str) -> None:
        res = super().setMarkdown(markdown)
        self.document().setTextWidth(self.viewport().width() or self.width())  # 手动触发刷新内容确保高度计算
        return res

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

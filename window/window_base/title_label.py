import re

from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import QEvent, QObject, Qt, Signal, QSize, QTimer
from PySide6.QtWidgets import QLineEdit, QSizePolicy

class TitleLabel(QLineEdit):
    """ 作为标题栏的 TextEdit，支持双击修改 """
    label_edited = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName('TitleLabel')
        self.setReadOnly(True)
        self.installEventFilter(self)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            self.sizePolicy().verticalPolicy()
        )
        self.label = 'WindowTitle'

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        text = self.text()
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(text) + 30
        width = text_width
        return QSize(width, base.height())

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str):
        self._label = value
        self.setText(value)
        self.updateGeometry()

    def eventFilter(self, obj: QObject, event) -> bool:
        if obj is self:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self._label = self.text()
                    self._label = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', self._label)
                    self.label_edited.emit(self._label)
                    self.setReadOnly(True)
                    self.label = self._label
                    return True
                elif event.key() in (Qt.Key.Key_Escape,):
                    self.setText(self._label)
                    self.setReadOnly(True)
                    return True
                
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                self.setReadOnly(False)
                QTimer.singleShot(0, lambda: (self.setFocus(), self.selectAll()))
                return True
            
            elif event.type() == QEvent.Type.Paint:
                self.updateGeometry()
            
            elif event.type() == QEvent.Type.FocusOut:
                self.setText(self._label)
                self.setReadOnly(True)
                return True

        return super().eventFilter(obj, event)

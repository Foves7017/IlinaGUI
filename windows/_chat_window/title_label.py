import re
from PySide6.QtCore import QEvent, QObject, Qt, Signal, QSize, QTimer
from PySide6.QtWidgets import QLineEdit, QSizePolicy
from PySide6.QtGui import QFontMetrics

from QSS import qss_formatter, QSSFiles

class TitleLabel(QLineEdit):
    """ 作为标题栏的 TextEdit，在ChatWindow用来作为显示对话名，并支持双击修改 """
    label_edited = Signal(str)
    def __init__(self):
        super().__init__()
        qss_formatter.add_widget(self, 'TitleLabel', QSSFiles.chat_window)
        self.setEnabled(False)
        self.installEventFilter(self)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            self.sizePolicy().verticalPolicy()
        )
        self.saved_text: str = ''

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        text = self.text()
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(text) + 30
        width = text_width
        return QSize(width, base.height())

    @property
    def label(self) -> str:
        return self.saved_text

    @label.setter
    def label(self, value: str):
        self.saved_text = value
        self.setText(value)
        self.updateGeometry()

    def eventFilter(self, obj: QObject, event) -> bool:
        if obj is self:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self.saved_text = self.text()
                    self.saved_text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', self.saved_text)
                    self.label_edited.emit(self.saved_text)
                    self.setEnabled(False)
                    self.label = self.saved_text
                    return True
                elif event.key() in (Qt.Key.Key_Escape,):
                    self.setText(self.saved_text)
                    self.setEnabled(False)
                    return True
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                self.setEnabled(True)
                QTimer.singleShot(0, lambda: (self.setFocus(), self.selectAll()))
                return True
            elif event.type() == QEvent.Type.Paint:
                self.updateGeometry()
        return super().eventFilter(obj, event)

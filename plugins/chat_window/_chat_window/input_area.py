from enum import Enum
from PySide6.QtWidgets import QWidget, QPushButton, QTextEdit, QSizePolicy, QGridLayout, QHBoxLayout
from PySide6.QtCore import Qt, QEvent, Signal

# from QSS import QSSFiles, qss_formatter
from layout.formatter import Formatter
from ..consts import *

class InputState(str, Enum):
    SEND = 'SEND'
    STOP = 'STOP'

class SendButton(QPushButton):
    def __init__(self):
        super().__init__()
        self._state: InputState = InputState.SEND
        self.setObjectName('InputSendButton')
    
    @property
    def state(self):
        return self._state
    
    @state.setter
    def state(self, new_value: InputState):
        self._state = new_value
        self.update()
    
    def update(self) -> None:
        if self._state == InputState.SEND:
            self.setText('↑')
        elif self._state == InputState.STOP:
            self.setText('■')
        return super().update()

class InputTextEdit(QTextEdit):
    def __init__(self, formatter: Formatter):
        super().__init__(placeholderText='在这里和 AI 聊天...')
        self.setObjectName('InputTextedit')
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Minimum
        )
        self.document().documentLayout().documentSizeChanged.connect(self.input_textedit_ondocuentSizeChanged)
        self.formatter = formatter

    def input_textedit_ondocuentSizeChanged(self, size):  # 用来约束文本框使得高度随内容自适应
        if size.height() < self.formatter.chat_window_max_input_area_height:
            self.setFixedHeight(size.height())
        else:
            self.setFixedHeight(self.formatter.chat_window_max_input_area_height)

class InputArea(QWidget):
    send = Signal()
    def __init__(self, formatter: Formatter):
        super().__init__()
        # ----------- 文本输入区域 ------------------------------------------------------------------
        self.setObjectName('InputArea')
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Minimum
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # ← 缺少这一行！
        area_layout = QGridLayout(self)

        # ----------- 发送按钮 ------------------------------------------------------------------
        self.send_button = SendButton()
        self.send_button.state = InputState.SEND
        self.send_button.pressed.connect(self.send.emit)
        area_layout.addWidget(self.send_button, 0, 1, alignment=Qt.AlignmentFlag.AlignBottom)

        # ----------- 文本输入框 ------------------------------------------------------------------
        self.textedit = InputTextEdit(formatter)  # 文本输入部分
        area_layout.addWidget(self.textedit, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)

        self.setMinimumHeight(120)

        # 点击 input_area 空白处时，激活文本输入框
        self.installEventFilter(self)
        # 拦截回车：Enter 发送，Shift+Enter 换行
        self.textedit.installEventFilter(self)

    @property
    def text(self) -> str:
        return self.textedit.toMarkdown()
    
    @text.setter
    def text(self, new_text: str):
        self.textedit.setMarkdown(new_text)
    
    @property
    def state(self) -> str:
        return self.send_button.state
    
    @state.setter
    def state(self, new_state: InputState):
        self.send_button.state = new_state

    def eventFilter(self, obj, event):
        # 点击 input_area 空白区域时，激活文本输入框
        if obj is self:
            if event.type() == QEvent.Type.MouseButtonPress:
                self.textedit.setFocus()
                return True
            
        # 输入框：Enter 发送，Shift+Enter 换行
        if obj is self.textedit:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                        self.send.emit()
                        return True
        return super().eventFilter(obj, event)
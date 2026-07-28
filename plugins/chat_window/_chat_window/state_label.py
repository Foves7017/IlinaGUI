from enum import Enum
from PySide6.QtWidgets import QPushButton
class StateLabelText(str, Enum):
    IDLE = '空闲'
    CONNECTING = '连接API服务中...'
    TRANSPORTING = '传输信息流中...'

class StateLabel(QPushButton):
    def __init__(self):
        super().__init__()
        self.state = StateLabelText.IDLE
        self.setObjectName('StateLabel')

    @property
    def state(self) -> StateLabelText:
        return self._state

    @state.setter
    def state(self, new_state: StateLabelText):
        self._state = new_state
        self.setText(self._state)
        self.setProperty('state', self._state)
        # 通知样式引擎「这个 widget 的属性变了，重新匹配选择器」
        self.style().unpolish(self)
        self.style().polish(self)
    
    
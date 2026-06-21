from PySide6.QtWidgets import QLabel

from QSS import qss_formatter, QSSFiles

class WorkPathBar(QLabel):
    def __init__(self):
        super().__init__()
        self._workpath: str = ''
        qss_formatter.add_widget(self, 'WorkPathBar', QSSFiles.chat_window)
    
    @property
    def workpath(self) -> str:
        return self._workpath
    
    @workpath.setter
    def workpath(self, new_value: str):
        self._workpath = new_value
        self.setText(f'当前工作目录：{self._workpath}')

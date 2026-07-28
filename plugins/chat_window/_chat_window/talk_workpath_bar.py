from PySide6.QtWidgets import QLabel

class WorkPathBar(QLabel):
    def __init__(self):
        super().__init__()
        self._workpath: str = ''
        self.setObjectName('WorkPathBar')
    
    @property
    def workpath(self) -> str:
        return self._workpath
    
    @workpath.setter
    def workpath(self, new_value: str):
        self._workpath = new_value
        self.setText(f'当前工作目录：{self._workpath}')

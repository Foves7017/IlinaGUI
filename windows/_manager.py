# 对话管理器窗口（主窗口）

from PySide6 import QtWidgets

class ManagerWindow(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(ManagerWindow, self).__init__(parent)

        self.setWindowTitle('ILINA')
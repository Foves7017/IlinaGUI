from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtGui import QFont

from globals import app_path

class Loading(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel('Ilina GUI')
        self.info = QLabel('正在加载中')

        # title：大一点，Maple Mono NF CN，粗体，颜色 #0F0F1F
        title_font = QFont('Maple Mono NF CN', 36)
        title_font.setBold(True)
        self.title.setFont(title_font)
        self.title.setStyleSheet('color: #8080FF;')

        # info：大小不变，Maple Mono NF CN，不加粗，颜色 #0F0F1F
        info_font = QFont('Maple Mono NF CN')
        info_font.setBold(False)
        self.info.setFont(info_font)
        self.info.setStyleSheet('color: #8080FF;')

        layout = QVBoxLayout(self)
        layout.setSpacing(0)

        layout.addStretch(0)
        # 两个文本水平居中对齐
        layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.info, alignment=Qt.AlignmentFlag.AlignHCenter)
        # 去掉 title 与 info 之间的间距，让字体贴在一起
        layout.addStretch(0)

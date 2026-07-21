PLUGIN_DISPLAY_NAME = '测试'

CONNECTED_FILES = ['*.py', '*.md']

from PySide6.QtWidgets import QWidget

class ContentWidget(QWidget):
    def __init__(self, init):
        super().__init__()

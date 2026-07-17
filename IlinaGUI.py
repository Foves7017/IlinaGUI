import sys
from pathlib import Path

from FovesLog import setup_log
from FovesConfig import ConfigLoader

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from utils import app_dir
from window.manager.manager import Manager

if __name__ == "__main__":
    setup_log(log_floder=app_dir()/'logs')

    app_argv = sys.argv[:]

    if sys.platform == 'win32':
        app_argv += ['-platform', 'windows:darkmode=2']    

    app = QApplication(app_argv) 

    # 加载字体
    font_dir = app_dir() / 'fonts'
    for ext in ('*.ttf', '*.otf'):
        for font_file in font_dir.glob(ext):
            QFontDatabase.addApplicationFont(str(font_file))

    # 创建窗口和信号连接
    form = Manager(sys.argv)
    app.styleHints().colorSchemeChanged.connect(form._on_color_scheme_changed)
    form.show()

    sys.exit(app.exec())
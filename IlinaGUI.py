import sys
from FovesLog import setup_log

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from utils import app_dir
from window.window_base.window_base import WindowBase

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
    form = WindowBase()
    app.styleHints().colorSchemeChanged.connect(form._on_color_scheme_changed)
    form.show()

    sys.exit(app.exec())
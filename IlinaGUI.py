# 启动 Magager 的入口
from FovesLog import setup_log
import os
import sys
import datetime 
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from windows import ChatWindow
from QSS.color_loader import QSSFormatter
from utils import app_dir

DEFAULT_SAVE_PATH = r'.ilina'

import ctypes

if getattr(sys, "frozen", False):
    ctypes.windll.kernel32.AllocConsole()
    ctypes.windll.user32.ShowWindow(
        ctypes.windll.kernel32.GetConsoleWindow(),
        0
    )


if __name__ == '__main__':
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")

    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

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
    if len(sys.argv) > 1:
        if os.path.isfile(sys.argv[1]) or sys.argv[1].endswith('.ilinatree'):
            file_path = sys.argv[1]
        else:
            file_path = os.path.join(sys.argv[1], datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")+'.ilinatree') 
    else:
        file_path = os.path.join(DEFAULT_SAVE_PATH, datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")+'.ilinatree')
    print(f'{file_path=}')
    form = ChatWindow(file_path)
    app.styleHints().colorSchemeChanged.connect(form._on_color_scheme_changed)

    form.show()

    sys.exit(app.exec())
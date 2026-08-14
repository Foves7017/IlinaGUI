import sys

from FovesLog import setup_log

from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtGui import QFontDatabase


from globals import app_path
from main_window.main_window import MainWindow
from ilina_app import IlinaApp

if __name__ == "__main__":
    # 1. 初始化日志系统
    setup_log(log_floder=app_path()/'logs')

    # 2. 创建 app
    app_argv = sys.argv[:]
    if sys.platform == 'win32':
        app_argv += ['-platform', 'windows:darkmode=2']    
    app = IlinaApp(app_argv) 

    # 3. 设置主题
    QQuickStyle.setStyle("Fusion")
    app.setStyle("Fusion")

    # 4. 加载字体
    font_dir = app_path() / 'fonts'
    for ext in ('*.ttf', '*.otf'):
        for font_file in font_dir.rglob(ext):
            QFontDatabase.addApplicationFont(str(font_file))

    # 创建窗口和信号连接
    form = MainWindow()
    form.show()

    sys.exit(app.exec())
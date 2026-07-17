from utils import app_dir
from pydantic import BaseModel

ACTIVEBAR_QML_PATH = str(app_dir()/'layout'/'qml'/'active_bar.qml')
SPLITTER_QSS_PATH = str(app_dir()/'layout'/'qss'/'splitter.qss')

MANAGER_CONFIG_PATH = app_dir()/'configs'/'manager_window.json'

class ManagerConfig(BaseModel):
    pass
from utils import app_dir
from pydantic import BaseModel

ACTIVEBAR_QML_PATH = str(app_dir()/'layout'/'qml'/'active_bar.qml')
DOCK_MANAGER_QSS_PATH = str(app_dir()/'layout'/'qss'/'dock_manager.qss')

MANAGER_CONFIG_PATH = app_dir()/'configs'/'manager_window.json'

class ManagerConfig(BaseModel):
    dock_state: str = ''
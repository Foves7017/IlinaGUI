from uuid import UUID
from utils import app_dir, config_dir
from pydantic import BaseModel

ACTIVEBAR_QML_PATH = str(app_dir()/'manager'/'active_bar.qml')
DOCK_MANAGER_QSS_PATH = str(app_dir()/'manager'/'dock_manager.qss')
MANAGER_YAML_PATH = str(app_dir()/'manager'/'manager_window.yaml')

MANAGER_CONFIG_PATH = config_dir()/'manager_window.json'

class ManagerConfig(BaseModel):
    dock_state: str = ''
    created_docks: dict[UUID, str] = {}
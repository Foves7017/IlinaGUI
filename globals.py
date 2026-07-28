from sys import argv
from pathlib import Path

from FovesConfig import ConfigLoader

from app_config import APP_CONFIG_PATH, AppConfig

print(f'import theme')
from theme_manager import get_theme_manager

print(f'import dock manager')
from manager.dock_manager import get_dock_manager

print(f'import plugin manager')
from plugins.plugin_manager import get_plugin_manager

def get_workspace() -> Path:
    config = ConfigLoader(APP_CONFIG_PATH, AppConfig).readonly()
    workspace: Path = Path(config.latest_workspace or config.default_workspace)
    if len(argv) > 1:
        path = Path(argv[1])
        if path.is_dir():
            workspace = path
        elif path.is_file():
            workspace = path.parent
    return workspace
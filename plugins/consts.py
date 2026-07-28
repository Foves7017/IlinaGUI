from uuid import UUID
from typing import Any
from dataclasses import dataclass
from layout.formatter import Formatter
from .plugin_manager import PluginManager

@dataclass
class InitParam:
    uuid: UUID|None
    workspace: str
    open_file: str|None
    formatter: Formatter
    plugin_manager: PluginManager
    dock_manager: Any
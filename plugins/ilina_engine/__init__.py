from IlinaEngine._paths import PROVIDER_CONFIG_PATH, MCP_CONFIG_PATH, ENGINE_CONFIG_PATH, EngineConfig
from IlinaEngine.api.providers import SaveData as provider_savedata
from IlinaEngine.mcp_client import SaveData as mcp_savedata
from .content import ContentWidget, hook

from ..consts import SettingItem

PLUGIN_DISPLAY_NAME = '对话树'

CONNECTED_FILES = '*.ilinatree'

ACTIVE_BAR_ICON_CHARA = chr(62323)

ACTIVE_BAR_CLICK_HOOK = hook

SETTINGS = [
    SettingItem(
        name='供应商设置',
        config_filepath=PROVIDER_CONFIG_PATH,
        config_model=provider_savedata
    ),
    SettingItem(
        name='MCP 设置',
        config_filepath=MCP_CONFIG_PATH,
        config_model=mcp_savedata
    ),
    SettingItem(
        name='对话引擎设置',
        config_filepath=ENGINE_CONFIG_PATH,
        config_model=EngineConfig
    )
]
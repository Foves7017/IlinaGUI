DISPLAY_NAME = '设置面板'

from globals import plugin_path
THEME_YAML = plugin_path()/'setting_pannel'/'settings_pannel.yaml'

from .content import ContentWidget as DOCK_WIDGET
ACTIVE_BAR_ICON_CHARA = chr(60052)
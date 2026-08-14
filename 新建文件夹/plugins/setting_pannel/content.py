from uuid import UUID
from pathlib import Path
from typing import Type
from pydantic import BaseModel

from PySide6.QtCore import Slot, Signal, QModelIndex, Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QVBoxLayout, QLabel, QSizePolicy

from globals import ConfigPage, DockInfo
from ilina_app import app_instance

class ContentWidget(QWidget):
    def __init__(self, info: DockInfo):
        super().__init__()

        layout = QHBoxLayout(self)

        self.names = QListWidget()
        self.names.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding
        )
        self.names.setFixedWidth(app_instance().theme_manager.name_list_width)

        self.config_models: dict[str, ConfigPage] = {}
        self.listitems: dict[str, QListWidgetItem] = {}
        for item in [info.config_model for info in app_instance().plugin_manager.plugins.values() if info.config_model]:
            self.config_models[item.name] = item
            self.listitems[item.name] = QListWidgetItem(item.name)
            self.names.addItem(self.listitems[item.name])

        self.names.clicked.connect(self.on_click)

        layout.addWidget(self.names)
        layout.addWidget(QWidget())

    @Slot()
    def on_click(self, index: QModelIndex):
        name = self.names.item(index.row()).text()
        item = self.config_models[name]
        layout = self.layout()
        if layout:
            if layout.count() > 1:
                widget = layout.takeAt(1)
                if widget:
                    widget = widget.widget()
                    if widget:
                        widget.deleteLater()
            widget = ConfigFile(item.config_filepath, item.config_model)
            layout.addWidget(widget)
                
class ConfigFile(QWidget):
    def __init__(self, savepath: str|Path, savemodel: Type[BaseModel]):
        super().__init__()

        savepath = Path(savepath)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel(text=savemodel.__name__)

        layout.addWidget(title)

        # if savepath.exists() and savepath.is_file():
        #     data = savemodel.model_validate_json(savepath.read_text('UTF8'))
        # else:
        #     data = savemodel()

        # for field_name, field_type in savemodel.model_fields.items():
            # print(field_type, field_name, f'{field_type.annotation}')
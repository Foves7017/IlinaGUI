import os
from pathlib import Path
from logging import getLogger
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QObject, Property, Signal, QDirIterator, QByteArray
from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtQuickWidgets import QQuickWidget

from plugins.consts import InitParam

QML_FILEPATH = r'plugins\file_manager\qml\page.qml'
YAML_PATH = r'plugins\file_manager\yaml.yaml'

class Backend(QObject):
    view_content_signal = Signal()
    double_click_item = Signal(str)

    def __init__(self, 
                 workspace: str,
                 plug_model: QStandardItemModel,
                 file_model: QStandardItemModel,
                 ) -> None:
        super().__init__()
        self._workspace = workspace
        self._view_content = False
        self._plug_model = plug_model
        self._file_model = file_model

    @Property(QObject, constant=True)
    def plug_model(self):
        return self._plug_model
    
    @Property(QObject, constant=True)
    def file_model(self):
        return self._file_model

    @Property(str, constant=True)
    def workspace(self):
        return self._workspace
    
    @Property(bool, notify=view_content_signal)
    def view_content(self): # pyright: ignore[reportRedeclaration]
        return self._view_content
    
    @view_content.setter
    def view_content(self, value: bool):
        self._view_content = value
        self.view_content_signal.emit()

class ContentWidget(QQuickWidget):
    def __init__(self, init_param: InitParam):
        super().__init__()
        self.setClearColor(Qt.GlobalColor.transparent)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

        self.uuid = init_param.uuid
        self.log = getLogger(f'文件管理插件[{str(self.uuid).split('-')[-1]}]')
        self.filenames: list[str] = []

        # 创建文件模型
        self.file_model = QStandardItemModel()
        self.file_model.setItemRoleNames({
            Qt.ItemDataRole.DisplayRole: QByteArray(b'display'),
            Qt.ItemDataRole.UserRole + 1: QByteArray(b'filePath')
        }) 
        # 递归工作目录添加元素
        def get_item(path: Path) -> QStandardItem:
            item = QStandardItem(path.name)
            if path.is_file():
                item.setData(path.absolute().as_posix(), Qt.ItemDataRole.UserRole + 1)

            if path.is_dir():
                for _next in path.iterdir():
                    item.appendRow(get_item(Path(_next)))
            
            return item
        for top in Path(init_param.workspace).iterdir():
            self.file_model.appendRow(get_item(top))


        # 插件视图的模型
        self.plugin_model = QStandardItemModel()
        self.plugin_model.setItemRoleNames({
            Qt.ItemDataRole.DisplayRole: QByteArray(b'display'),
            Qt.ItemDataRole.UserRole + 1: QByteArray(b'filePath')
        }) 
        # 遍历插件内容添加元素
        for name, file_filter in init_param.plugin_manager.name_to_extra_name.items():
            plug = QStandardItem(name)

            qdir = QDirIterator(init_param.workspace, file_filter,
                                flags=QDirIterator.IteratorFlag.Subdirectories)
            
            while qdir.hasNext():
                item = qdir.next()
                child = QStandardItem(Path(item).relative_to(init_param.workspace).as_posix())
                child.setData(item, Qt.ItemDataRole.UserRole + 1)
                plug.appendRow(child)
            
            self.plugin_model.appendRow(plug)

        # 设置 QML
        self.backend = Backend(init_param.workspace, self.plugin_model, self.file_model)
        self.backend.double_click_item.connect(lambda x: print(f'双击: {x}'))
        self.rootContext().setContextProperty('backend', self.backend)
        # self.rootContext().setContextProperty("file_root_index", root_index)
        init_param.formatter.add_qml_widget(self, QML_FILEPATH)
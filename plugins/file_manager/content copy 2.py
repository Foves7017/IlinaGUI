import os
from logging import getLogger

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot
from PySide6.QtWidgets import QFileSystemModel, QTreeView
from PySide6.QtQuickWidgets import QQuickWidget

from plugins.consts import InitParam


class GroupedFileModel(QAbstractListModel):
    """按插件名分组的扁平文件列表模型"""

    PluginNameRole = Qt.ItemDataRole.UserRole + 1
    FileNameRole   = Qt.ItemDataRole.UserRole + 2
    FilePathRole   = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[dict] = []

    def roleNames(self):
        return {
            self.PluginNameRole: b"pluginName",
            self.FileNameRole:   b"fileName",
            self.FilePathRole:   b"filePath",
        }

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self._items):
            return None
        item = self._items[index.row()]
        if role == self.PluginNameRole:
            return item["pluginName"]
        elif role == self.FileNameRole:
            return item["fileName"]
        elif role == self.FilePathRole:
            return item["filePath"]
        return None

    def set_items(self, items: list[dict]):
        self.beginResetModel()
        self._items = items
        self.endResetModel()

class QMLBackend:
    def __init__(self,
                 workspacePath: str,
                 treeModel: QFileSystemModel,
                 groupedModel: GroupedFileModel
                 ) -> None:
        self.workspacePath: str = workspacePath
        self.viewMode: int = 1
        self.treeModel = treeModel
        self.groupedModel = groupedModel
    
    @Slot()
    def toggleViewMode(self):
        print(f'toggle_view_mode {self.viewMode=}')
    
    @Slot()
    def openFileByIndex(self, row, col):
        print(f'open_file_by_index {row=} {col=}')

    @Slot()
    def openGroupedFile(self, index):
        print(f'open_grouped_file {index=}')

class ContentWidget(QQuickWidget):
    def __init__(self, init_param: InitParam):
        super().__init__()
        self.uuid = init_param.uuid
        self.log = getLogger(f'文件管理插件[{str(self.uuid).split('-')[-1]}]')
        self.plugin_manager = init_param.plugin_manager

        self.setClearColor(Qt.GlobalColor.transparent)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

        # 从插件管理器中获取所有关联的扩展名
        connect_exts = []
        for exts in init_param.plugin_manager.name_to_extra_name.values():
            connect_exts.extend(exts)
        self.log.info(f'当前使用的过滤器：{connect_exts}')

        # 创建文件模型（目录树用）
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(init_param.workspace)
        self.file_model.setNameFilters(connect_exts)
        self.file_model.setNameFilterDisables(False)

        # 创建分组列表模型（扩展名分类用）
        self.file_list_model = GroupedFileModel(self)

        self.backend = QMLBackend(init_param.workspace, self.file_model, self.file_list_model)

        # self.setSource('plugins/file_manager/page.qml')
        init_param.formatter.add_qml_widget(self, 'plugins/file_manager/page.qml')
        self.rootContext().setContextProperty('backend', self.backend)

        # 监听文件变动，自动刷新分组列表
        self.file_model.directoryLoaded.connect(lambda _: self._update_listmodel())
        self.file_model.rowsInserted.connect(
            lambda parent, first, last: self._update_listmodel()
        )
        self.file_model.rowsRemoved.connect(
            lambda parent, first, last: self._update_listmodel()
        )
        self.file_model.fileRenamed.connect(
            lambda path, old, new: self._update_listmodel()
        )

        # 初始构建
        self._update_listmodel()

    def _update_listmodel(self):
        """根据 file_model 的当前文件系统状态更新 file_list_model"""
        items: list[dict] = []

        # 构建 扩展名 → 插件名 的映射
        ext_to_plugin: dict[str, str] = {}
        for plugin_name, exts in self.plugin_manager.name_to_extra_name.items():
            for ext in exts:
                ext_to_plugin[ext.lstrip("*")] = plugin_name

        # 遍历工作目录，收集所有匹配扩展名的文件
        workspace = self.file_model.rootPath()
        for dirpath, _dirnames, filenames in os.walk(workspace):
            for fname in filenames:
                ext = os.path.splitext(fname)[1]
                plugin_name = ext_to_plugin.get(ext)
                if plugin_name is not None:
                    full_path = os.path.join(dirpath, fname)
                    items.append({
                        "pluginName": self.plugin_manager.get_display_name_by_name(plugin_name),
                        "fileName":   fname,
                        "filePath":   full_path,
                    })

        # 按 pluginName 排序，同一插件的文件聚合在一起
        items.sort(key=lambda x: x["pluginName"])

        self.file_list_model.set_items(items)
        self.log.debug(f'分组列表已更新，共 {len(items)} 个文件')

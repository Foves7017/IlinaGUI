from typing import Dict
from uuid import UUID
from logging import getLogger
from datetime import datetime

from IlinaEngine import Engine, IlinaMessage
from PySide6.QtCore import QByteArray, QModelIndex, QObject, Property, Signal, Qt, QAbstractListModel, QThread, Slot
from PySide6.QtQuickWidgets import QQuickWidget

from utils import get_short_uuid, plugin_dir
from globals import get_workspace, get_theme_manager
from .invokeworker import InvokeWorker

QML_FILEPATH = str(plugin_dir()/'ilina_engine'/'page.qml')

class IlinaMessageListModel(QAbstractListModel):
    ROLE = Qt.ItemDataRole.UserRole + 1
    CONTENT = Qt.ItemDataRole.UserRole + 2
    REASONING_CONTENT = Qt.ItemDataRole.UserRole + 3
    ROLE_NORMAL_COLOR = Qt.ItemDataRole.UserRole + 4
    ROLE_EXTRA_COLOR = Qt.ItemDataRole.UserRole + 5

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.messages: list[IlinaMessage] = []

    def rowCount(self, parent: QModelIndex=QModelIndex()) -> int:
        return len(self.messages)

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.ROLE: QByteArray(b'role'),
            self.CONTENT: QByteArray(b'content'),
            self.REASONING_CONTENT: QByteArray(b'reasoning_content'),
            self.ROLE_NORMAL_COLOR: QByteArray(b'role_normal_color'),
            self.ROLE_EXTRA_COLOR: QByteArray(b'role_extra_color'),
        }

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        item = self.messages[index.row()]
        if role == self.ROLE:
            return item.role
        elif role == self.CONTENT:
            return item.content
        elif role == self.REASONING_CONTENT:
            return item.reasoning_content
        elif role == self.ROLE_NORMAL_COLOR:
            return getattr(get_theme_manager(), f'role_{item.role}_normal_color')
        elif role == self.ROLE_EXTRA_COLOR:
            return getattr(get_theme_manager(), f'role_{item.role}_extra_color')
        return None

class Backend(QObject):
    send_button_pressed = Signal(str)

    def __init__(self, engine: Engine) -> None:
        super().__init__()
        self._engine = engine

        self.send_button_pressed.connect(self.on_start_chat)

    @Property(IlinaMessage)
    def message_list(self):
        return self._engine.message_list

    @Slot()
    def on_new_message(self, new_message: IlinaMessage):
        print(new_message)

    @Slot()
    def on_start_chat(self, user_prompt: str):
        self._engine.chat(user_prompt)
        self.start_invoke()

    def start_invoke(self):
        """ 开始通过 worker 接受消息 """
        # 创建 worker 和线程
        self.worker_thread = QThread()
        self.worker_thread.setObjectName('Receive Engine Event')
        self.invoke_worker = InvokeWorker(self._engine)
        self.invoke_worker.moveToThread(self.worker_thread)

        # 关联信号
        self.worker_thread.started.connect(self.invoke_worker.run)  # 线程开始 -> worker 工作
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)  # 线程结束 -> 删除线程
        # self.invoke_worker.event_received.connect(self.on_engine_event)  # worker 收到事件 -> self.on_engine_event
        self.invoke_worker.event_received.connect(self.on_new_message)  # worker 收到事件 -> self.on_engine_event
        self.invoke_worker.finished.connect(self.worker_thread.quit)  # worker 完成 -> 线程结束
        self.invoke_worker.finished.connect(self.invoke_worker.deleteLater)  # worker 完成 -> 删除worker
        # self.invoke_worker.finished.connect(self.on_invoke_worker_finished)  # worker 完成 -> 通知主窗口切换按钮
        # 开始线程 
        self.worker_thread.start()

class ContentWidget(QQuickWidget):
    def __init__(self, uuid: UUID, open_file: str|None):
        super().__init__()
        assert open_file
        self.log = getLogger(f'IlinaEngine@{get_short_uuid(uuid)}')

        self.uuid = uuid
        self.file = open_file

        self.ilina_engine = Engine(open_file)

        self.message_list_model = IlinaMessageListModel()
        self.message_list_model.messages = self.ilina_engine.message_list

        # 设置透明背景
        self.setClearColor(Qt.GlobalColor.transparent)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
        # 设置 QML
        self.backend = Backend(self.ilina_engine)
        self.rootContext().setContextProperty('backend', self.backend)
        self.rootContext().setContextProperty('ilina_message_list_model', self.message_list_model)
        get_theme_manager().add_qml_widget(self, QML_FILEPATH)

def hook():
    ilina = get_workspace()/'.ilina'
    ilina.mkdir(exist_ok=True)
    return (ilina/f'{datetime.now().strftime('%Y_%m_%d_%H_%M_%S.ilinatree')}').as_posix()

from typing import Callable
from uuid import UUID
from IlinaEngine import Engine, NodeEvent, NodeEventTypes, IlinaMessage
from FovesConfig import ConfigLoader
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Qt, QByteArray, Slot, QTimer, QThread, QEvent
from PySide6.QtWidgets import QSplitter, QSizePolicy, QWidget, QVBoxLayout, QMessageBox

from ._window_base import WindowBase
from ._chat_window.tree_area import TreeArea
from ._chat_window.input_area import InputArea, InputState
from ._chat_window.scroll_area import ScrollArea
from ._chat_window.title_label import TitleLabel
from ._chat_window.state_label import StateLabel, StateLabelText
from ._chat_window.invoke_worker import InvokeWorker
from ._chat_window.tree_float_window import TreeFloatWindow
from ._chat_window.talk_workpath_bar import WorkPathBar

from QSS import QSSFiles, qss_formatter
from .types import WindowConfig
from utils import app_dir

CONFIG_PATH = app_dir()/'configs'/'window.json'

class ChatWindow(WindowBase):
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__()
        self.loading_label.setText(f'Now Loading...\n\n正在创建界面')
        QTimer.singleShot(1, self._setup_content)

    def _setup_content(self):
        """ 加载界面元素，之所以专门整个函数是为了放在 singleShot 里，其实我也不知道这样能不能加载更快
        """
        # 改变显示文字

        # 创建分割区域并作为主区域
        self._setup_splitter()
        self.root_layout.addWidget(self.splitter)

        # 设置标题
        self.title_label = TitleLabel()
        self.titlebar_layout.insertWidget(0, self.title_label)

        # 设置状态文本
        self.state_label = StateLabel()
        self.titlebar_layout.insertWidget(1, self.state_label)

        # 创建浮动窗口
        self.tree_float_window = TreeFloatWindow()

        # 让窗口启动后再加载引擎
        self.loading_label.setText(f'Now Loading...\n\n界面创建完成\n正在设置 Ilina Engine')
        QTimer.singleShot(0, self._setup_engine)

    def _setup_engine(self):
        """ 初始化引擎并设置各种东西 """

        try:
            self.engine = Engine(self.filename)
        except Exception as e:
            self.loading_label.setText(f"Ilina Engine 报告了一个错误\n{repr(e)}")
            return

        self.title_label.label = self.engine.name  # 标题
        self.workpath_label.workpath = self.engine.workpath  # 工作目录
        self.scroll_area.add_messages(*self.engine.message_list)  # 消息

        # 引擎加载好之后载入 QSS
        self.loading_label.setText(f'Now Loading...\n\n界面创建完成\nIlina Engine 已启动\n正在载入样式')
        QTimer.singleShot(0, lambda: self.reload_style(self.after_first_reload_style))

    def after_first_reload_style(self):
        """ 第一次重载 QSS 的回调 """
        self.loading_label.deleteLater()

        # 有这个函数最开始是因为这个 ↓ 放在设置引擎的时候线条颜色会不对
        self.tree_area.draw(self.engine.readonly_root_node, self.engine.readonly_leaves)

        # 连接各种事件
        # 树状图的事件
        self.tree_area.tree_node_click.connect(self.on_tree_node_click)
        self.tree_area.tree_node_enter.connect(self.on_tree_node_enter)
        self.tree_area.tree_node_left.connect(self.on_tree_node_left)
        # 点击状态标签重载
        self.state_label.pressed.connect(self.on_reload_clicked)
        # 编辑标题重命名
        self.title_label.label_edited.connect(lambda name:self.engine.set_name(name))
        # 发送按钮
        self.input_area.send.connect(self.on_send_pressed)
        # 浮动窗口的几个按钮
        self.tree_float_window.edit_node.connect(self.start_edit_node)
        self.tree_float_window.delete_node.connect(self.delete_node)
        self.tree_float_window.move_to_node.connect(lambda target: self.move_to_node(target, True))
        self.tree_float_window.invoke_from_node.connect(self.invoke_from_node)
        # 来自滚动区的事件
        self.scroll_area.start_edit_node.connect(self.start_edit_node)
        self.scroll_area.edit_finished.connect(self.finished_edit_node)
        self.scroll_area.invoke_from_node.connect(self.invoke_from_node)

        # 遍历Engine的警告列表，弹窗警告
        for item in self.engine.warning_list:
            self.log.warning(f'Ilina Engine 发出警告：{item}')
            QMessageBox.warning(self, 'Ilina Engine 发出的警告', item)

    def _setup_splitter(self):
        """ 创建分割区域 """
        # 创建分割区域本身
        self.splitter = QSplitter()
        qss_formatter.add_widget(self.splitter, 'Splitter', QSSFiles.chat_window)

        # 创建左侧的树视图
        self.tree_area = TreeArea()
        self.splitter.addWidget(self.tree_area)

        # 创建右侧的对话视图
        self._setup_talk_area()
        self.splitter.addWidget(self.talk_area)

        # 从设置里导入 spliter 的分配信息
        config = ConfigLoader(CONFIG_PATH, WindowConfig).readonly()
        if config.chat_splitter_state == '':
            self.splitter.setSizes([300, 400])
        else:
            self.splitter.restoreState(QByteArray.fromBase64(config.chat_splitter_state.encode()))
        self.splitter.splitterMoved.connect(self.on_splitter_moved)
    

    def _setup_talk_area(self):
        """ 创建对话区域 """
        # 创建对话区域本身
        self.talk_area = QWidget()
        qss_formatter.add_widget(self.talk_area, 'TalkArea', QSSFiles.chat_window)
        self.talk_area.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        talk_area_layout = QVBoxLayout(self.talk_area)

        # 创建工作目录显示条
        self.workpath_label = WorkPathBar()
        talk_area_layout.addWidget(self.workpath_label)

        # 创建滚动区
        self.scroll_area = ScrollArea()
        talk_area_layout.addWidget(self.scroll_area)

        # 创建输入区
        self.input_area = InputArea()
        talk_area_layout.addWidget(self.input_area, alignment=Qt.AlignmentFlag.AlignBottom)
    
    def start_invoke(self, start_from: UUID|None=None):
        """ 开始通过 worker 接受消息 """
        # 设置状态标题为连接中
        self.state_label.state = StateLabelText.CONNECTING
        # 设置按钮文字
        self.input_area.state = InputState.STOP
        # 创建 worker 和线程
        self.worker_thread = QThread()
        self.worker_thread.setObjectName('Receive Engine Event')
        self.invoke_worker = InvokeWorker(self.engine, start_from)
        self.invoke_worker.moveToThread(self.worker_thread)

        # 关联信号
        self.worker_thread.started.connect(self.invoke_worker.run)  # 线程开始 -> worker 工作
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)  # 线程结束 -> 删除线程
        self.invoke_worker.event_received.connect(self.on_engine_event)  # worker 收到事件 -> self.on_engine_event
        self.invoke_worker.error.connect(self.on_invoke_worker_error)  # worker 发生错误 -> self.on_invoke_worker_error
        self.invoke_worker.finished.connect(self.worker_thread.quit)  # worker 完成 -> 线程结束
        self.invoke_worker.finished.connect(self.invoke_worker.deleteLater)  # worker 完成 -> 删除worker
        self.invoke_worker.finished.connect(self.on_invoke_worker_finished)  # worker 完成 -> 通知主窗口切换按钮
        # 开始线程 
        self.worker_thread.start()

    @Slot()
    def on_invoke_worker_finished(self):
        # 切换状态栏
        self.state_label.state = StateLabelText.IDLE
        # 切换按钮
        self.input_area.state = InputState.SEND
        self.tree_area.draw(self.engine.readonly_root_node, self.engine.readonly_leaves)

    @Slot()
    def on_invoke_worker_error(self, error: str):
        self.state_label.state = StateLabelText.IDLE
        self.input_area.state = InputState.SEND
        self.log.error(f'invoke_worker_error: {error}')

    @Slot()
    def on_engine_event(self, call_event: NodeEvent):
        self.state_label.state = StateLabelText.TRANSPORTING

        if call_event._type == NodeEventTypes.CREATED:  # 创建节点
            self.scroll_area.add_messages([call_event.node.uuid], [call_event.node.message])
            self.tree_area.draw(self.engine.readonly_root_node, self.engine.readonly_leaves)

        elif call_event._type == NodeEventTypes.UPDATED:
            self.scroll_area.update_item(call_event.node.uuid, call_event.node.message)
            self.scroll_area.target_scroll_uuid = None
            

        elif call_event._type == NodeEventTypes.ERROR:
            self.scroll_area.add_messages([call_event.node.uuid], [call_event.node.message])
            self.log.error(f'引擎产出了错误事件：\n{call_event.node.message.content}')
            return

    @Slot()
    def on_reload_clicked(self):
        self.reload_style()
        self.tree_area.draw(self.engine.readonly_root_node, self.engine.readonly_leaves)

    @Slot()
    def on_splitter_moved(self):  # 记录Splitter的位置
        with ConfigLoader(CONFIG_PATH, WindowConfig) as conf:
            conf.chat_splitter_state = self.splitter.saveState().toBase64().data().decode()   # pyright: ignore[reportAttributeAccessIssue]
    
    @Slot()
    def on_tree_node_enter(self, node_uuid: UUID):
        if not self.tree_float_window.Clicked:
            self.tree_float_window.set_node(node_uuid, self.engine.get_message_by_uuid(node_uuid))
            self.tree_float_window.show()
    
    @Slot()
    def on_tree_node_left(self, uuid: UUID):
        if not self.tree_float_window.Clicked:
            self.tree_float_window.hide()

    @Slot()
    def on_tree_node_click(self, uuid: UUID):
        try:
            self.tree_float_window.Clicked = True
            self.tree_float_window.set_node(uuid, self.engine.get_message_by_uuid(uuid))

            if uuid in self.scroll_area:
                self.scroll_area.target_scroll_uuid = uuid
                self.scroll_area.auto = True
        except IndexError:
            pass
    
    @Slot()
    def send_message(self):
        """ 发送消息。但如果 content 为空就返回 False，表示其实未发送 """
        content = self.input_area.text
        user_message = IlinaMessage(role='user', content=content)
        if content != '':
            new_node_uuid = self.engine.send(user_message)
            self.scroll_area.add_messages([new_node_uuid], [user_message])
            self.tree_area.draw(self.engine.readonly_root_node, self.engine.readonly_leaves)
            self.scroll_area.target_scroll_uuid = new_node_uuid
            self.scroll_area.auto = True
            # QTimer.singleShot(0, self.scroll_area.scroll_to_bottom)
            self.input_area.text = ''
            self.start_invoke()
            return True
        else:
            return False

    @Slot()
    def on_send_pressed(self):
        if self.state_label.state == StateLabelText.IDLE:
            if not self.send_message():  # 如果其实未发送就直接返回，什么都不做
                return
            self.input_area.state = InputState.SEND
        else:
            self.invoke_worker.stop_flag = True
    
    @Slot()
    def move_to_node(self, target_uuid: UUID, load_all: bool):
        self.engine.move_to_node(target_uuid)
        self.tree_float_window.Clicked = False
        self.tree_float_window.hide()
        self.tree_area.draw(self.engine.readonly_root_node, self.engine.readonly_leaves)
        self.scroll_area.clear()

        if load_all:
            self.scroll_area.add_messages(*self.engine.message_list)
        else:
            uuids, messages = self.engine.message_list
            uuid_index = uuids.index(target_uuid)
            if self.engine.get_message_by_uuid(target_uuid).role != 'assistant':
                uuid_index += 1
            self.scroll_area.add_messages(uuids[:uuid_index], messages[:uuid_index])
        
        self.scroll_area.target_scroll_uuid = target_uuid
        self.scroll_area.auto = True
    
    @Slot()
    def delete_node(self, target: UUID):
        self.engine.delete_node(target)
        self.tree_float_window.Clicked = False
        self.tree_float_window.hide()
        self.tree_area.draw(self.engine.readonly_root_node, self.engine.readonly_leaves)
        if self.state_label.text() == StateLabelText.IDLE:
            self.scroll_area.clear()
            self.scroll_area.add_messages(*self.engine.message_list)
    
    @Slot()
    def invoke_from_node(self, target: UUID):
        self.tree_float_window.Clicked = False
        self.tree_float_window.hide()

        self.tree_area.draw(self.engine.readonly_root_node, self.engine.readonly_leaves)

        self.scroll_area.clear()
        self.move_to_node(target, False)
            
        self.start_invoke(target)

    @Slot()
    def start_edit_node(self, target: UUID):
        if target not in self.scroll_area:
            self.move_to_node(target, True)
        self.scroll_area.start_edit(target)
        self.tree_float_window.hide()
        self.tree_float_window.Clicked = False

    @Slot()
    def finished_edit_node(self, target: UUID, new_message: IlinaMessage, invoke: bool):
        new_node_uuid = self.engine.edit_node(target, new_message)
        self.move_to_node(new_node_uuid, True)
        if invoke:
            self.start_invoke()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.tree_float_window != self.childAt(event.pos()):
            self.tree_float_window.Clicked = False
            self.tree_float_window.hide()
        super().mousePressEvent(event)
    
    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.tree_float_window.Clicked = False
                self.tree_float_window.hide()
        return super().changeEvent(event)
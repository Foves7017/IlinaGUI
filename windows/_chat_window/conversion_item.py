from uuid import UUID
from FovesConfig import ConfigLoader
from pyperclip import copy as copy_to_clip
from PySide6.QtGui import QEnterEvent, QMouseEvent
from PySide6.QtCore import QObject, Slot, QTimer, QEvent, Qt, Signal
from PySide6.QtWidgets import QWidget, QLabel, QSizePolicy, QPushButton, QHBoxLayout, QVBoxLayout
from IlinaEngine.type import IlinaMessage
from typing import cast

from .markdown_browser import MarkdownBrowser

from utils import app_dir
from QSS import qss_formatter, QSSFiles
from ..types import WindowConfig

class ConversionItem(QWidget):
    """ 对话气泡？ """
    edit_finished = Signal(UUID, IlinaMessage, bool)  # 编辑完成的信号
    invoke_from_node = Signal(UUID)
    edit_node = Signal(UUID)

    def __init__(self, node_uuid: UUID, message: IlinaMessage):
        super().__init__()
        self.node_uuid = node_uuid
        self.node_message = message
        self.Editing: bool = False

        # 从设置中读取自动折叠高度备用
        self.max_collapse_height = ConfigLoader(app_dir()/'configs'/'window.json', WindowConfig).readonly().max_collapse_height

        qss_formatter.add_widget(self, 'ConversionItem', QSSFiles.chat_window)

        # 显示角色的部分
        self.roleLabel = QLabel(text=message.role.title())
        qss_formatter.add_widget(self.roleLabel, 'ConversionItemRoleLabel', QSSFiles.chat_window)
        self.roleLabel.setProperty('role', message.role)
        self.roleLabel.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            self.roleLabel.sizePolicy().verticalPolicy(),
        )
        self.roleLabel.setFixedWidth(96)
        self.roleLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # 显示思考的部分，在 role != assistant 或 reasoning_content 为空的时候隐藏
        self.reasoningContentBlock = MarkdownBrowser()
        qss_formatter.add_widget(self.reasoningContentBlock, 'ConversionItemReasoningContentBlock', QSSFiles.chat_window)
        self.reasoningContentBlock.setProperty('role', message.role)
        self.reasoningContentBlock.setSizePolicy(
            self.reasoningContentBlock.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Maximum
        )
        self.reasoningContentBlock.setMarkdown(message.reasoning_content)

        # 显示内容的部分
        self.contentBlock = MarkdownBrowser()
        self.contentBlock.setProperty('role', message.role)
        qss_formatter.add_widget(self.contentBlock, 'ConversionItemContentBlock', QSSFiles.chat_window)
        self.contentBlock.setObjectName('ConversionItemContentBlock')
        self.contentBlock.setSizePolicy(
            self.contentBlock.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Maximum
        )
        # 关联内容按钮的消息实现快捷键
        self.contentBlock.hotkey_save.connect(lambda: self.edit_ok_pressed(False))
        self.contentBlock.hotkey_save_invoke.connect(lambda: self.edit_ok_pressed(True))
        self.contentBlock.hotkey_cancel.connect(self.edit_cancel_pressed)

        # 编辑的确认并生成按钮
        self.edit_ok_invoke_button = QPushButton()
        qss_formatter.add_widget(self.edit_ok_invoke_button, 'ConversionItemButton', QSSFiles.chat_window)
        self.edit_ok_invoke_button.setText('保存并生成')
        self.edit_ok_invoke_button.pressed.connect(lambda: self.edit_ok_pressed(True))

        # 编辑的确认按钮
        self.edit_ok_button = QPushButton()
        qss_formatter.add_widget(self.edit_ok_button, 'ConversionItemButton', QSSFiles.chat_window)
        self.edit_ok_button.setText('保存')
        self.edit_ok_button.pressed.connect(lambda: self.edit_ok_pressed(False))

        # 编辑的取消按钮
        self.edit_cancel_button = QPushButton()
        qss_formatter.add_widget(self.edit_cancel_button, 'ConversionItemButton', QSSFiles.chat_window)
        self.edit_cancel_button.setText('放弃')
        self.edit_cancel_button.pressed.connect(self.edit_cancel_pressed)

        # 编辑按钮区
        self.edit_button_area = QWidget()
        qss_formatter.add_widget(self.edit_button_area, 'ConversionItemButtonArea', QSSFiles.chat_window)
        # 编辑按钮区布局
        edit_button_layout = QHBoxLayout(self.edit_button_area)
        edit_button_layout.setSpacing(0)
        edit_button_layout.setContentsMargins(0, 0, 0, 0)
        edit_button_layout.addWidget(self.edit_ok_invoke_button)
        edit_button_layout.addWidget(self.edit_ok_button)
        edit_button_layout.addWidget(self.edit_cancel_button)
        edit_button_layout.addStretch()

        # 浮动区的“重新生成”按钮
        self.float_restart_button = QPushButton()
        self.float_restart_button.setText(f'重新生成')
        qss_formatter.add_widget(self.float_restart_button, 'ConversionItemButton', QSSFiles.chat_window)
        self.float_restart_button.pressed.connect(self.on_restart_pressed)

        # 浮动区的复制按钮
        self.float_copy_button = QPushButton()
        self.float_copy_button.setText(f' 复制 ')
        qss_formatter.add_widget(self.float_copy_button, 'ConversionItemButton', QSSFiles.chat_window)
        self.float_copy_button.pressed.connect(self.on_copy_pressed)

        # 浮动按钮区
        self.float_button_area = QWidget()
        qss_formatter.add_widget(self.float_button_area, 'ConversionItemButtonArea', QSSFiles.chat_window)
        float_button_layout = QHBoxLayout(self.float_button_area)
        float_button_layout.setSpacing(0)
        float_button_layout.setContentsMargins(0, 0, 0, 0)
        float_button_layout.addWidget(self.float_copy_button)
        float_button_layout.addWidget(self.float_restart_button)
        float_button_layout.addStretch()

        # 设置固定高度
        policy = self.float_copy_button.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.float_copy_button.setSizePolicy(policy)
        # 之所以不再外包一层，是因为我未来想做成那种一个一个按钮逐个浮现的效果。
        self.float_buttons: list[QPushButton] = [
            self.float_copy_button,
            self.float_restart_button,
        ]
        for button in self.float_buttons:
            button.hide()

        # 顶部按钮区的展开按钮
        self.top_expand_button = QPushButton()
        self.top_expand_button.setText('展开')
        qss_formatter.add_widget(self.top_expand_button, 'ConversionItemButton', QSSFiles.chat_window)
        self.top_expand_button.pressed.connect(self.on_expand_pressed)

        # 顶部按钮区的展开思考按钮
        self.top_expand_reasoning_button = QPushButton()
        self.top_expand_reasoning_button.setText('展开思考')
        qss_formatter.add_widget(self.top_expand_reasoning_button, 'ConversionItemButton', QSSFiles.chat_window)
        self.top_expand_reasoning_button.pressed.connect(self.on_reason_expand_pressed)

        # 顶部按钮区
        self.top_button_area = QWidget()
        qss_formatter.add_widget(self.top_button_area, 'ConversionItemButtonArea', QSSFiles.chat_window)
        top_button_layout = QHBoxLayout(self.top_button_area)
        top_button_layout.setSpacing(0)
        top_button_layout.setContentsMargins(0, 0, 0, 0)
        top_button_layout.addWidget(self.top_expand_button)
        top_button_layout.addWidget(self.top_expand_reasoning_button)
        top_button_layout.addStretch()

        # 包括在思考和内容外面的框
        self.contentArea = QWidget()
        self.contentArea.setObjectName('ConversionItemContentArea')
        qss_formatter.add_widget(self.contentArea, 'ConversionItemContentArea', QSSFiles.chat_window)
        self.contentArea.setProperty('role', self.node_message.role)
        self.contentArea.setSizePolicy(
            self.contentArea.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Maximum
        )

        # 思考外面的框的布局
        area_layout = QVBoxLayout(self.contentArea)
        area_layout.setSpacing(0)
        area_layout.setContentsMargins(0, 0, 0, 0)
        area_layout.addWidget(self.top_button_area)
        area_layout.addWidget(self.reasoningContentBlock)
        area_layout.addWidget(self.contentBlock)
        area_layout.addWidget(self.edit_button_area)
        area_layout.addWidget(self.float_button_area)

        # 布局
        root_layout = QHBoxLayout(self)
        root_layout.addWidget(self.roleLabel)
        root_layout.addWidget(self.contentArea)

        self.update_message(message)
        

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.roleLabel:
            if event.type() == QMouseEvent:
                event = cast(QMouseEvent, event)
                print(event.button()==Qt.MouseButton.LeftButton)
        return super().eventFilter(watched, event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.edit_node.emit(self.node_uuid)
        return super().mouseDoubleClickEvent(event)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.float_copy_button.setText(f' 复制 ')
        for button in self.float_buttons:
            button.show()
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        for button in self.float_buttons:
            button.hide()
        return super().leaveEvent(event)

    @Slot()
    def on_expand_pressed(self):
        if self.contentBlock.expand:
            self.edit_cancel_pressed()
        self.contentBlock.expand = not self.contentBlock.expand
        self.update_hide()
    
    @Slot()
    def on_reason_expand_pressed(self):
        self.reasoningContentBlock.expand = not self.reasoningContentBlock.expand
        self.update_hide()

    @Slot()
    def on_restart_pressed(self):
        self.invoke_from_node.emit(self.node_uuid)

    @Slot()
    def on_copy_pressed(self):
        copy_to_clip(self.node_message.content)
        self.float_copy_button.setText(f'已复制')
    
    @Slot()
    def start_edit(self):
        self.contentBlock.setEnabled(True)
        self.Editing = True
        self.update_hide()
        self.contentBlock.show()  # 假设初始内容为空会隐藏，这里单独设置强制显示
        self.contentBlock.expand = True
        self.update_hide()
        QTimer.singleShot(0, self.contentBlock.setFocus)
    
    @Slot()
    def edit_ok_pressed(self, invoke: bool):
        self.contentBlock.setEnabled(False)
        self.Editing = False
        self.update_hide()
        self.node_message.content = self.contentBlock.toMarkdown()
        self.edit_finished.emit(self.node_uuid, self.node_message, invoke)

    @Slot()
    def edit_cancel_pressed(self):
        self.contentBlock.setEnabled(False)
        self.Editing = False
        self.update_hide()
        self.contentBlock.setMarkdown(self.node_message.content)

    def update_message(self, message: IlinaMessage):
        """ 根据节点类型设置消息 """
        # 设置消息
        if self.node_message.role == 'tool':
            self.contentBlock.setPlainText(message.content)
            self.reasoningContentBlock.setPlainText(message.tool_name)
        else:
            self.contentBlock.setMarkdown(message.content)
            self.reasoningContentBlock.setMarkdown(message.reasoning_content)
        # 如果是 tool 和 system 就直接折叠, assistant 的思考也折叠
        if self.node_message.role in ['tool', 'system']:
            self.contentBlock.expand = False
        elif self.node_message.role == 'assistant':
            self.reasoningContentBlock.expand = False
        QTimer.singleShot(0, self.update_hide)
    
    def update_hide(self) -> None:
        """ 刷新各个组件的状态 """
        # 根据节点设置是否显示思考，只有 tool 和 assistant 显示思考
        # 并且，就算显示思考，如果思考内容为空也隐藏
        if self.node_message.role in ['assistant', 'tool']:
            if self.node_message.reasoning_content != '' or self.node_message.tool_name != '':
                self.reasoningContentBlock.show()
            else:
                self.reasoningContentBlock.hide()
        else:
            self.reasoningContentBlock.hide()
        
        # 根据节点内容设置按钮，只有 assistant 且超过高度显示按钮
        self.top_expand_reasoning_button.hide()
        if self.node_message.role == 'assistant':
            if self.reasoningContentBlock.document().size().height() > self.max_collapse_height:
                self.top_expand_reasoning_button.show()
        
        # 如果 content 内容为空就不显示
        if self.node_message.content == '':
            self.contentBlock.hide()
        else:
            self.contentBlock.show()

        # 是否显示功能区按钮，如果展示功能区，就隐藏浮动区
        if self.Editing:
            self.edit_button_area.show()
            self.float_button_area.hide()
        else:
            self.edit_button_area.hide()
            self.float_button_area.show()
        
        # 是否显示隐藏按钮
        if self.contentBlock.document().size().height() > self.max_collapse_height:
            self.top_expand_button.show()
        else:
            self.top_expand_button.hide()

        # 根据文本框展开的情况更新按钮文本
        if self.contentBlock.expand:
            self.top_expand_button.setText('折叠')
        else:
            self.top_expand_button.setText('展开')
        if self.node_message.role == 'assistant':
            if self.reasoningContentBlock.expand:
                self.top_expand_reasoning_button.setText('折叠思考')
            else:
                self.top_expand_reasoning_button.setText('展开思考')
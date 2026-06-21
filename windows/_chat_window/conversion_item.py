from uuid import UUID
from pyperclip import copy as copy_to_clip
from PySide6.QtGui import QEnterEvent, QMouseEvent
from PySide6.QtCore import Slot, QTimer, QEvent, Qt, Signal
from PySide6.QtWidgets import QWidget, QLabel, QSizePolicy, QPushButton, QHBoxLayout, QVBoxLayout
from IlinaEngine.type import IlinaMessage

from .markdown_browser import MarkdownBrowser

from QSS import qss_formatter, QSSFiles

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

        # 包括在思考和内容外面的框
        self.contentArea = QWidget()
        self.contentArea.setObjectName('ConversionItemContentArea')
        qss_formatter.add_widget(self.contentArea, 'ConversionItemContentArea', QSSFiles.chat_window)
        self.contentArea.setSizePolicy(
            self.contentArea.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Maximum
        )

        # 思考外面的框的布局
        area_layout = QVBoxLayout(self.contentArea)
        area_layout.setSpacing(0)
        area_layout.setContentsMargins(0, 0, 0, 0)
        area_layout.addWidget(self.reasoningContentBlock)
        area_layout.addWidget(self.contentBlock)
        area_layout.addWidget(self.edit_button_area)
        area_layout.addWidget(self.float_button_area)

        # 布局
        root_layout = QHBoxLayout(self)
        root_layout.addWidget(self.roleLabel)
        root_layout.addWidget(self.contentArea)

        self.update_message(message)

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
        if self.node_message.role == 'tool':
            # self.contentBlock.setMarkdown('**'+ message.tool_name +'**\n\n'+message.content[:50]+('...' if len(message.content) > 50 else ''))
            self.contentBlock.setMarkdown('**'+ message.tool_name +'**\n\n'+message.content)
        else:
            self.contentBlock.setMarkdown(message.content)
        self.reasoningContentBlock.setMarkdown(message.reasoning_content)
        self.update_hide()
    
    def update_hide(self) -> None:
        # 是否显示思考
        if self.node_message.role != 'assistant':
            self.reasoningContentBlock.hide()
        else:
            if self.node_message.reasoning_content == '':
                self.reasoningContentBlock.hide()
            else:
                self.reasoningContentBlock.show()
        
        # 如果 content 内容未空就不显示
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
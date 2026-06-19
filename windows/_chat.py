import traceback
from FovesConfig import ConfigLoader
from pyperclip import copy as copy_to_clip
from IlinaEngine import Engine
from IlinaEngine.type import IlinaMessage, Node, NodeEventTypes, NodeEvent
from uuid import UUID
from ._window_base import WindowBase
from PySide6 import QtWidgets, QtGraphs
from PySide6.QtGui import (QEnterEvent, QIcon, QKeyEvent, QMouseEvent, QPainter, QPixmap, QColor, QBrush, QPen, QCursor, 
                           QPainterPath)
from PySide6.QtCore import Slot, QTimer, QEvent, QByteArray, QRectF, Qt, Signal, QObject, QThread
from .types import WindowConfig
from QSS import *

from ._chat_window.title_label import TitleLabel
from ._chat_window.markdown_browser import MarkdownBrowser

CONFIG_PATH = 'configs/window.json'

ROLE_COLOR_MAP = {
    'user': qss_formatter.colors.chat_window.role_user_color,
    'assistant': qss_formatter.colors.chat_window.role_assistant_color,
    'tool': qss_formatter.colors.chat_window.role_tool_color,
    'system': qss_formatter.colors.chat_window.role_system_color,
}

class StateLabelText(str, Enum):
    IDLE = '空闲'
    CONNECTING = '连接API服务中...'
    TRANSPORTING = '传输信息流中...'

class InvokeWorker(QObject):
    event_received = Signal(object)
    finished = Signal()
    error = Signal(str)

    def __init__(self, engine: Engine, start_from: UUID|None=None):
        super().__init__()
        self.engine = engine
        self.log = logging.getLogger('InvokeWorker')
        self.stop_flag: bool = False
        self.start_from = start_from

    @Slot()
    def run(self):
        try:
            self.log.info(f'开始调用并接受事件')
            gene = self.engine.invoke(self.start_from)
            for event in gene:
                self.log.debug(f'next event: {event}')
                self.event_received.emit(event)
                send_event = gene.send(self.stop_flag)
                self.log.debug(f'send event: {send_event}')
                self.event_received.emit(send_event)

            self.log.info(f'事件接受完毕，正在退出线程')
            self.finished.emit()
        except StopIteration:
            self.finished.emit()
        except Exception as e:
            self.error.emit(f'{type(e).__name__}:\n{traceback.format_exc()}')

class LayoutNodeFloatWindow(QtWidgets.QWidget):
    """ 显示 Layout 节点信息 """
    
    move_to_node = Signal(UUID)
    delete_node = Signal(UUID)
    invoke_from_node = Signal(UUID)
    edit_node = Signal(UUID)

    def __init__(self):
        super().__init__()
        # 设置属性
        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        # 透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 显示时不抢焦点
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # 显示角色的标题
        self.role_label = QtWidgets.QLabel()
        self.role_label.setObjectName('LayoutNodeFloatWindowRole')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.role_label,
            qss_filename=QSSFiles.chat_window
        ))

        # 显示内容
        self.content_label = QtWidgets.QLabel()
        self.content_label.setObjectName('LayoutNodeFloatWindowContent')
        self.content_label.setWordWrap(True)
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.content_label,
            qss_filename=QSSFiles.chat_window
        ))
        # 设置宽度
        self.content_label.setFixedWidth(qss_formatter.config.chat_window.float_window_fixed_width)
        self.content_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Minimum
        )

        # 设置布局
        layout = QtWidgets.QVBoxLayout(self)
        # 给自绘阴影预留空间
        layout.setContentsMargins(20, 20, 20, 20)
        # 添加元素
        layout.addWidget(self.role_label)
        layout.addWidget(self.content_label)
        layout.addWidget(self._setup_function_area())

        # 设置状态量
        self.Clicked: bool = False

        # 设置信号
        self.function_moveto.pressed.connect(self.on_moveto_pressed)
        self.function_delete.pressed.connect(self.on_delete_pressed)
        self.function_restart.pressed.connect(self.on_restart_pressed)
        self.function_edit.pressed.connect(self.on_edit_pressed)

        # 初始化更新
        self.update()

    def update(self) -> None:
        # 获取屏幕并判断是否超出屏幕，如果超出屏幕就移动
        screen = QtWidgets.QApplication.screenAt(QCursor.pos()) 
        if screen:
            overflow = self.frameGeometry().bottom() - screen.availableGeometry().bottom()
            if overflow > 0:
                self.move(self.pos().x(), self.pos().y() - overflow)

        # 根据点击状态决定要不要显示按钮
        if self.Clicked:
            self.function_area.show()
        else:
            self.function_area.hide()
        
        # 根据节点类型判断按钮的状态（未实现的也设置成disabled了）
        self.function_edit.setEnabled(True)
        self.function_restart.setEnabled(True)
        self.function_moveto.setEnabled(True)
        self.function_delete.setEnabled(True)

        return super().update()

    def paintEvent(self, event):
        """ 绘制浮动窗口（自绘阴影 + 圆角背景）

        绘制分为两层（从外到内）：
          1. 阴影层：从 margin 最外层向内逐层绘制，alpha 递减
          2. 主背景层：圆角矩形，颜色 = 角色色，alpha 取决于是否被点击锁定
        """

        # ── 初始化 QPainter ────────────────────────────────────────
        # QPainter 是所有 Qt 自绘的入口，必须在 paintEvent 内构造
        painter = QPainter(self)
        # 开启抗锯齿，让圆角和阴影边缘平滑过渡
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ── 从全局 QSS 系统中读取配置 ──────────────────────────────
        # cfg: 非颜色配置（圆角半径、窗口尺寸等数字量）
        cfg = qss_formatter.config.chat_window
        # colors: 颜色配置（各角色的颜色值、透明度等）
        colors = qss_formatter.colors.chat_window
        # 圆角半径，例如 4px，控制浮窗四个角的弧度
        radius = cfg.float_window_radiu

        # ── 确定背景颜色与透明度 ────────────────────────────────────
        # 基础颜色取自 ROLE_COLOR_MAP，根据当前消息角色（user/assistant/tool/system）
        bg_color = QColor(colors.float_window_background_color)
        # bg_color = QColor(ROLE_COLOR_MAP[self.role])
        if not self.Clicked:
            # 未点击时：半透明，透明度从配置读取（如 128，即 50%）
            # 这样鼠标 hover 经过的浮窗不会完全遮挡下方内容
            bg_color.setAlpha(colors.float_window_background_alpha)
        else:
            # 点击锁定后：完全不透明（alpha=255）
            # 表示用户聚焦于该节点，浮窗应清晰可读
            bg_color.setAlpha(255)

        # ── 阴影外延宽度 ──────────────────────────────────────────
        # shadow_margin 决定阴影向外扩散多少像素
        # 这里的 6px 与 __init__ 中 layout.setContentsMargins(20,20,20,20)
        # 配合使用——margin 预留了阴影 + 额外的呼吸空间
        shadow_margin = 6

        # ── 确定内容区域矩形 ───────────────────────────────────────
        # self.rect() 是整个浮窗的完整区域（含 margin），
        # 用 adjusted(+m, +m, -m, -m) 从四边各向内收缩 shadow_margin，
        # 得到不含阴影的"内容矩形"作为主背景的范围
        rect = self.rect().adjusted(
            shadow_margin,    # 左边界右移
            shadow_margin,    # 上边界下移
            -shadow_margin,   # 右边界左移
            -shadow_margin    # 下边界上移
        )

        # ═══════════════════════════════════════════════════════════
        # 第一层：阴影（从外向内逐层绘制）
        # ═══════════════════════════════════════════════════════════
        # 原理：在内容矩形外围逐层画略大的圆角矩形，
        #       每层的 alpha 从高到低递减，模拟柔和扩散阴影。
        #
        # 例如 shadow_margin=6 时：
        #   i=0 → 紧贴内容矩形，alpha 最大（40）
        #   i=5 → 最外层，alpha 最小（≈7）
        #
        # 阴影颜色与角色色相同，保证浮窗和节点颜色一致。
        for i in range(shadow_margin):
            # ── 计算当前层的透明度 ─────────────────────────────────
            # alpha 从 40 线性递减到 ~7（最外层）
            #   i=0: alpha = 40 * (1 - 0/6) = 40
            #   i=5: alpha = 40 * (1 - 5/6) ≈ 7
            # 这种线性衰减让阴影从内到外自然淡出
            alpha = int(
                colors.float_window_shadow_start_alpha * (1 - i / shadow_margin)
            )

            # 阴影颜色 = 角色色 + 当前层透明度
            shadow_color = QColor(ROLE_COLOR_MAP[self.role])
            shadow_color.setAlpha(alpha)

            # 阴影层不需要描边，只需要填充
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(shadow_color)

            # ── 绘制当前阴影层的圆角矩形 ────────────────────────────
            # rect.adjusted(-i, -i, i, i) 将矩形向四边各扩展 i 像素，
            # 形成比上一层大一圈的阴影环。
            # 圆角半径也要同步增大 radius + i，
            # 否则外层矩形圆角不够大会露出直角边缘。
            # 外层矩形
            outer_rect = rect.adjusted(
                -i,
                -i,
                i,
                i
            )

            # 外层路径
            outer_path = QPainterPath()
            outer_path.addRoundedRect(
                QRectF(outer_rect),
                radius + i,
                radius + i
            )

            # 内层路径
            inner_path = QPainterPath()
            inner_path.addRoundedRect(
                QRectF(rect),
                radius,
                radius
            )

            # 环 = 外层 - 内层
            ring_path = outer_path.subtracted(inner_path)

            # 绘制环
            painter.fillPath(
                ring_path,
                shadow_color
            )
        # ═══════════════════════════════════════════════════════════
        # 第二层：主背景（圆角矩形，覆盖在阴影之上）
        # ═══════════════════════════════════════════════════════════
        # 在阴影全部画完之后，再画紧贴内容矩形的背景。
        # 这样主背景会自然地"盖在"阴影上面，
        # 从视觉上看就是"圆角矩形 + 向外扩散的柔和阴影"。
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)

        painter.drawRoundedRect(
            rect,          # 内容矩形，和阴影最内层（i=0）位置完全一致
            radius,        # 圆角半径，使用配置值
            radius
        )

    def set_node(self, node_uuid: UUID, node_message: IlinaMessage):
        """ 设置节点 """
        self.node_uuid = node_uuid  # 这个后面用在按钮出发事件时传递节点 UUID 确定点击的是哪个节点
        self.role_label.setText(node_message.role.title())
        self.role = node_message.role
        self.content_label.setText(
            node_message.content[:50].replace('\n', '')  
        + ('...' if len(node_message.content) > 50 else '')) 

        # 移动鼠标和重绘
        self.move(QCursor.pos())
        self.update()
    
    def _setup_function_area(self) -> QtWidgets.QWidget:

        # 编辑按钮
        self.function_edit = QtWidgets.QPushButton()
        self.function_edit.setText('编辑')
        self.function_edit.setObjectName('FloatWindowFunctionButton')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.function_edit,
            qss_filename=QSSFiles.chat_window
        ))

        # 重新生成按钮
        self.function_restart = QtWidgets.QPushButton()
        self.function_restart.setText('重新生成')
        self.function_restart.setObjectName('FloatWindowFunctionButton')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.function_restart,
            qss_filename=QSSFiles.chat_window
        ))

        # 切换到按钮
        self.function_moveto = QtWidgets.QPushButton()
        self.function_moveto.setText('切换到此')
        self.function_moveto.setObjectName('FloatWindowFunctionButton')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.function_moveto,
            qss_filename=QSSFiles.chat_window
        ))

        # 删除到按钮
        self.function_delete = QtWidgets.QPushButton()
        self.function_delete.setText('删除')
        self.function_delete.setObjectName('FloatWindowFunctionButton')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.function_delete,
            qss_filename=QSSFiles.chat_window
        ))

        # 功能区本身
        self.function_area = QtWidgets.QWidget()
        self.function_area.setObjectName('FloatWindowFunctionArea')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.function_area,
            qss_filename=QSSFiles.chat_window
        ))

        layout = QtWidgets.QVBoxLayout(self.function_area)
        layout.setSpacing(0)
        layout.addWidget(self.function_moveto)
        layout.addWidget(self.function_edit)
        layout.addWidget(self.function_restart)
        layout.addWidget(self.function_delete)

        return self.function_area

    @Slot()
    def on_moveto_pressed(self):
        self.move_to_node.emit(self.node_uuid)
    
    @Slot()
    def on_delete_pressed(self):
        self.delete_node.emit(self.node_uuid)
    
    @Slot()
    def on_restart_pressed(self):
        self.invoke_from_node.emit(self.node_uuid)
    
    @Slot()
    def on_edit_pressed(self):
        self.edit_node.emit(self.node_uuid)

class LayoutNode(QtWidgets.QGraphicsObject):
    hover_entered = Signal(UUID)
    hover_left = Signal(UUID)
    
    def __init__(self, node_role: str, node_uuid, layer: int, radiu: int, space: int):
        super().__init__()
        self.node_role = node_role
        self.node_uuid = node_uuid  # 用于发送事件
        self.layer: int|float = layer
        self.columnpos: int|None = None
        self.radiu = radiu
        self.space = space

        self.setZValue(1)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
    
        # 设置 hover 信号
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        self.hover_entered.emit(self.node_uuid)
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        self.hover_left.emit(self.node_uuid)
        return super().hoverLeaveEvent(event)

    def set_position(self):
        assert self.columnpos is not None
        self.setPos(
            self.columnpos*(2*self.radiu+self.space),
            self.layer*(2*self.radiu+self.space),
        )

    def boundingRect(self) -> QRectF:
        return QRectF(
            -self.radiu-(self.space//2),
            -self.radiu-(self.space//2),
            2*self.radiu+self.space,
            2*self.radiu+self.space,
        )
    
    def paint(self, painter: QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget=None) -> None:
        color = QColor(ROLE_COLOR_MAP[self.node_role])
        painter.setBrush(QColor(color))
        if self.columnpos == 0:
            painter.setPen(QPen(QColor(qss_formatter.colors.chat_window.role_line_color), 
                                qss_formatter.config.chat_window.tree_node_line_width))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(-self.radiu, -self.radiu, self.radiu*2, self.radiu*2)

        if option.state & QtWidgets.QStyle.StateFlag.State_MouseOver:
            painter.setBrush(QBrush())
            painter.setPen(QPen(QColor(qss_formatter.colors.chat_window.role_line_color), 1))
            circ_r = 5
            painter.drawEllipse(-self.radiu - circ_r, -self.radiu - circ_r, self.radiu*2 + circ_r*2, self.radiu*2 + circ_r*2)

class ConversionItem(QtWidgets.QWidget):
    """ 对话气泡？ """
    edit_finished = Signal(UUID, IlinaMessage, bool)  # 编辑完成的信号
    invoke_from_node = Signal(UUID)
    edit_node = Signal(UUID)

    def __init__(self, node_uuid: UUID, message: IlinaMessage):
        super().__init__()
        self.node_uuid = node_uuid
        self.node_message = message
        self.Editing: bool = False

        self.setObjectName('ConversionItem')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self,
            qss_filename=QSSFiles.chat_window
        ))

        # 显示角色的部分
        self.roleLabel = QtWidgets.QLabel(text=message.role.title())
        self.roleLabel.setObjectName('ConversionItemRoleLabel')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.roleLabel,
            qss_filename=QSSFiles.chat_window
        ))
        self.roleLabel.setProperty('role', message.role)
        self.roleLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            self.roleLabel.sizePolicy().verticalPolicy(),
        )
        self.roleLabel.setFixedWidth(96)
        self.roleLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # 显示思考的部分，在 role != assistant 或 reasoning_content 为空的时候隐藏
        self.reasoningContentBlock = MarkdownBrowser()
        self.reasoningContentBlock.setObjectName('ConversionItemReasoningContentBlock')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.reasoningContentBlock,
            qss_filename=QSSFiles.chat_window
        ))
        self.reasoningContentBlock.setSizePolicy(
            self.reasoningContentBlock.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Maximum
        )
        self.reasoningContentBlock.setMarkdown(message.reasoning_content)

        # 显示内容的部分
        self.contentBlock = MarkdownBrowser()
        self.contentBlock.setProperty('role', message.role)
        self.contentBlock.setObjectName('ConversionItemContentBlock')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.contentBlock,
            qss_filename=QSSFiles.chat_window
        ))
        self.contentBlock.setSizePolicy(
            self.contentBlock.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Maximum
        )
        # 关联内容按钮的消息实现快捷键
        self.contentBlock.hotkey_save.connect(lambda: self.edit_ok_pressed(False))
        self.contentBlock.hotkey_save_invoke.connect(lambda: self.edit_ok_pressed(True))
        self.contentBlock.hotkey_cancel.connect(self.edit_cancel_pressed)

        # 编辑的确认并生成按钮
        self.edit_ok_invoke_button = QtWidgets.QPushButton()
        self.edit_ok_invoke_button.setObjectName('ConversionItemButton')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.edit_ok_invoke_button,
            qss_filename=QSSFiles.chat_window
        ))
        self.edit_ok_invoke_button.setText('保存并生成')
        self.edit_ok_invoke_button.pressed.connect(lambda: self.edit_ok_pressed(True))

        # 编辑的确认按钮
        self.edit_ok_button = QtWidgets.QPushButton()
        self.edit_ok_button.setObjectName('ConversionItemButton')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.edit_ok_button,
            qss_filename=QSSFiles.chat_window
        ))
        self.edit_ok_button.setText('保存')
        self.edit_ok_button.pressed.connect(lambda: self.edit_ok_pressed(False))

        # 编辑的取消按钮
        self.edit_cancel_button = QtWidgets.QPushButton()
        self.edit_cancel_button.setObjectName('ConversionItemButton')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.edit_cancel_button,
            qss_filename=QSSFiles.chat_window
        ))
        self.edit_cancel_button.setText('放弃')
        self.edit_cancel_button.pressed.connect(self.edit_cancel_pressed)

        # 编辑按钮区
        self.edit_button_area = QtWidgets.QWidget()
        self.edit_button_area.setObjectName('ConversionItemButtonArea')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.edit_button_area,
            qss_filename=QSSFiles.chat_window
        ))
        # 编辑按钮区布局
        edit_button_layout = QtWidgets.QHBoxLayout(self.edit_button_area)
        edit_button_layout.setSpacing(0)
        edit_button_layout.setContentsMargins(0, 0, 0, 0)
        edit_button_layout.addWidget(self.edit_ok_invoke_button)
        edit_button_layout.addWidget(self.edit_ok_button)
        edit_button_layout.addWidget(self.edit_cancel_button)
        edit_button_layout.addStretch()

        # 浮动区的“重新生成”按钮
        self.float_restart_button = QtWidgets.QPushButton()
        self.float_restart_button.setObjectName('ConversionItemButton')
        self.float_restart_button.setText(f'重新生成')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.float_restart_button,
            qss_filename=QSSFiles.chat_window
        ))
        self.float_restart_button.pressed.connect(self.on_restart_pressed)

        # 浮动区的复制按钮
        self.float_copy_button = QtWidgets.QPushButton()
        self.float_copy_button.setObjectName('ConversionItemButton')
        self.float_copy_button.setText(f' 复制 ')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.float_copy_button,
            qss_filename=QSSFiles.chat_window
        ))
        self.float_copy_button.pressed.connect(self.on_copy_pressed)

        # 浮动按钮区
        self.float_button_area = QtWidgets.QWidget()
        self.float_button_area.setObjectName('ConversionItemButtonArea')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.float_button_area,
            qss_filename=QSSFiles.chat_window
        ))
        float_button_layout = QtWidgets.QHBoxLayout(self.float_button_area)
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
        self.float_buttons: list[QtWidgets.QPushButton] = [
            self.float_copy_button,
            self.float_restart_button,
        ]
        for button in self.float_buttons:
            button.hide()

        # 包括在思考和内容外面的框
        self.contentArea = QtWidgets.QWidget()
        self.contentArea.setObjectName('ConversionItemContentArea')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.contentArea,
            qss_filename=QSSFiles.chat_window
        ))
        self.contentArea.setSizePolicy(
            self.contentArea.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Maximum
        )

        # 思考外面的框的布局
        area_layout = QtWidgets.QVBoxLayout(self.contentArea)
        area_layout.setSpacing(0)
        area_layout.setContentsMargins(0, 0, 0, 0)
        area_layout.addWidget(self.reasoningContentBlock)
        area_layout.addWidget(self.contentBlock)
        area_layout.addWidget(self.edit_button_area)
        area_layout.addWidget(self.float_button_area)

        # 布局
        root_layout = QtWidgets.QHBoxLayout(self)
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
            self.contentBlock.setMarkdown('**'+ message.tool_name +'**\n\n'+message.content[:50]+('...' if len(message.content) > 50 else ''))
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

class ChatWindow(WindowBase):
    def __init__(self, filepath: str):
        super().__init__()

        self.engine = Engine(filepath)

        # 保存节点和消息气泡的对应、以及最新添加的气泡、尚在调用中的工作气泡
        self.uuid_to_conversion_item: dict[UUID, ConversionItem] = {}
        self.Adding_node: bool = False

        # 设置标题
        self.title_label = TitleLabel()
        self.title_label.label = self.engine.name
        self.title_label.label_edited.connect(lambda name: self.engine.set_name(name))
        self.titlebar_layout.insertWidget(0, self.title_label)

        self.setWindowTitle(f'Foves CLI v0.7.4 - {filepath}')
        # 添加状态文字
        self.titlebar_layout.insertWidget(1, self._setup_state_label())
        # 添加标题栏按钮
        self.titlebar_layout.insertWidget(3, self._setup_change_width_button())
        self.titlebar_layout.insertWidget(3, self._setup_hide_tree_button())
        # 添加内容组件
        self.root_layout.addWidget(self._setup_splitter_area())
        # 初始化浮动窗口
        self.layout_node_float_window = LayoutNodeFloatWindow()
        self.layout_node_float_window.hide()

        # 关联信号
        self.layout_node_float_window.move_to_node.connect(self.move_to_node)
        self.layout_node_float_window.delete_node.connect(self.delete_node)
        self.layout_node_float_window.invoke_from_node.connect(self.invoke_from_node)
        self.layout_node_float_window.edit_node.connect(self.start_edit_node)
        self.state_label.pressed.connect(self.reload_style)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.layout_node_float_window.Clicked = False
                self.layout_node_float_window.hide()
        return super().changeEvent(event)

    def _setup_state_label(self) -> QtWidgets.QPushButton:  # 隐藏小功能：点击这个状态可以重载 QSS
        self.state_label = QtWidgets.QPushButton()
        self.set_state_label_text_and_prop(StateLabelText.IDLE)
        self.state_label.setObjectName('StateLabel')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.state_label,
            qss_filename=QSSFiles.chat_window
        ))
        return self.state_label

    def set_state_label_text_and_prop(self, new_state: StateLabelText):
        self.state_label.setText(new_state)
        self.state_label.setProperty('state', new_state)
        # 通知样式引擎「这个 widget 的属性变了，重新匹配选择器」
        self.state_label.style().unpolish(self.state_label)
        self.state_label.style().polish(self.state_label)

    def start_invoke(self, start_from: UUID|None=None):
        """ 开始通过 worker 接受消息 """
        # 设置状态标题为连接中
        self.set_state_label_text_and_prop(StateLabelText.CONNECTING)
        # 设置按钮文字
        self.input_send_button.setText('■')
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

    def redraw_tree(self):
        self.log.info(f'开始重绘树')
        self.tree_scene.clear()
        # 建立树节点到绘图节点的映射表，并设置层坐标
        table: dict[Node, LayoutNode] = {}
        def update_table(node: Node, deepth: int):
            if node not in table:
                table[node] = LayoutNode(node.message.role, node.uuid, deepth, 
                                         qss_formatter.config.chat_window.tree_node_radiu,
                                         qss_formatter.config.chat_window.tree_node_space,
                                         )
                table[node].hover_entered.connect(self.on_layout_node_enter)
                table[node].hover_left.connect(self.on_layout_node_left)
                for child in node.children:
                    update_table(child, deepth+1)
        update_table(self.engine.readonly_root_node, 0)

        # 获取所有叶子节点，并为其指定纵坐标
        leaves = self.engine.readonly_leaves
        for i, leaf in enumerate(leaves):
            table[leaf].columnpos = i 
        
        # 为所有未分配纵坐标的叶子节点指定纵坐标
        def get_column(node: Node) -> int:
            column = table[node].columnpos
            if table[node].columnpos is None:  # 没有指定纵坐标
                # 获取所有子节点的纵坐标
                for child in node.children:
                    get_column(child)
                child = node._get_pointed_child()
                if child is not None:  # 子节点没有指定纵坐标
                    column = get_column(child)  # 向下寻找
                    table[node].columnpos = column
                else:
                    raise RuntimeError(f'节点 {node.uuid} 没有 column，且没有可追踪的 pointed child')
            assert column is not None
            return column
        root_column = get_column(self.engine.readonly_root_node)

        # 把所有节点的纵坐标都减去根节点的纵坐标，这样可以居中，并结合设置的行列确定最终的坐标
        max_layer = -1
        for node in table:
            max_layer = max(max_layer, table[node].layer)
            table[node].columnpos -= root_column # pyright: ignore[reportOperatorIssue]
        # 同时也调节一下layer坐标，同样是为了居中
        max_layer = max_layer / 2 + 0.5
        for node in table:
            table[node].layer -= max_layer
            table[node].set_position()
            self.tree_scene.addItem(table[node])
        
        # 递归画线
        def line_to_children(node: Node):
            for child in node.children:
                line = QtWidgets.QGraphicsLineItem(table[node].x(), table[node].y(), table[child].x(), table[child].y())
                line.setPen(QPen(
                    QColor(qss_formatter.colors.chat_window.role_line_color),
                    qss_formatter.config.chat_window.tree_node_line_width)
                )
                line.setZValue(0)
                self.tree_scene.addItem(line)
                line_to_children(child)
        line_to_children(self.engine.readonly_root_node)

        # 固定场景矩形，确保原点 (0,0) 处于视图中心
        rect = self.tree_scene.itemsBoundingRect()
        half_w = max(abs(rect.left()), abs(rect.right())) + 50
        half_h = max(abs(rect.top()), abs(rect.bottom())) + 50
        self.tree_scene.setSceneRect(
            QRectF(-half_w, -half_h, half_w * 2, half_h * 2)
        )
        self.tree_view.centerOn(0, 0)

        # 绑定信号
        self.tree_scene.selectionChanged.connect(self.on_layout_node_selected)
        self.log.info(f'重绘树完成')
    
    def scroll_to_node(self, node_uuid: UUID):
        try:
            item = self.uuid_to_conversion_item[node_uuid]
            self.scroll_area.ensureWidgetVisible(item)
        except KeyError:
            pass
            
        return  # 关于下面费劲写了几个版本不如上面那个更好用这件事……
        if self.Adding_node:
            QTimer.singleShot(0, lambda: self.scroll_to_node(node_uuid)) 
        else:    
            if node_uuid in self.uuid_to_conversion_item:
                try:
                    current = self.scroll_area.verticalScrollBar().value()
                    target = self.uuid_to_conversion_item[node_uuid].geometry().top()
                    if current != target:
                        if current != self.scroll_area.verticalScrollBar().maximum(): # 最大，添加空白
                            self.scroll_area.verticalScrollBar().setValue(target) 
                            QTimer.singleShot(0, lambda: self.scroll_to_node(node_uuid)) 
                except KeyError:
                    QTimer.singleShot(0, lambda: self.scroll_to_node(node_uuid)) 

    def reload_style(self):
        try:
            self.redraw_tree()
        except AttributeError as e:
            self.log.warning(f'重新加载样式时出现出错误：{type(e)}:{e}')
        return super().reload_style()

    def reload_icon(self):
        super().reload_icon()
        # 切换缩放按钮
        config = ConfigLoader(CONFIG_PATH, WindowConfig).readonly()
        if config.chat_width_state:
            self.width_button.setIcon(QIcon(QPixmap.fromImage(self.icons.copy(64, 64, 64, 64))))
        else:
            self.width_button.setIcon(QIcon(QPixmap.fromImage(self.icons.copy(128, 64, 64, 64))))
        
        if config.chat_hide_tree:
            self.tree_button.setIcon(QIcon(QPixmap.fromImage(self.icons.copy(0, 0, 64, 64))))
        else:
            self.tree_button.setIcon(QIcon(QPixmap.fromImage(self.icons.copy(128, 0, 64, 64))))

    def add_conversion_item(self, node_uuid: UUID, node_message: IlinaMessage) -> None:
        item = ConversionItem(node_uuid, node_message)
        self.uuid_to_conversion_item[node_uuid] = item
        self.scroll_layout.addWidget(item)
        item.edit_finished.connect(self.finished_edit_node)
        item.invoke_from_node.connect(self.invoke_from_node)
        item.edit_node.connect(self.start_edit_node)

    def reset_conversion_item(self, max_target: UUID|None=None, including: bool=True) -> None:
        """ 清空对话并重新添加，如果指定了 max_target，会在那里停下，如果including为True，就会添加完再停 """
        self.log.info(f'重新添加节点，到 {max_target} 停止，{including=}')
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)          # ① 从布局中取出（不放任其悬空）
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()  
        # 为对话区域里的每个对话创建一个气泡，并添加到布局中
        self.uuid_to_conversion_item = {}
        self.Adding_node = True
        # with self.tree as root:
        for node_uuid, node_message in zip(*self.engine.message_list):
            if max_target and node_uuid == max_target:
                if including:
                    self.add_conversion_item(node_uuid, node_message)
                self.Adding_node = False
                return
            self.add_conversion_item(node_uuid, node_message)
        self.Adding_node = False

    def change_tree(self, toogle: bool=False) -> None:
        """ 切换树视图的显示状态 """
        with ConfigLoader(CONFIG_PATH, WindowConfig) as conf:
            if toogle:
                conf.chat_hide_tree = not conf.chat_hide_tree

            if conf.chat_hide_tree:
                self.tree_area.show()
            else:
                self.tree_area.hide()

    def change_width(self, toggle: bool=False) -> None:
        """ 刷新文本区的宽度，可以同时设置 """
        # 设置文本的宽度
        with ConfigLoader(CONFIG_PATH, WindowConfig) as config:
            if toggle:
                config.chat_width_state = not config.chat_width_state

            if config.chat_width_state:
                self.scroll_area.setMaximumWidth(self.maximumWidth())
                self.input_area.setMaximumWidth(self.maximumWidth())
            else:
                self.scroll_area.setMaximumWidth(qss_formatter.config.chat_window.conversion_area_width)
                self.input_area.setMaximumWidth(qss_formatter.config.chat_window.conversion_area_width)
    
    def _setup_tree_area(self) -> QtWidgets.QWidget:

        # 场景和视角
        self.tree_scene = QtWidgets.QGraphicsScene()
        self.tree_view = QtWidgets.QGraphicsView(self.tree_scene)
        self.tree_view.setObjectName('TreeView')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.tree_view,
            qss_filename=QSSFiles.chat_window
        ))
        self.tree_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree_view.setResizeAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter
        )
        self.redraw_tree()
        # 区域
        self.tree_area = QtWidgets.QWidget()
        self.tree_area.setObjectName('TreeArea')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.tree_area,
            qss_filename=QSSFiles.chat_window
        ))
        area_layout = QtWidgets.QVBoxLayout(self.tree_area)
        area_layout.addWidget(self.tree_view)

        # 确认开关状态
        self.change_tree()

        return self.tree_area

    def _setup_splitter_area(self) -> QtWidgets.QWidget:
        self.splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName('Splitter')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.splitter,
            qss_filename=QSSFiles.chat_window
        ))
        self.splitter.addWidget(self._setup_tree_area())
        self.splitter.addWidget(self._setup_talk_area())

        # 从设置里导入 spliter 的分配信息
        config = ConfigLoader(CONFIG_PATH, WindowConfig).readonly()
        if config.chat_splitter_state == '':
            self.splitter.setSizes([300, 400])
        else:
            self.splitter.restoreState(QByteArray.fromBase64(config.chat_splitter_state.encode()))
        self.splitter.splitterMoved.connect(self.on_splitter_moved)

        return self.splitter

    def _setup_input_area(self) -> QtWidgets.QWidget:
        # ----------- 发送按钮 ------------------------------------------------------------------
        self.input_send_button = QtWidgets.QPushButton('↑')
        self.input_send_button.setObjectName('InputSendButton')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.input_send_button,
            qss_filename=QSSFiles.chat_window
        ))
        self.input_send_button.pressed.connect(self.on_send_pressed)

        # ----------- 文本输入框 ------------------------------------------------------------------
        self.input_textedit = QtWidgets.QTextEdit(placeholderText='在这里和 AI 聊天...')  # 文本输入部分
        self.input_textedit.setObjectName('InputTextedit')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.input_textedit,
            qss_filename=QSSFiles.chat_window
        ))
        self.input_textedit.setSizePolicy(
            self.input_textedit.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Minimum
        )
        def input_textedit_ondocuentSizeChanged(size):  # 用来约束文本框使得高度随内容自适应
            if size.height() < qss_formatter.config.chat_window.max_input_area_height:
                self.input_textedit.setFixedHeight(size.height())
            else:
                self.input_textedit.setFixedHeight(qss_formatter.config.chat_window.max_input_area_height)
        self.input_textedit.document().documentLayout().documentSizeChanged.connect(
            input_textedit_ondocuentSizeChanged
        )

        # ----------- 文本输入区域 ------------------------------------------------------------------
        self.input_area = QtWidgets.QWidget()  # 文本输入的整体框架
        self.input_area.setObjectName('InputArea')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.input_area,
            qss_filename=QSSFiles.chat_window
        ))
        self.input_area.setSizePolicy(
            self.input_area.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Minimum
        )
        area_layout = QtWidgets.QGridLayout(self.input_area)
        area_layout.addWidget(self.input_textedit, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        area_layout.addWidget(self.input_send_button, 0, 1, alignment=Qt.AlignmentFlag.AlignBottom)

        # 点击 input_area 空白处时，激活文本输入框
        self.input_area.installEventFilter(self)

        # 拦截回车：Enter 发送，Shift+Enter 换行
        self.input_textedit.installEventFilter(self)

        # ----------- 外层用来定位的容器 ------------------------------------------------------------------
        self.input_outside = QtWidgets.QWidget()
        self.input_outside.setObjectName('InputOutside')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.input_outside,
            qss_filename=QSSFiles.chat_window
        ))
        self.input_outside.setSizePolicy(
            self.input_outside.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.input_outside.setMinimumHeight(qss_formatter.config.chat_window.min_input_area_height)
        self.input_outside.setMaximumHeight(qss_formatter.config.chat_window.max_input_area_height)

        outside_layout = QtWidgets.QHBoxLayout(self.input_outside)
        outside_layout.addSpacing(0)
        outside_layout.addWidget(self.input_area)
        outside_layout.addSpacing(0)

        return self.input_outside

    def _setup_scroll_area(self) -> QtWidgets.QWidget:
        # 文本的滚动区域
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setObjectName('ScrollArea')
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.scroll_area,
            qss_filename=QSSFiles.chat_window
        ))

        self.scroll_area.setWidgetResizable(True)  # 内容 widget 随滚动区域自适应宽度
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 滚动区域内部的内容容器
        content = QtWidgets.QWidget()
        content.setObjectName('ScrollContent')
        qss_formatter.add_qss_info(QSSInfo(
            widget=content,
            qss_filename=QSSFiles.chat_window
        ))
        self.scroll_layout = QtWidgets.QVBoxLayout(content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # 顶部对齐，不拉伸

        # 为对话区域里的每个对话创建一个气泡，并添加到布局中
        self.reset_conversion_item()

        self.scroll_layout.addStretch(1)  # 底部留白，内容不足时不会散开
        self.scroll_area.setWidget(content)


        # 外层用来定位的容器
        self._scroll_outside = QtWidgets.QWidget()
        self._scroll_outside.setObjectName('ScrollOutside')
        outside_layout = QtWidgets.QHBoxLayout(self._scroll_outside)
        
        outside_layout.addSpacing(0)
        outside_layout.addWidget(self.scroll_area)
        outside_layout.addSpacing(0)

        # 让 outside 空白区域的滚轮事件转发给 scroll_area
        self._scroll_outside.installEventFilter(self)

        qss_formatter.add_qss_info(QSSInfo(
            widget=self._scroll_outside,
            qss_filename=QSSFiles.chat_window
        ))

        self.scroll_to_node(self.engine.readonly_now_node)

        return self._scroll_outside

    def _setup_talk_area(self) -> QtWidgets.QWidget:
        """ 建立对话区域 """
        # 上面是滚动区域，下面是输入区域
        talk_area = QtWidgets.QWidget()
        talk_area.setObjectName('TalkArea')
        qss_formatter.add_qss_info(QSSInfo(
            widget=talk_area,
            qss_filename=[QSSFiles.window_base, QSSFiles.chat_window]
        ))

        layout = QtWidgets.QVBoxLayout(talk_area)
        layout.addWidget(self._setup_scroll_area())
        layout.addWidget(self._setup_input_area())
        self.change_width()

        return talk_area

    def eventFilter(self, obj, event):
        """将 outside 空白区域的滚轮事件转发给 scroll_area.viewport()"""
        if obj is getattr(self, '_scroll_outside', None):
            if event.type() == QEvent.Type.Wheel:
                QtWidgets.QApplication.sendEvent(self.scroll_area.viewport(), event)
                return True
        # 点击 input_area 空白区域时，激活文本输入框
        if obj is getattr(self, 'input_area', None):
            if event.type() == QEvent.Type.MouseButtonPress:
                self.input_textedit.setFocus()
                return True
        # 输入框：Enter 发送，Shift+Enter 换行
        if obj is getattr(self, 'input_textedit', None):
            if event.type() == QEvent.Type.KeyPress:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                        self.on_send_pressed()
                        return True
        return super().eventFilter(obj, event)

    def _setup_change_width_button(self) -> QtWidgets.QPushButton:
        self.width_button = QtWidgets.QPushButton()
        self.width_button.setObjectName('TitleBarButton')
        self.width_button.setSizePolicy(
            self.width_button.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.width_button,
            qss_filename=QSSFiles.window_base
        ))
        self.width_button.pressed.connect(self.on_width)
        
        return self.width_button
    
    def _setup_hide_tree_button(self) -> QtWidgets.QPushButton:
        self.tree_button = QtWidgets.QPushButton()
        self.tree_button.setObjectName('TitleBarButton')
        self.tree_button.setSizePolicy(
            self.tree_button.sizePolicy().horizontalPolicy(),
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        qss_formatter.add_qss_info(QSSInfo(
            widget=self.tree_button,
            qss_filename=QSSFiles.window_base
        ))
        self.tree_button.pressed.connect(self.on_tree)
        
        return self.tree_button

    @Slot()
    def start_edit_node(self, target: UUID):
        if target not in self.uuid_to_conversion_item:
            self.move_to_node(target)
        self.scroll_to_node(target)
        self.uuid_to_conversion_item[target].start_edit()
        self.layout_node_float_window.hide()
        self.layout_node_float_window.Clicked = False

    @Slot()
    def finished_edit_node(self, target: UUID, new_message: IlinaMessage, invoke: bool):
        new_node_uuid = self.engine.edit_node(target, new_message)
        self.move_to_node(new_node_uuid)
        if invoke:
            self.start_invoke()

    @Slot()
    def on_invoke_worker_finished(self):
        # 切换状态栏
        self.set_state_label_text_and_prop(StateLabelText.IDLE)
        # 切换按钮
        self.input_send_button.setText('↑')
        self.redraw_tree()

    @Slot()
    def on_send_pressed(self):
        if self.state_label.text() == StateLabelText.IDLE:
            if not self.send_message():  # 如果其实未发送就直接返回，什么都不做
                return
            self.input_send_button.setText('■')
        else:
            self.invoke_worker.stop_flag = True

    @Slot()
    def on_engine_event(self, call_event: NodeEvent):
        self.set_state_label_text_and_prop(StateLabelText.TRANSPORTING)


        if call_event._type == NodeEventTypes.CREATED:
            self.add_conversion_item(call_event.node.uuid, call_event.node.message)
            self.redraw_tree()
            # self.scroll_to_node(call_event.node.uuid)
        elif call_event._type == NodeEventTypes.UPDATED:
            self.uuid_to_conversion_item[call_event.node.uuid].update_message(call_event.node.message)
            self.scroll_to_node(call_event.node.uuid)
        elif call_event._type == NodeEventTypes.ERROR:
            self.log.error(f'引擎产出了错误事件：\n{call_event.node.message.content}')
            return

    @Slot()
    def on_invoke_worker_error(self, error: str):
        self.set_state_label_text_and_prop(StateLabelText.IDLE)
        self.input_send_button.setText('↑')
        self.log.error(f'invoke_worker_error: {error}')

    @Slot()
    def on_width(self):
        self.change_width(True)
        self.reload_icon()
    
    @Slot()
    def on_tree(self):
        self.change_tree(True)
        self.reload_icon()

    @Slot()
    def on_splitter_moved(self):
        with ConfigLoader(CONFIG_PATH, WindowConfig) as conf:
            conf.chat_splitter_state = self.splitter.saveState().toBase64().data().decode()   # pyright: ignore[reportAttributeAccessIssue]

    @Slot()
    def on_layout_node_enter(self, node_uuid: UUID):
        if not self.layout_node_float_window.Clicked:
            self.layout_node_float_window.set_node(node_uuid, self.engine.get_message_by_uuid(node_uuid))
            self.layout_node_float_window.show()
    
    @Slot()
    def on_layout_node_left(self, node: LayoutNode):
        if not self.layout_node_float_window.Clicked:
            self.layout_node_float_window.hide()

    @Slot()
    def on_layout_node_selected(self):
        try:
            layout_node: LayoutNode = self.tree_scene.selectedItems()[0] # pyright: ignore[reportAssignmentType]
            self.layout_node_float_window.Clicked = True
            self.layout_node_float_window.set_node(layout_node.node_uuid, self.engine.get_message_by_uuid(layout_node.node_uuid))
            self.scroll_to_node(layout_node.node_uuid)
        except IndexError:
            pass
    
    @Slot()
    def move_to_node(self, target_uuid: UUID):
        self.engine.move_to_node(target_uuid)
        self.layout_node_float_window.Clicked = False
        self.layout_node_float_window.hide()
        self.redraw_tree()
        self.reset_conversion_item()
        QTimer.singleShot(10, lambda: self.scroll_to_node(target_uuid))

    @Slot()
    def send_message(self):
        """ 发送消息。但如果 content 为空就返回 False，表示其实未发送 """
        content = self.input_textedit.toPlainText()
        user_message = IlinaMessage(role='user', content=content)
        if content != '':
            new_node_uuid = self.engine.send(user_message)
            self.add_conversion_item(new_node_uuid, user_message)
            self.redraw_tree()
            QTimer.singleShot(10, lambda: self.scroll_to_node(new_node_uuid))
            self.input_textedit.clear()
            self.start_invoke()
            return True
        else:
            return False

    @Slot()
    def delete_node(self, target: UUID):
        self.engine.delete_node(target)
        self.layout_node_float_window.Clicked = False
        self.layout_node_float_window.hide()
        self.redraw_tree()
        if self.state_label.text() == StateLabelText.IDLE:
            self.reset_conversion_item()
    
    @Slot()
    def invoke_from_node(self, target: UUID):
        self.layout_node_float_window.Clicked = False
        self.layout_node_float_window.hide()

        self.redraw_tree()
        is_assistant = self.engine.get_message_by_uuid(target).role == 'assistant'
        if target in self.uuid_to_conversion_item:  # 如果在当前显示中，就删除后续的节点
            self.remove_conversion_items_after(target, is_assistant)
        else:
            self.move_to_node(target)
            self.reset_conversion_item(target, not is_assistant)
            QTimer.singleShot(10, lambda: self.scroll_to_node(target))
        self.start_invoke(target)

    def remove_conversion_items_after(self, target: UUID, include_target: bool=False):
        """ 删除对话列表中，目标 target 之后的所有节点， """
        uuids = list(self.uuid_to_conversion_item.keys())
        end_index = uuids.index(target) + (0 if include_target else 1)
        self.log.info(f'删除 {target} 之后的节点，{end_index=}')
        for delete_node in uuids[end_index:]:
            # item = self.scroll_layout.takeAt(self.scroll_layout)          # ① 从布局中取出（不放任其悬空）
            # if item is not None:
            #     widget = item.widget()
            #     if widget is not None:
                    # widget.deleteLater()
            self.uuid_to_conversion_item[delete_node].deleteLater()


    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.layout_node_float_window != self.childAt(event.pos()):
            self.layout_node_float_window.Clicked = False
            self.layout_node_float_window.hide()
        super().mousePressEvent(event)
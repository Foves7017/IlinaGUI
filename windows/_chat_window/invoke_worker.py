import logging
import traceback

from uuid import UUID
from IlinaEngine import Engine
from PySide6.QtCore import Signal, QObject, Slot

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
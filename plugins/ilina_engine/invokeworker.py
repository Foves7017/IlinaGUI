import logging
import traceback

from uuid import UUID
from IlinaEngine import Engine, IlinaMessage
from PySide6.QtCore import Signal, QObject, Slot

class InvokeWorker(QObject):
    event_received = Signal(IlinaMessage)
    finished = Signal()


    def __init__(self, engine: Engine):
        super().__init__()
        self.engine = engine
        self.log = logging.getLogger('InvokeWorker')
        self.stop_flag: bool = False

    @Slot()
    def run(self):
        try:
            self.log.info(f'开始 _invoke 并接受事件')
            for event in self.engine._invoke():
                self.log.debug(f'next event: {event}')
                self.event_received.emit(event)
                if self.stop_flag:
                    raise StopIteration

            self.log.info(f'事件接受完毕，正在退出线程')
            self.finished.emit()
        except StopIteration:
            self.log.info(f'事件接受完毕，正在退出线程')
            self.finished.emit()
        except Exception as e:
            self.log.error(f'{type(e).__name__}:\n{traceback.format_exc()}')
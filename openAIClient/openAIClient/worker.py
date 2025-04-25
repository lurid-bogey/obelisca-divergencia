import logging
from PySide6.QtCore import QObject, Signal, QRunnable, Slot

from openAIClient.chatSession import ChatSession


class WorkerSignals(QObject):
    finished = Signal(str)
    error = Signal(str)


class WorkerRunnable(QRunnable):
    """
    Worker Runnable for executing the API call in a background thread.
    """
    def __init__(self, chatSession: ChatSession, userText: str, filePathList: list):
        super().__init__()
        self.chatSession = chatSession
        self.userText = userText
        self.filePathList = filePathList
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        """
        Executes the sendMessage operation in a separate thread.
        """
        try:
            reply = self.chatSession.sendMessage(self.userText, self.filePathList)
            self.signals.finished.emit(reply)
        except Exception as e:
            logging.error("Error in worker: %s", e, exc_info=True)
            self.signals.error.emit(str(e))

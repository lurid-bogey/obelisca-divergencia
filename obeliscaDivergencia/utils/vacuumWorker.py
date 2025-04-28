import logging
import sqlite3

from PySide6.QtCore import (QObject, Signal, QRunnable, Slot)

from obeliscaDivergencia.config import getDatabasePath


class VacuumWorkerSignals(QObject):
    """ Defines the signals available from a VacuumWorker.
    Supported signals are:

    finished
        No data

    error
        `str` containing error message
    """
    finished = Signal()
    error = Signal(str)


class VacuumWorker(QRunnable):
    """ Worker thread for vacuuming the SQLite database. """
    def __init__(self, dbPath: str):
        super().__init__()
        self.dbPath = dbPath
        self.signals = VacuumWorkerSignals()

    @Slot()
    def run(self):
        """
        Executes the VACUUM command on the SQLite database.
        """
        try:
            logging.info("Starting database vacuum...")
            connection = sqlite3.connect(self.dbPath)
            cursor = connection.cursor()
            cursor.execute("VACUUM;")
            connection.commit()
            connection.close()
            logging.info("Database vacuum completed successfully.")
            self.signals.finished.emit()
        except Exception as e:
            logging.error(f"Database vacuum failed: {e}")
            self.signals.error.emit(str(e))

import logging
import os
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDropEvent, QDragEnterEvent

from obeliscaDivergencia.gui.customListItem import CustomListItem
from obeliscaDivergencia.utils.fileUtils import normalizeFilePath, isBinaryFile


class DroppableListWidget(QListWidget):
    """
    A QListWidget subclass that accepts drag-and-drop for files and directories.
    Emits a signal with the list of file paths when files/folders are dropped.
    """

    def __init__(self, parent, binaryExtensions, folderBalcklist):
        super().__init__(parent)
        self.parent = parent
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.binaryExtensions = binaryExtensions
        self.folderBalcklist = folderBalcklist

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            filePaths = [url.toLocalFile() for url in urls]
            attachedFiles = []
            for path in filePaths:
                if os.path.isfile(path):
                    normalizedPath = normalizeFilePath(path)
                    attachedFiles.append(normalizedPath)
                elif os.path.isdir(path):
                    # Recursively add files from the directory
                    for root, dirs, files in os.walk(path):
                        # Filter out blacklisted directories.
                        dirs[:] = [dirName for dirName in dirs if dirName not in self.folderBalcklist]
                        for file in files:
                            fullPath = os.path.join(root, file)
                            normalizedPath = normalizeFilePath(fullPath)
                            attachedFiles.append(normalizedPath)
            if attachedFiles:
                self.parent.attachFiles(attachedFiles)
            event.acceptProposedAction()
        else:
            event.ignore()

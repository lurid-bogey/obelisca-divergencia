import logging

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize, Signal  # Import Signal

from obeliscaDivergencia.config import resourcePath


class CustomListItem(QWidget):
    # Define a signal that emits the file path to be removed
    removeClicked = Signal(str)

    def __init__(self, text):
        super().__init__()

        # Initialize labels for icons and text.
        self.leftIconLabel = QLabel()
        self.textLabel = QLabel(text)
        # Replace the clickable label with a push button.
        self.rightIconButton = QPushButton()
        # Set a flat style so it looks more like an icon.
        self.rightIconButton.setFlat(True)

        # Set the pixmaps/icons for the icons.
        self.leftIconLabel.setPixmap(QPixmap(resourcePath("assets/new-file.png", forcedPath=True)).scaled(16, 16))
        # Instead of setting the pixmap on a label, set an icon on the push button.
        self.rightIconButton.setIcon(QIcon(resourcePath("assets/delete-red.png", forcedPath=True)))
        self.rightIconButton.setIconSize(QSize(8, 8))

        # Set up the horizontal layout.
        layout = QHBoxLayout()
        layout.addWidget(self.leftIconLabel)
        layout.addWidget(self.textLabel)
        layout.addWidget(self.rightIconButton)

        # Adjust layout spacing and margins.
        layout.setSpacing(10)
        layout.setContentsMargins(5, 0, 5, 0)

        self.setLayout(layout)
        # Connect the click signal of the push button to perform the specific action.
        self.rightIconButton.clicked.connect(self.onRightIconClicked)

    # This function is triggered when the right button is clicked.
    def onRightIconClicked(self):
        # Emit the signal with the file path
        filePath = getattr(self.rightIconButton, "customData", None)
        if filePath:
            self.removeClicked.emit(filePath)
        else:
            logging.info("No file path associated with this item.")

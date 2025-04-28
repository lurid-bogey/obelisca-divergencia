from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt, Signal


class SendableTextEdit(QTextEdit):
    # Custom signal to indicate that the user wants to send the message.
    sendMessage = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Enforce that only plain text is accepted.
        self.setAcceptRichText(False)
        # Ensure that long lines are wrapped to fit within the widget.
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

    def keyPressEvent(self, event):
        # Check if Ctrl+Enter (or Ctrl+Return) is pressed.
        # Note: Qt.Key_Enter may include the KeypadModifier.
        key = event.key()
        mod = event.modifiers()

        accepted = False

        # Check for Ctrl+Return (regular Return key with Control)
        if key == Qt.Key.Key_Return and mod == Qt.KeyboardModifier.ControlModifier:
            accepted = True
        # Check for Ctrl+Enter (enter key from the keypad, which comes with an extra modifier)
        elif key == Qt.Key.Key_Enter and mod == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.KeypadModifier):
            accepted = True

        if accepted:
            self.sendMessage.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

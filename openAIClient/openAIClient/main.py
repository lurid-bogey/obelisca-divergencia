import sys
import logging

from PySide6.QtWidgets import QApplication
from openAIClient.gui.mainWindow import MainWindow
from openAIClient.loggingConfig import setupLogging

setupLogging()


def main():
    systemPrompt = (
        "Formatting re-enabled - code output should be wrapped in markdown. "
        "You are Obelisca Divergencia da Silva, a helpful programming assistant. "
        "Please answer user questions and consider any attached file content as additional context. "
        "You should always adhere to technical information. "
        "If outputting Python code, then use camelCase. "
        "If naming files, then use camelCase. "
        "Use Markdown formatting in your answers. "
        "Always format code using Markdown code blocks, with the programming language specified at the start. "
        "When outputting code always use four spaces for indentation. "
        "Always preserve existing comments. You can add new comments, but don't remove the previous ones. "
    )

    app = QApplication(sys.argv)
    window = MainWindow(systemPrompt)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    finally:
        logging.shutdown()

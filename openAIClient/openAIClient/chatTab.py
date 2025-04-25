import os
import logging
import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QFileDialog, QMessageBox, QListWidgetItem, QApplication, QMainWindow
)
from PySide6.QtGui import QIcon, QTextCursor
from PySide6.QtCore import Signal, QThreadPool, QSettings

from openAIClient.worker import WorkerRunnable
from openAIClient.gui.Ui_conversationWidget import Ui_conversationForm
from openAIClient.gui.customTextEdit import SendableTextEdit
from openAIClient.gui.customListItem import CustomListItem
from openAIClient.utils.markdownUtils import convertMarkdownToHtml
from openAIClient.utils.fileUtils import normalizeFilePath, isBinaryFile
from openAIClient.chatSession import ChatSession
from openAIClient.config import resourcePath


class ChatTab(QWidget):
    """
    A dedicated ChatTab widget that encapsulates its own conversation UI,
    attached file list, and ChatSession.
    """
    # Define signals
    tokenUpdated = Signal(int, int)      # totalTokens, currentTokenCount
    titleUpdated = Signal(int, str)      # conversationId, newTitle

    def __init__(self, chatSession: ChatSession, conversationId: int, parent=None):
        super().__init__(parent)
        self.chatSession = chatSession
        self.conversationId = conversationId  # Store the conversation ID
        self.threadPool = QThreadPool.globalInstance()
        # Initialize attachedFiles from database instead of starting with an empty list.
        self.attachedFiles = []  # List to hold attached file paths
        self.loadAttachedFilesFromDatabase()  # Load from the database if any attachments exist

        # Load the conversation UI from the compiled UI file.
        self.ui = Ui_conversationForm()
        self.ui.setupUi(self)

        # Replace the default QTextEdit with a custom SendableTextEdit.
        self.customUserInput = SendableTextEdit()
        self.customUserInput.setPlaceholderText("Type your message here...")
        self.customUserInput.setFixedHeight(80)
        parentLayout = self.ui.userInput.parentWidget().layout()
        parentLayout.replaceWidget(self.ui.userInput, self.customUserInput)
        self.ui.userInput.deleteLater()
        self.ui.userInput = self.customUserInput

        self.ui.busyIndicator.setVisible(False)

        self.ui.attachDirectoryButton.setMinimumHeight(35)
        self.ui.attachButton.setMinimumHeight(35)
        self.ui.sendButton.setMinimumHeight(35)
        self.ui.attachDirectoryButton.setMinimumWidth(135)
        self.ui.attachButton.setMinimumWidth(135)
        self.ui.sendButton.setMinimumWidth(135)

        self.ui.attachedFilesList.setStyleSheet("background-color: #fafafa;")
        self.ui.sendButton.setStyleSheet("text-align: left; padding-left: 10px; background-color: #eef2ff;")
        self.ui.busyIndicator.setStyleSheet(
           "background-color: #eef2ff; color: blue; font-weight: bold;"
        )

        # Configure button icons and sizes.
        self.ui.attachButton.setIcon(QIcon(resourcePath("assets/file-add.png", forcedPath=True)))
        self.ui.attachDirectoryButton.setIcon(QIcon(resourcePath("assets/folder-add.png", forcedPath=True)))
        self.ui.sendButton.setIcon(QIcon(resourcePath("assets/upload-circle.png", forcedPath=True)))

        # Connect signals.
        self.ui.attachButton.clicked.connect(self.onAttachFiles)
        self.ui.attachDirectoryButton.clicked.connect(self.onAttachDirectory)
        self.ui.sendButton.clicked.connect(self.onSendClicked)
        self.ui.userInput.sendMessage.connect(self.onSendClicked)

        # If there's existing conversation history, load it into the display
        self.loadExistingConversation()
        # Update the UI list widget with any loaded attachments.
        self.updateAttachedFilesList()

    def loadAttachedFilesFromDatabase(self):
        """
        Loads attached files from the database for this conversation and initializes self.attachedFiles.
        """
        # Locate the parent that stores conversationDb (typically the MainWindow)
        parent = self.parentWidget()
        while parent and not hasattr(parent, 'conversationDb'):
            parent = parent.parentWidget()
        if parent and hasattr(parent, 'conversationDb'):
            try:
                # Execute a query joining the files table with the conversation_attachements
                query = """
                    SELECT f.file_path 
                    FROM files f 
                    INNER JOIN conversation_attachements ca ON f.id = ca.file_id 
                    WHERE ca.conversation_id = ?
                """
                cursor = parent.conversationDb.conn.execute(query, (self.conversationId,))
                rows = cursor.fetchall()
                # Save all the attached file paths into self.attachedFiles.
                self.attachedFiles = [row[0] for row in rows]
                logging.info("Loaded %d attached files for conversation ID %d",
                             len(self.attachedFiles), self.conversationId)
            except Exception as e:
                logging.error("Failed to load attached files for conversation %d: %s",
                              self.conversationId, e)

    def loadExistingConversation(self):
        """
        Loads the existing conversation history into the conversation display.
        """
        for message in self.chatSession.conversationHistory[1:]:
            role = message.get("role", "")
            content = message.get("content", "")
            if role == "user":
                self.appendToConversation("**You:** " + content)
            elif role == "assistant":
                self.appendToConversation("**Assistant:** " + content)
        self.ui.conversationDisplay.moveCursor(QTextCursor.MoveOperation.End)
        logging.info("Loaded existing conversation into ChatTab.")

    def onAttachFiles(self):
        """
        Opens a file dialog to select files. Filters out binary files and duplicates.
        Updates the database.
        """
        # Open file dialog to select multiple files, starting in the last used directory.
        filePaths, _ = QFileDialog.getOpenFileNames(self, "Select Files", self.getLastDirectory(), "All Files (*)")
        if not filePaths:
            return

        # Update last used directory
        self.setLastDirectory(os.path.dirname(filePaths[0]))

        newFiles = []
        # Normalize paths and skip binary files and duplicates.
        for filePath in filePaths:
            normalizedPath = normalizeFilePath(filePath)
            if isBinaryFile(normalizedPath, self.chatSession.BINARY_EXTENSIONS):
                logging.info("Skipping binary file: %s", normalizedPath)
                continue
            if normalizedPath in self.attachedFiles:
                logging.info("File already attached: %s", normalizedPath)
                continue
            newFiles.append(normalizedPath)

        if not newFiles:
            return

        # Append the new files and update the database.
        self.attachedFiles.extend(newFiles)

        # Read from the database the files which were already attached if needed.
        parent = self.parentWidget()
        while parent and not hasattr(parent, 'conversationDb'):
            parent = parent.parentWidget()
        if parent and hasattr(parent, 'conversationDb'):
            parent.conversationDb.recordAttachmentsForConversation(self.conversationId, newFiles)

        # Update the UI list widget.
        self.updateAttachedFilesList()

    def onAttachDirectory(self):
        """
        Opens a directory dialog to select a directory. Recursively attaches eligible files.
        Filters out binary files and duplicates. Updates the database.
        """
        # Open directory dialog starting in the last used directory.
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.getLastDirectory())
        if not directory:
            return

        # Update last used directory.
        self.setLastDirectory(directory)

        newFiles = []
        # Walk recursively through the directory.
        for root, dirs, files in os.walk(directory):
            # Skip blacklisted directories.
            dirs[:] = [dirName for dirName in dirs if dirName not in self.chatSession.FOLDER_BLACKLIST]
            for fileName in files:
                fullPath = os.path.join(root, fileName)
                normalizedPath = normalizeFilePath(fullPath)
                if isBinaryFile(normalizedPath, self.chatSession.BINARY_EXTENSIONS):
                    logging.info("Skipping binary file: %s", normalizedPath)
                    continue
                if normalizedPath in self.attachedFiles:
                    logging.info("File already attached: %s", normalizedPath)
                    continue
                newFiles.append(normalizedPath)

        if not newFiles:
            return

        # Append the new files and update the database.
        self.attachedFiles.extend(newFiles)

        parent = self.parentWidget()
        while parent and not hasattr(parent, 'conversationDb'):
            parent = parent.parentWidget()
        if parent and hasattr(parent, 'conversationDb'):
            parent.conversationDb.recordAttachmentsForConversation(self.conversationId, newFiles)

        # Update the UI list widget.
        self.updateAttachedFilesList()

    def updateAttachedFilesList(self):
        """
        Updates the attachedFilesList QListWidget to display current attachments with appropriate icons.
        """
        self.ui.attachedFilesList.clear()
        for path in self.attachedFiles:
            # custom list item with two icons
            displayText = str(Path(path).name)
            item = QListWidgetItem(self.ui.attachedFilesList)
            customWidget = CustomListItem(displayText)
            item.setSizeHint(customWidget.sizeHint())
            # store the path into the label
            customWidget.rightIconButton.customData = path

            # Connect the removeClicked signal to the removeAttachedFile slot
            customWidget.removeClicked.connect(self.removeAttachedFile)

            self.ui.attachedFilesList.setStyleSheet(
            """QListWidget::item {
                background-color: #eef2ff;  /* light blue background */
                border: 1px solid #ccc; 
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #8aa0d7;  /* darker blue background when selected */
            }""")

            self.ui.attachedFilesList.addItem(item)
            self.ui.attachedFilesList.setItemWidget(item, customWidget)

    def removeAttachedFile(self, filePath: str):
        """
        Removes the specified file from attachedFiles, attachedFilesList, and deletes it from the database.

        Args:
            filePath (str): The path of the file to remove.
        """
        logging.info(f"Attempting to remove attached file: {filePath}")

        # Remove from attachedFiles list
        if filePath in self.attachedFiles:
            self.attachedFiles.remove(filePath)
            logging.info(f"Removed '{filePath}' from attachedFiles.")
        else:
            logging.warning(f"File '{filePath}' not found in attachedFiles.")

        # Find and remove the QListWidgetItem
        listWidget = self.ui.attachedFilesList
        itemToRemove = None
        for i in range(listWidget.count()):
            item = listWidget.item(i)
            widget = listWidget.itemWidget(item)
            if hasattr(widget, 'rightIconButton') and getattr(widget.rightIconButton, "customData", None) == filePath:
                itemToRemove = item
                break

        if itemToRemove:
            listWidget.takeItem(listWidget.row(itemToRemove))
            logging.info(f"Removed QListWidgetItem for '{filePath}' from attachedFilesList.")
        else:
            logging.warning(f"No QListWidgetItem found for '{filePath}' in attachedFilesList.")

        # Remove from the database
        parent = self.parentWidget()
        while parent and not hasattr(parent, 'conversationDb'):
            parent = parent.parentWidget()
        if parent and hasattr(parent, 'conversationDb'):
            try:
                # Retrieve the file ID
                cursor = parent.conversationDb.conn.execute(
                    'SELECT id FROM files WHERE file_path = ?', (filePath,))
                row = cursor.fetchone()
                if row:
                    fileId = row[0]
                    # Delete the attachment relationship
                    parent.conversationDb.conn.execute(
                        'DELETE FROM conversation_attachements WHERE conversation_id = ? AND file_id = ?',
                        (self.conversationId, fileId))
                    logging.info(f"Deleted attachment relationship for file ID {fileId} and conversation ID {self.conversationId}.")

                # Clean up orphaned files
                parent.conversationDb.deleteOrphanedFiles()
                logging.info(f"Completed database cleanup for '{filePath}'.")
            except Exception as e:
                logging.error(f"Failed to remove '{filePath}' from the database: {e}")
        else:
            logging.error("ConversationDatabase not found in parent hierarchy.")

    def getLastDirectory(self) -> str:
        """
        Retrieves the last used directory from settings.

        Returns:
            str: The path of the last used directory.
        """
        settingsFile = (Path(__file__).resolve().parent.parent / "settings.ini")
        settings = QSettings(str(settingsFile), QSettings.Format.IniFormat)
        lastDirValue = settings.value("General/lastDirectory", "")
        if lastDirValue:
            return str(Path(lastDirValue).resolve())
        return ""

    def setLastDirectory(self, directory: str):
        """
        Saves the last used directory to settings.

        Args:
            directory (str): The path of the directory to save.
        """
        settingsFile = (Path(__file__).resolve().parent.parent / "settings.ini")
        settings = QSettings(str(settingsFile), QSettings.Format.IniFormat)
        settings.setValue("General/lastDirectory", directory)

    def onSendClicked(self):
        """
        Sends the user text (with any file attachments) to the ChatSession.
        Displays a preview of the estimated token count before sending.
        Disables UI elements while waiting for a reply.
        """
        userText = self.ui.userInput.toPlainText().strip()
        if not userText:
            QMessageBox.warning(self, "Warning", "Please type a message before sending.")
            return

        # Prepare the full user message with attachments
        filePathList = self.attachedFiles
        filePathsStr = ",".join(filePathList)
        attachmentContent = ""
        if filePathsStr.strip():
            attachmentContent = self.chatSession.readFilesContent(filePathsStr)

        fullUserMessage = userText.strip()
        if attachmentContent:
            fullUserMessage += "\n" + attachmentContent.strip()

        # Calculate token count for the new message
        tokensInMessage = len(self.chatSession.encoding.encode(fullUserMessage))
        currentTokenCount = self.chatSession.countTokens()
        newTotalTokens = currentTokenCount + tokensInMessage

        # Disable the input and show busy indicator.
        self.ui.sendButton.setEnabled(False)
        self.ui.attachButton.setEnabled(False)
        self.ui.attachDirectoryButton.setEnabled(False)
        self.ui.attachedFilesList.setEnabled(False)
        self.ui.userInput.setEnabled(False)
        self.ui.busyIndicator.setVisible(True)

        self.appendToConversation("**You:** " + userText)
        self.ui.userInput.clear()
        self.ui.conversationDisplay.moveCursor(QTextCursor.MoveOperation.End)

        # Emit token counts
        self.tokenUpdated.emit(newTotalTokens, newTotalTokens)

        QApplication.processEvents()

        # Proceed to send the message
        worker = WorkerRunnable(self.chatSession, userText, filePathList)
        worker.signals.finished.connect(self.onWorkerFinished)
        worker.signals.error.connect(self.onWorkerError)
        self.threadPool.start(worker)

    def onWorkerFinished(self, reply: str):
        """
        Called when the ChatSession returns a reply.

        Args:
            reply (str): The assistant's reply.
        """
        self.appendToConversation("**Assistant:** " + reply)
        # Emit token counts
        totalTokens = self.chatSession.lastTotalTokens
        currentTokenCount = self.chatSession.countTokens()
        self.tokenUpdated.emit(totalTokens, currentTokenCount)

        # Update the conversation title if it's the first message
        parent = self.parentWidget()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parentWidget()
        if parent and hasattr(parent, 'conversationDb'):
            conversation = parent.conversationDb.getConversationById(self.conversationId)
            if conversation and conversation["title"].startswith("Conversation"):
                firstUserMessage = self.chatSession.getFirstUserMessage()
                if firstUserMessage:
                    # Truncate to seven words
                    title = ' '.join(firstUserMessage.split()[:7])
                    parent.conversationDb.updateConversationTitle(self.conversationId, title)
                    # Emit the titleUpdated signal with conversationId and newTitle
                    self.titleUpdated.emit(self.conversationId, title)

        # Save the updated conversation history to the database
        self.saveConversationHistory()

        self.resetAfterSend()

    def onWorkerError(self, errorMessage: str):
        """
        Called if an error occurs while sending the message.

        Args:
            errorMessage (str): The error message.
        """
        logging.error("Error when sending message: %s", errorMessage, exc_info=True)
        QMessageBox.critical(self, "Error", f"An error occurred: {errorMessage}")
        self.resetAfterSend()

    def resetAfterSend(self):
        """
        Resets the UI (re-enables buttons) after a message is sent.
        """
        self.ui.userInput.clear()
        self.ui.sendButton.setEnabled(True)
        self.ui.attachButton.setEnabled(True)
        self.ui.attachDirectoryButton.setEnabled(True)
        self.ui.attachedFilesList.setEnabled(True)
        self.ui.userInput.setEnabled(True)
        self.ui.busyIndicator.setVisible(False)

    def appendToConversation(self, text: str):
        """ Appends a message to the conversation display with a local timestamp.
        Args:
          text (str): The text to append.
        """
        # Get current UTC time
        utcTime = datetime.datetime.now(datetime.timezone.utc)

        # Convert UTC time to local time
        localTime = utcTime.astimezone()  # Defaults to the system's local timezone

        # Format the timestamp as desired
        formattedTimestamp = localTime.strftime('%Y-%m-%d %H:%M:%S %z')

        fullTextWithTimestamp = f"{text}\n<span style='font-size: small; color: gray;'>{formattedTimestamp}</span>"

        fullHtml = convertMarkdownToHtml(fullTextWithTimestamp)
        newContent = f"""
        <div></div>
        <div style="margin: 0; padding: 0; color: initial; font-family: initial;">
            {fullHtml}
            <br>
        </div>"""
        self.ui.conversationDisplay.append(newContent)

    def saveConversationHistory(self):
        """
        Saves the current conversation history to the database.
        """
        # Assuming MainWindow holds the ConversationDatabase instance
        parent = self.parentWidget()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parentWidget()
        if parent and hasattr(parent, 'conversationDb'):
            parent.conversationDb.updateConversationHistory(
                self.conversationId,
                self.chatSession.conversationHistory
            )
            logging.info(f"Saved updated conversation history for ID {self.conversationId}.")

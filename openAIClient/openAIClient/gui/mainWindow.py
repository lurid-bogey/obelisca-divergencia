import sys
import os
import logging
import configparser
import datetime
from typing import Optional, Tuple
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QMessageBox, QApplication, QComboBox, QLabel, QListWidgetItem,
    QListWidget, QMenu, QInputDialog, QAbstractItemView
)
from PySide6.QtCore import QByteArray, QSettings, Qt, QPoint
from PySide6.QtGui import QIcon, QKeySequence, QAction

from openAIClient.gui.Ui_mainWindow import Ui_MainWindow
from openAIClient.gui.chatTab import ChatTab
from openAIClient.chatSession import ChatSession
from openAIClient.utils.database import ConversationDatabase
from openAIClient.config import getDatabasePath, resourcePath, getDeploymentConfigs


class MainWindow(QMainWindow):
    """
    Main application window for the Azure OpenAI Chat GUI.
    Manages multiple ChatTab instances and integrates conversation management via SQLite.
    """
    def __init__(self, systemPrompt: str):
        super().__init__()
        self.systemPrompt = systemPrompt

        self.setWindowTitle("Azure OpenAI Chat GUI")
        self.resize(700, 600)

        # Load the UI from the compiled .ui file.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.conversationsList.setStyleSheet("""
            QListWidget::item {
                padding: 5px;               /* padding around individual items */
                margin: 2px;                /* spacing between items */
                background-color: #eef2ff;  /* light blue background */
            }
            QListWidget::item:selected {
                background-color: #8aa0d7;  /* darker blue background when selected */
            }
        """)

        # Enable custom context menu
        self.ui.conversationsList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.conversationsList.customContextMenuRequested.connect(self.onConversationsListContextMenu)

        # Configure the File menu.
        self.ui.actionExit.setIcon(QIcon(resourcePath("assets/delete-red.png", forcedPath=True)))
        self.ui.actionExit.triggered.connect(QApplication.quit)

        # Create new chat action.
        self.actionNewChat = QAction("New Chat", self)
        self.actionNewChat.setIcon(QIcon(resourcePath("assets/add-square.png", forcedPath=True)))
        self.actionNewChat.setToolTip('Start a new conversation')
        self.actionNewChat.setShortcut(QKeySequence("Ctrl+T"))
        self.actionNewChat.triggered.connect(self.createNewChatTab)

        # Create delete chat action.
        self.actionDeleteChat = QAction("Delete Chat", self)
        self.actionDeleteChat.setIcon(QIcon(resourcePath("assets/subtract-square.png", forcedPath=True)))
        self.actionDeleteChat.setToolTip('Delete selected conversation(s)')
        self.actionDeleteChat.setShortcut(QKeySequence(Qt.Key.Key_Delete))
        self.actionDeleteChat.triggered.connect(self.deleteSelectedChat)

        # Add the new actions to the File menu.
        self.ui.menuFile.addAction(self.actionNewChat)
        self.ui.menuFile.addAction(self.actionDeleteChat)
        self.ui.menuFile.addSeparator()

        # Remove the Exit action and add it at the end to ensure it is the last item.
        self.ui.menuFile.removeAction(self.ui.actionExit)
        self.ui.menuFile.addAction(self.ui.actionExit)

        # Also add the new actions to the toolbar.
        self.ui.toolBar.addAction(self.actionNewChat)
        self.ui.toolBar.addAction(self.actionDeleteChat)

        # --- Deployment Combobox Setup ---
        self.deploymentComboBox = QComboBox()
        self.loadDeploymentOptions()  # Populate the combobox from settings.ini
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addWidget(QLabel("Deployment: "))
        self.ui.toolBar.addWidget(self.deploymentComboBox)
        # -------------------------------------

        # --- Token Display Labels ---
        self.totalTokensLabel = QLabel("Tokens: <b>0</b>")
        self.ui.statusBar.addPermanentWidget(self.totalTokensLabel)
        # ------------------------------

        # Initialize the SQLite database.
        dbPath = getDatabasePath()
        self.conversationDb = ConversationDatabase(dbPath)
        logging.info(f"Initialized ConversationDatabase at {dbPath}")

        # Clear any pre-existing tabs.
        self.ui.tabWidget.clear()
        self.chatTabs = []
        self.conversationIdToTab = {}
        self.currentChatTab = None

        # signals
        self.ui.tabWidget.currentChanged.connect(self.onTabChanged)
        self.ui.conversationsList.itemChanged.connect(self.onConversationTitleEdited)
        self.ui.conversationsList.itemClicked.connect(self.onConversationSelected)  # <-- Added

        # Enable tab closable
        self.ui.tabWidget.setTabsClosable(True)
        self.ui.tabWidget.tabCloseRequested.connect(self.onTabCloseRequested)

        # Create context menu actions
        self.createContextMenuActions()

        self.loadWindowGeometry()
        self.createNewChatTab()
        self.populateConversationsList()
        self.setWindowIcon(QIcon(resourcePath("assets/blah.png", forcedPath=True)))

    def createContextMenuActions(self):
        """
        Creates actions for the context menu.
        """
        self.contextMenu = QMenu(self)

        # Delete Action
        self.actionContextDelete = QAction("Delete", self)
        self.actionContextDelete.triggered.connect(self.deleteSelectedChat)

        # Rename Action
        self.actionContextRename = QAction("Rename", self)
        self.actionContextRename.triggered.connect(self.renameSelectedConversation)

        # Summarize Action
        self.actionContextSummarize = QAction("Summarize", self)
        self.actionContextSummarize.triggered.connect(self.summarizeSelectedConversation)

        self.contextMenu.addAction(self.actionContextDelete)
        self.contextMenu.addAction(self.actionContextRename)
        self.contextMenu.addAction(self.actionContextSummarize)

    def onConversationsListContextMenu(self, position: QPoint):
        """
        Displays the context menu at the given position.

        Args:
            position (QPoint): The position where the context menu is triggered.
        """
        # Get the global position
        globalPosition = self.ui.conversationsList.viewport().mapToGlobal(position)

        # Determine the number of selected items
        selectedItems = self.ui.conversationsList.selectedItems()
        selectCount = len(selectedItems)

        # Enable or disable actions based on selection
        if selectCount == 0:
            # If no item is selected, do not show the context menu
            return
        elif selectCount > 1:
            # If multiple items are selected, disable Rename and Summarize
            self.actionContextRename.setEnabled(False)
            self.actionContextSummarize.setEnabled(False)
        else:
            # Single selection: enable all actions
            self.actionContextRename.setEnabled(True)
            self.actionContextSummarize.setEnabled(True)

        # Show the context menu
        self.contextMenu.exec(globalPosition)

    def renameSelectedConversation(self, title):
        """
        Renames the selected conversation.
        """
        selectedItems = self.ui.conversationsList.selectedItems()
        if len(selectedItems) != 1:
            QMessageBox.warning(self, "Rename Conversation", "Please select a single conversation to rename.")
            return

        item = selectedItems[0]
        conversationId = item.data(Qt.ItemDataRole.UserRole)

        if title:
            # user already provided title
            newTitle = title.strip()
        else:
            # Prompt the user for a new name
            newTitle, ok = QInputDialog.getText(self, "Rename Conversation", "Enter new conversation title:", text=item.text())
            if ok and newTitle.strip():
                newTitle = newTitle.strip()
            else:
                # QMessageBox.information(self, "Rename Conversation", "Renaming canceled or invalid title.")
                return

        # Update the database
        self.conversationDb.updateConversationTitle(conversationId, newTitle)
        # Update the QListWidgetItem
        item.setText(newTitle)
        logging.info(f"Renamed conversation ID {conversationId} to '{newTitle}'.")

    def summarizeSelectedConversation(self):
        """
        Generates and displays a summary of the selected conversation.
        """
        selectedItems = self.ui.conversationsList.selectedItems()
        if len(selectedItems) != 1:
            QMessageBox.warning(self, "Summarize Conversation", "Please select a single conversation to summarize.")
            return

        item = selectedItems[0]
        conversationId = item.data(Qt.ItemDataRole.UserRole)

        # Retrieve the associated ChatTab
        if conversationId in self.conversationIdToTab:
            chatTab = self.conversationIdToTab[conversationId]
            summary = chatTab.chatSession.generateSummary()
            if summary:
                # QMessageBox.information(self, "Conversation Summary", f"Summary:\n{summary}")
                self.renameSelectedConversation(summary)
                logging.info(f"Generated summary for conversation ID {conversationId}.")
            else:
                QMessageBox.warning(self, "Summarize Conversation", "Failed to generate summary.")
                logging.warning(f"Failed to generate summary for conversation ID {conversationId}.")
        else:
            # If the conversation tab is not open, load the conversation first
            conversation = self.conversationDb.getConversationById(conversationId)
            if conversation:
                deploymentName = conversation["deployment_name"]
                # Find the deployment config matching the deploymentName
                deployments = getDeploymentConfigs()
                deploymentConfig = next((d for d in deployments if d["deploymentName"] == deploymentName), None)

                if not deploymentConfig:
                    QMessageBox.warning(self, "Deployment Not Found", f"No deployment configuration found for '{deploymentName}'.")
                    logging.error(f"No deployment configuration found for '{deploymentName}'.")
                    return

                chatSession = ChatSession(
                    systemPrompt=self.systemPrompt,
                    deploymentConfig=deploymentConfig,
                    maxContextTokens=100000
                )
                # Load existing conversation history
                chatSession.loadConversationHistory(conversation["conversation_history"])

                # Create a temporary ChatTab to generate the summary
                summary = chatSession.generateSummary()
                if summary:
                    # QMessageBox.information(self, "Conversation Summary", f"Summary:\n{summary}")
                    self.renameSelectedConversation(summary)
                    logging.info(f"Generated summary for conversation ID {conversationId}.")
                else:
                    QMessageBox.warning(self, "Summarize Conversation", "Failed to generate summary.")
                    logging.warning(f"Failed to generate summary for conversation ID {conversationId}.")
            else:
                QMessageBox.warning(self, "Summarize Conversation", "Selected conversation could not be loaded.")

    def loadDeploymentOptions(self):
        """
        Reads the deployments from the settings.ini file and populates the combobox.
        """
        deployments = getDeploymentConfigs()
        if not deployments:
            deployments = [{
                "section": "Default",
                "type": "openai",
                "endpoint": "https://api.openai.com/v1",
                "deploymentName": "gpt-3.5-turbo",
                "apiVersion": ""
            }]
            logging.warning("No deployments found. Using default deployment.")

        self.deploymentComboBox.clear()
        for deployment in deployments:
            displayName = deployment["deploymentName"]
            self.deploymentComboBox.addItem(displayName, userData=deployment)
        logging.info("Loaded deployments into combobox.")

    def populateConversationsList(self):
        """
        Populates the conversationsList QListWidget with conversations from the database.
        """
        self.ui.conversationsList.clear()
        conversations = self.conversationDb.getAllConversations()
        for convo in conversations:
            convoId, title, deploymentName, createdAt, conversationHistory, tokens = convo
            itemText = f"{title} (Tokens: {tokens})"
            item = QListWidgetItem(itemText)
            item.setData(Qt.ItemDataRole.UserRole, convoId)  # Store the conversation ID

            # Set the chat-spark icon for each item
            chatIconPath = resourcePath("assets/chat-spark.png", forcedPath=True)
            if os.path.exists(chatIconPath):
                item.setIcon(QIcon(chatIconPath))
            else:
                logging.warning(f"Icon file not found at: {chatIconPath}")

            # Parse the UTC timestamp
            try:
                utcTimestamp = datetime.datetime.fromisoformat(createdAt)
                if utcTimestamp.tzinfo is None:
                    utcTimestamp = utcTimestamp.replace(tzinfo=datetime.timezone.utc)
                localTimestamp = utcTimestamp.astimezone()
                formattedTimestamp = localTimestamp.strftime('%Y-%m-%d %H:%M:%S %z')
            except ValueError:
                # Fallback if parsing fails
                formattedTimestamp = createdAt

            item.setToolTip(f"{formattedTimestamp} | Tokens: {tokens}")
            # Make the item editable
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.ui.conversationsList.addItem(item)
        logging.info("Populated conversationsList with %d conversations.", len(conversations))

    def createNewChatTab(self, chatSession: ChatSession = None, conversationId: Optional[int] = None):
        """
        Creates a new chat tab with its own ChatSession.
        If no ChatSession is provided, a new one is created using the currently selected deployment.
        If creating a tab for an existing conversation, uses the provided conversationId.
        """
        if conversationId is not None:
            # Check if the conversation is already open
            if conversationId in self.conversationIdToTab:
                existingTab = self.conversationIdToTab[conversationId]
                tabIndex = self.ui.tabWidget.indexOf(existingTab)
                if tabIndex != -1:
                    self.ui.tabWidget.setCurrentIndex(tabIndex)
                    logging.info(f"Switched to existing tab for conversation ID {conversationId}.")
                    return  # Early exit since the tab is already open

        if chatSession in (None, False):
            settingsFile = (Path(__file__).resolve().parent.parent / "settings.ini")
            settings = QSettings(str(settingsFile), QSettings.Format.IniFormat)
            lastSelectedDeployment = settings.value("General/lastSelectedDeployment", "")
            index = self.deploymentComboBox.findText(str(lastSelectedDeployment))

            if index != -1:
                self.deploymentComboBox.setCurrentIndex(index)   # Set the current index if found

            # Retrieve the deployment from the combobox
            selectedIndex = self.deploymentComboBox.currentIndex()
            if selectedIndex < 0:
                QMessageBox.warning(self, "No Deployment", "No deployment configuration selected.")
                logging.error("No deployment configuration selected.")
                return

            deploymentConfig = self.deploymentComboBox.currentData()
            if not deploymentConfig:
                QMessageBox.warning(self, "Invalid Deployment", "Selected deployment configuration is invalid.")
                logging.error("Selected deployment configuration is invalid.")
                return

            # Create a new ChatSession without conversationId
            chatSession = ChatSession(
                systemPrompt=self.systemPrompt,
                deploymentConfig=deploymentConfig,
                db=self.conversationDb,
                maxContextTokens=100000
            )

            # Add a new conversation to the database with a temporary title
            title = f"Conversation {len(self.chatTabs) + 1}"
            conversationId = self.conversationDb.addConversation(title, chatSession.deploymentName, chatSession.conversationHistory)
            if conversationId is None:
                QMessageBox.critical(self, "Database Error", "Failed to create a new conversation. Please check the logs for more details.")
                logging.error("Failed to create a new conversation. Aborting tab creation.")
                return
            logging.info(f"Added new conversation to database with ID {conversationId} and title '{title}'.")

            # Add the new conversation to the conversationsList
            itemText = f"{title} (Tokens: {chatSession.countTokens()})"
            item = QListWidgetItem(itemText)
            item.setData(Qt.ItemDataRole.UserRole, conversationId)

            # Set the chat-spark icon for the new item
            chatIconPath = resourcePath("assets/chat-spark.png", forcedPath=True)
            if os.path.exists(chatIconPath):
                item.setIcon(QIcon(chatIconPath))
            else:
                logging.warning(f"Icon file not found at: {chatIconPath}")

            # Set the tooltip to the stored timestamp
            conversation = self.conversationDb.getConversationById(conversationId)
            if conversation and "created_at" in conversation:
                createdAt = conversation["created_at"]
                utcTimestamp = datetime.datetime.fromisoformat(createdAt)
                if utcTimestamp.tzinfo is None:
                    utcTimestamp = utcTimestamp.replace(tzinfo=datetime.timezone.utc)
                localTimestamp = utcTimestamp.astimezone()
                isoTimestamp = localTimestamp.strftime('%Y-%m-%d %H:%M:%S %z')
            else:
                # Fallback to current UTC time if retrieval fails
                isoTimestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S %z')

            item.setToolTip(f"{isoTimestamp} | Tokens: {chatSession.countTokens()}")
            # Make the item editable
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.ui.conversationsList.insertItem(0, item)  # Insert at top
            logging.info("Inserted new conversation into conversationsList.")

        # Else, creating a tab for an existing conversation
        newTab = ChatTab(chatSession, conversationId, parent=self)
        # Connect the tokenUpdated signal
        newTab.tokenUpdated.connect(self.updateTokenDisplay)
        # Connect the titleUpdated signal
        newTab.titleUpdated.connect(self.updateConversationsListItem)

        # Use the deployment name in the tab title.
        tabTitle = f"Chat - {chatSession.deploymentName}"
        tabIndex = self.ui.tabWidget.addTab(newTab, tabTitle)
        self.ui.tabWidget.setCurrentIndex(tabIndex)
        self.chatTabs.append(newTab)

        # Update the mapping dictionary
        self.conversationIdToTab[conversationId] = newTab

        logging.info(f"Created new chat tab with deployment: {chatSession.deploymentName} for conversation ID {conversationId}.")

    def onConversationSelected(self, item: QListWidgetItem):
        """
        Loads the selected conversation into a new chat tab and highlights it.

        Args:
            item (QListWidgetItem): The selected QListWidgetItem representing a conversation.
        """
        conversationId = item.data(Qt.ItemDataRole.UserRole)
        conversation = self.conversationDb.getConversationById(conversationId)
        if conversation:
            # Check if the conversation tab is already open
            if conversationId in self.conversationIdToTab:
                existingTab = self.conversationIdToTab[conversationId]
                tabIndex = self.ui.tabWidget.indexOf(existingTab)
                if tabIndex != -1:
                    self.ui.tabWidget.setCurrentIndex(tabIndex)
                    logging.info(f"Switched to existing tab for conversation ID {conversationId}.")
                    return  # Early exit since the tab is already open

            # Initialize ChatSession with existing history and correct deployment name
            deploymentName = conversation["deployment_name"]
            # Find the deployment config matching the deploymentName
            deployments = getDeploymentConfigs()
            deploymentConfig = next((d for d in deployments if d["deploymentName"] == deploymentName), None)

            if not deploymentConfig:
                QMessageBox.warning(self, "Deployment Not Found", f"No deployment configuration found for '{deploymentName}'.")
                logging.error(f"No deployment configuration found for '{deploymentName}'.")
                return

            chatSession = ChatSession(
                systemPrompt=self.systemPrompt,
                deploymentConfig=deploymentConfig,
                conversationId=conversationId,
                db=self.conversationDb,
                maxContextTokens=100000
            )
            # Load existing conversation history
            chatSession.loadConversationHistory(conversation["conversation_history"])
            logging.info(f"Loaded conversation ID {conversationId} into a new chat tab.")
            self.createNewChatTab(chatSession, conversationId)
        else:
            QMessageBox.warning(self, "Error", "Selected conversation could not be loaded.")

    def deleteSelectedChat(self):
        """
        Deletes the currently selected conversation(s) from the database and updates the conversationsList.
        """
        selectedItems = self.ui.conversationsList.selectedItems()
        if not selectedItems:
            QMessageBox.information(self, "No Selection", "Please select a conversation to delete.")
            return

        confirm = QMessageBox.question(
            self,
            "Delete Conversation",
            "Are you sure you want to delete the selected conversation(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        for item in selectedItems:
            conversationId = item.data(Qt.ItemDataRole.UserRole)
            self.conversationDb.deleteConversationById(conversationId)
            self.ui.conversationsList.takeItem(self.ui.conversationsList.row(item))
            logging.info(f"Deleted conversation ID {conversationId} from the database.")

            # Check if the tab is open and remove it
            if conversationId in self.conversationIdToTab:
                tab = self.conversationIdToTab.pop(conversationId)
                tabIndex = self.ui.tabWidget.indexOf(tab)
                if tabIndex != -1:
                    self.ui.tabWidget.removeTab(tabIndex)
                    self.chatTabs.remove(tab)
                    logging.info(f"Removed tab for deleted conversation ID {conversationId}.")

        # QMessageBox.information(self, "Deleted", "Selected conversation(s) have been deleted.")

    def updateTokenDisplay(self, totalTokens: int, currentTokenCount: int):
        """
        Updates the token display labels in the status bar.

        Args:
            totalTokens (int): The total tokens used.
            currentTokenCount (int): The current token count.
        """
        self.totalTokensLabel.setText(f"Tokens: <b>{totalTokens}</b>")

    def onTabChanged(self, index: int):
        """
        Slot to handle tab changes. Updates the status bar to reflect the token counts
        of the newly active chat tab and highlights the corresponding conversation in the list.

        Args:
            index (int): The index of the newly active tab.
        """
        # Disconnect signal from previous chat tab
        if self.currentChatTab:
            try:
                self.currentChatTab.tokenUpdated.disconnect(self.updateTokenDisplay)
            except TypeError:
                pass  # No connection exists

        # Get the new current chat tab
        newChatTab = self.chatTabs[index] if index >= 0 and index < len(self.chatTabs) else None
        self.currentChatTab = newChatTab

        if newChatTab:
            # Connect the tokenUpdated signal
            newChatTab.tokenUpdated.connect(self.updateTokenDisplay)
            # Update the status bar with the current token counts
            totalTokens = newChatTab.chatSession.lastTotalTokens
            currentTokenCount = newChatTab.chatSession.countTokens()
            self.updateTokenDisplay(totalTokens, currentTokenCount)
            logging.info("Switched to tab index %d with total tokens: %d and current tokens: %d",
                         index, totalTokens, currentTokenCount)

            # Highlight the corresponding conversation in the list
            conversationId = newChatTab.conversationId
            self.highlightConversationInList(conversationId)
        else:
            # If no tab is active, reset the status bar and selection
            self.totalTokensLabel.setText("Tokens: <b>0</b>")
            self.ui.conversationsList.clearSelection()
            logging.info("No active chat tab. Resetting token display and conversation selection.")

    def highlightConversationInList(self, conversationId: int):
        """
        Highlights the QListWidgetItem corresponding to the given conversation ID.

        Args:
            conversationId (int): The ID of the conversation to highlight.
        """
        # ensure that the conversationsList allows only single selections
        self.ui.conversationsList.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        listWidget = self.ui.conversationsList
        for row in range(listWidget.count()):
            item = listWidget.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == conversationId:
                listWidget.setCurrentItem(item)
                listWidget.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)
                logging.info(f"Highlighted conversation ID {conversationId} in the list.")
                break

        # revert to extended selection
        self.ui.conversationsList.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def onTabCloseRequested(self, index: int):
        """
        Handles the event when a tab's close button is clicked.
        """
        if index < 0 or index >= len(self.chatTabs):
            return

        tab = self.chatTabs.pop(index)
        conversationId = tab.conversationId

        # Remove from the mapping
        if conversationId in self.conversationIdToTab:
            del self.conversationIdToTab[conversationId]

        # Remove the tab from the widget
        self.ui.tabWidget.removeTab(index)
        logging.info(f"Manually closed tab for conversation ID {conversationId}.")

    def loadWindowGeometry(self):
        """
        Loads the window's geometry from the INI file and adjusts it to ensure
        the window is fully visible across all available screens.
        """
        # Assuming deployments are already loaded into the combobox
        settingsFile = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "settings.ini")
        settings = QSettings(settingsFile, QSettings.Format.IniFormat)
        geometry = settings.value("Window/geometry")

        # Restore Geometry if Available
        if geometry:
            if isinstance(geometry, str):
                geometry = QByteArray.fromHex(geometry.encode())
            if isinstance(geometry, QByteArray):
                if self.restoreGeometry(geometry):
                    logging.info("Loaded window geometry from settings.")
                else:
                    logging.warning("Failed to restore window geometry. Using default.")
            else:
                logging.warning("Invalid geometry format in settings. Using default.")
        else:
            logging.info("No window geometry found in settings. Centering the window.")
            # Default to Primary Screen
            primaryScreen = QApplication.primaryScreen()
            screenGeo = primaryScreen.availableGeometry()
            self.resize(700, 600)  # Default size
            self.move(screenGeo.center() - self.rect().center())

        # Ensure the window is fully within at least one screen
        self.ensureWindowWithinAnyScreen()

    def ensureWindowWithinAnyScreen(self):
        """
        Ensures that the window is fully visible on at least one screen.
        If not, repositions it to the primary screen.
        """
        windowRect = self.frameGeometry()
        screens = QApplication.screens()
        isVisible = False

        for screen in screens:
            screenGeo = screen.availableGeometry()
            if screenGeo.contains(windowRect):
                isVisible = True
                break

        if not isVisible and screens:
            # Move to Primary Screen
            primaryScreen = QApplication.primaryScreen()
            screenGeo = primaryScreen.availableGeometry()

            newLeft = screenGeo.left() + 100  # Offset to prevent exact centering
            newTop = screenGeo.top() + 100

            # Ensure the window fits within the primary screen
            newLeft = min(newLeft, screenGeo.right() - self.width())
            newTop = min(newTop, screenGeo.bottom() - self.height())

            # Move the window
            self.move(newLeft, newTop)
            logging.info("Repositioned window to primary screen to ensure visibility.")

    def closeEvent(self, event):
        """
        Ensure the window settings are saved when the application is closed.
        """
        self.writeSettings()
        self.conversationDb.close()
        super().closeEvent(event)

    def writeSettings(self):
        """
        Saves the window's geometry and the last selected deployment to the INI file.
        """
        settingsFile = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "settings.ini")
        settings = QSettings(settingsFile, QSettings.Format.IniFormat)
        settings.setValue("Window/geometry", self.saveGeometry())
        # Save the last selected deployment
        lastDeployment = self.deploymentComboBox.currentData()
        if lastDeployment:
            settings.setValue("General/lastSelectedDeployment", lastDeployment["deploymentName"])
            logging.info(f"Saved last selected deployment: {lastDeployment['deploymentName']}")
        logging.info("Saved window geometry and last selected deployment to %s", settingsFile)

    def updateConversationsListItem(self, conversationId: int, newTitle: str):
        """
        Updates the corresponding QListWidgetItem with the new title.

        Args:
            conversationId (int): The ID of the conversation.
            newTitle (str): The new title for the conversation.
        """
        for row in range(self.ui.conversationsList.count()):
            item = self.ui.conversationsList.item(row)
            convoId = item.data(Qt.ItemDataRole.UserRole)
            if convoId == conversationId:
                # Update the item text without the timestamp
                item.setText(newTitle)
                break

    def onConversationTitleEdited(self, item: QListWidgetItem):
        """
        Handles the event when a conversation title is edited by the user.

        Args:
            item (QListWidgetItem): The QListWidgetItem that was edited.
        """
        conversationId = item.data(Qt.ItemDataRole.UserRole)
        newTitle = item.text().strip()

        if not newTitle:
            QMessageBox.warning(self, "Invalid Title", "Conversation title cannot be empty.")
            # Revert to the previous title
            conversation = self.conversationDb.getConversationById(conversationId)
            if conversation:
                item.setText(conversation["title"])
                # item.setToolTip(conversation["created_at"])
            return

        # Update the database with the new title
        self.conversationDb.updateConversationTitle(conversationId, newTitle)
        logging.info(f"User updated conversation ID {conversationId} title to '{newTitle}'.")

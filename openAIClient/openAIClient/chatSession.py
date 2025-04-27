import os
import logging
from typing import Optional, Dict
from docx import Document
from pdfminer.high_level import extract_text
import tiktoken

from openAIClient.config import initOpenAiClient
from openAIClient.utils.database import ConversationDatabase


class ChatSession:
    FOLDER_BLACKLIST = (".git", ".github", ".svn", ".idea", ".vscode", "__pycache__")
    # List of file extensions that are considered binary.
    BINARY_EXTENSIONS = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".zip",
        ".tar",
        ".gz",
        ".url",
        ".db",
        ".sqlite",
        ".exe",
        ".dll",
        ".pyd",
    )

    FILE_MARKER_START = "<|file|>"
    FILE_MARKER_END = "<|/file|>"

    def __init__(
        self,
        systemPrompt: str,
        deploymentConfig: Dict[str, str],
        conversationId: Optional[int] = None,
        db: Optional[ConversationDatabase] = None,
        maxContextTokens: int = 100000,
    ):
        """
        Initializes the conversation with the system prompt or existing history.

        Args:
            systemPrompt (str): The system prompt for the conversation.
            deploymentConfig (Dict[str, str]): The deployment configuration dictionary.
            conversationId (Optional[int]): The ID of the conversation in the database.
            db (Optional[ConversationDatabase]): The database instance.
            maxContextTokens (int, optional): Maximum number of context tokens. Defaults to 100000.
        """
        # Initialize OpenAI client
        self.client = initOpenAiClient(deploymentConfig)

        self.conversationHistory = [{"role": "user", "content": systemPrompt}]
        self.deploymentName = deploymentConfig["deploymentName"]
        self.lastTotalTokens = 0  # Attribute to hold the total tokens from API response.
        # Set a file size limit of 5MB per file.
        self.maxFileSize = 5 * 1024 * 1024
        # Set maximum context tokens (e.g., 4096 for GPT-3.5)
        self.maxContextTokens = maxContextTokens
        # Initialize the tokenizer
        self.encoding = tiktoken.get_encoding("cl100k_base")  # Use appropriate encoding
        logging.info("Initialized new chat session with system prompt and deployment: %s.", self.deploymentName)

        self.conversationId = conversationId
        self.db = db

    def loadConversationHistory(self, conversationHistory: list):
        """
        Loads existing conversation history into the session.

        Args:
            conversationHistory (list): The conversation history to load.
        """
        self.conversationHistory = conversationHistory
        logging.info("Loaded existing conversation history into ChatSession.")

    def extractTextFromDocx(self, filePath: str) -> str:
        try:
            doc = Document(filePath)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logging.error(f"Error extracting text from DOCX: {e}")
            return ""

    def extractTextFromPdf(self, filePath: str) -> str:
        try:
            text = extract_text(filePath)
            return text
        except Exception as e:
            logging.error(f"Error extracting text from PDF: {e}")
            return ""

    def _readSingleFile(self, filePath: str, baseDir: Optional[str] = None) -> str:
        """
        Attempts to read a single file. If the file is too large,
        has a binary extension, or fails to decode (non-UTF8), it returns an empty string.
        If a baseDir is provided (for files inside a directory), the file’s relative
        path is used in the output header.
        """
        try:
            fileSize = os.path.getsize(filePath)
            if fileSize > self.maxFileSize:
                logging.warning("File %s is too large (%d bytes) and will be skipped.", filePath, fileSize)
                return ""

            lowerFilePath = filePath.lower()

            if lowerFilePath.endswith(self.BINARY_EXTENSIONS):
                logging.info("Skipping binary file: %s", filePath)
                return ""
            elif lowerFilePath.endswith(".docx"):
                logging.info("Processing DOCX file: %s", filePath)
                fileContent = self.extractTextFromDocx(filePath)
            elif lowerFilePath.endswith(".pdf"):
                logging.info("Processing PDF file: %s", filePath)
                fileContent = self.extractTextFromPdf(filePath)
            else:
                with open(filePath, "r", encoding="utf-8") as fileHandle:
                    fileContent = fileHandle.read()

            if baseDir:
                relativePath = os.path.relpath(filePath, baseDir)
                header = f"\n{self.FILE_MARKER_START}[Content from {baseDir}/{relativePath}]:\n"
                footer = f"{self.FILE_MARKER_END}"
            else:
                header = f"\n{self.FILE_MARKER_START}[Content from {filePath}]:\n"
                footer = f"{self.FILE_MARKER_END}"
            logging.info("Successfully read file: %s", filePath)
            return header + fileContent + footer + "\n"
        except UnicodeDecodeError as ude:
            logging.warning("Unicode decode error for file %s: %s", filePath, ude)
        except Exception as error:
            logging.error("Error reading file %s: %s", filePath, error)
        return ""

    def readFilesContent(self, filePathsStr: str) -> str:
        """
        Given a comma-separated string of file or directory paths, reads and combines their contents.
        For directories, it recursively traverses each folder (ignoring blacklisted folder names)
        and adds each file’s content with a header. Files that are too large or appear to be binary
        are skipped.
        """
        contentFragments = []
        filePaths = filePathsStr.split(",")
        for filePath in filePaths:
            filePath = filePath.strip()
            if not filePath:
                continue
            if not os.path.exists(filePath):
                logging.warning("File or directory %s does not exist.", filePath)
                continue

            if os.path.isdir(filePath):
                logging.info("Processing directory: %s", filePath)
                for root, dirs, files in os.walk(filePath):
                    # Filter out blacklisted directories.
                    dirs[:] = [dirName for dirName in dirs if dirName not in self.FOLDER_BLACKLIST]
                    for fileName in files:
                        fullPath = os.path.join(root, fileName)
                        fileContent = self._readSingleFile(fullPath, filePath)
                        if fileContent:
                            contentFragments.append(fileContent)
            else:
                fileContent = self._readSingleFile(filePath)
                if fileContent:
                    contentFragments.append(fileContent)
        return "".join(contentFragments)

    def countTokens(self) -> int:
        """
        Counts the tokens in the conversationHistory using tiktoken for accurate counting.
        """
        total = 0
        for message in self.conversationHistory:
            text = message.get("content", "")
            total += len(self.encoding.encode(text))
        return total

    def trimConversationHistory(self):
        """
        Trims the conversation history to ensure total tokens are within the maximum context limit.
        Removes the oldest user and assistant messages.
        """
        while self.countTokens() > self.maxContextTokens:
            if len(self.conversationHistory) > 2:
                # Remove the second message (first user message after system prompt)
                removed = self.conversationHistory.pop(1)
                logging.info("Removed oldest message to trim tokens: %s", removed)
            else:
                # If only system prompt and one message left, break to avoid removing system prompt
                break

    def sendMessage(self, userText: str, filePathList: list) -> str:
        """
        Given the user's text and a list of file/directory paths, read their contents, append their
        content to the user text, update the conversationHistory, then call the OpenAI API
        and return the assistant's reply.
        """
        filePathsStr = ",".join(filePathList)
        attachmentContent = ""
        if filePathsStr.strip():
            attachmentContent = self.readFilesContent(filePathsStr)

        redactedUserMessage = userText.strip()  # The message that gets saved in the DB. Does not include file content.
        fullUserMessage = userText.strip()  # The message that gets sent to OpenAI. Includes file content.
        if attachmentContent:
            fullUserMessage += "\n" + attachmentContent.strip()

        # Schizophrenia maxima.
        # We have two conversations:
        #       * one for OpenAI,
        #       * one for the database.
        # The database should not include file content.
        apiConversationHistory = list(self.conversationHistory)
        apiConversationHistory.append({"role": "user", "content": fullUserMessage})
        self.conversationHistory.append({"role": "user", "content": redactedUserMessage})

        # Trim conversation history if necessary
        self.trimConversationHistory()

        # Optionally log the current token count before sending the API call.
        currentTokens = self.countTokens()
        logging.info("Current token count (before API call): %d", currentTokens)

        try:
            response = self.client.chat.completions.create(
                model=self.deploymentName,
                messages=apiConversationHistory,  # Send the full conversation including file content
            )
            reply = response.choices[0].message.content
            # Extract token usage from the API response if available.
            totalUsage = response.usage.total_tokens if response.usage else None
            if totalUsage is not None:
                self.lastTotalTokens = totalUsage
                # Update tokens in the database
                if self.db and self.conversationId:
                    self.db.updateConversationTokens(self.conversationId, self.lastTotalTokens)
            logging.info("Received reply from OpenAI API. Total tokens used: %s", self.lastTotalTokens)

            # Append the assistant's reply to the conversationHistory (DB storage)
            self.conversationHistory.append({"role": "assistant", "content": reply})

            # Trim conversation history again if necessary after appending the reply
            self.trimConversationHistory()

            # Log the new token count after receiving the reply.
            newTokenCount = self.countTokens()
            logging.info("Current token count (after API call): %d", newTokenCount)

            # Update tokens in database
            if self.db and self.conversationId:
                self.db.updateConversationTokens(self.conversationId, newTokenCount)

            return reply
        except Exception as error:
            errorMessage = f"Error during API call: {error}"
            logging.error(errorMessage, exc_info=True)
            return errorMessage

    def getFirstUserMessage(self) -> Optional[str]:
        """
        Retrieves the first user message from the conversation history.

        Returns:
            Optional[str]: The first user message or None if not found.
        """
        for message in self.conversationHistory:
            if message.get("role") == "user":
                return message.get("content", "").strip()
        return None

    def generateSummary(self) -> Optional[str]:
        """
        Generates a summary of the conversation using the OpenAI API.

        Returns:
            Optional[str]: The summary text or None if generation fails.
        """
        try:
            summaryPrompt = "Summarize the following conversation in seven words or less:\n" f"{self.getConversationText()}"
            response = self.client.chat.completions.create(
                model=self.deploymentName,
                messages=[{"role": "user", "content": summaryPrompt}],
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            logging.error(f"Failed to generate summary: {e}")
            return None

    def getConversationText(self) -> str:
        """
        Retrieves the full text of the conversation.

        Returns:
            str: The concatenated conversation messages.
        """
        texts = [msg["content"] for msg in self.conversationHistory]
        return "\n".join(texts)

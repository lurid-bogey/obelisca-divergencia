import sqlite3
import logging
import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Tuple


class ConversationDatabase:
    def __init__(self, dbPath: str):
        """
        Initializes the ConversationDatabase with the given SQLite database path.

        Args:
            dbPath (str): The path to the SQLite database file.
        """
        self.dbPath = dbPath
        self.conn = sqlite3.connect(self.dbPath)
        self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        self.createTables()
        self.addTokensColumnIfNotExists()

    def createTables(self):
        """
        Creates the conversations table if it does not already exist.
        """
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    deployment_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    conversation_history TEXT NOT NULL,
                    tokens INTEGER DEFAULT 0
                )
            """
            )

            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE 
                )
            """
            )

            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_attachements (
                    conversation_id INTEGER,
                    file_id INTEGER,
                    PRIMARY KEY (conversation_id, file_id),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
                )
            """
            )

    def addTokensColumnIfNotExists(self):
        """
        Adds the 'tokens' column to the 'conversations' table if it doesn't exist.
        """
        try:
            cursor = self.conn.execute("PRAGMA table_info(conversations)")
            columns = [row[1].lower() for row in cursor.fetchall()]
            if "tokens" not in columns:
                with self.conn:
                    self.conn.execute("ALTER TABLE conversations ADD COLUMN tokens INTEGER DEFAULT 0")
                    logging.info("Added 'tokens' column to 'conversations' table.")
            else:
                logging.info("'tokens' column already exists in 'conversations' table.")
        except sqlite3.Error as e:
            logging.error(f"Error adding 'tokens' column: {e}")

    def addConversation(self, title: str, deploymentName: str, conversationHistory: list, tokens: int = 0) -> Optional[int]:
        """
        Adds a new conversation to the database.

        Args:
            title (str): The title of the conversation.
            deploymentName (str): The OpenAI deployment name associated with the conversation.
            conversationHistory (list): The history of the conversation.
            tokens (int, optional): The number of tokens used in the conversation. Defaults to 0.

        Returns:
            Optional[int]: The ID of the newly created conversation, or None if failed.
        """
        # Use timezone-aware UTC timestamp
        created_at = datetime.now(timezone.utc).isoformat()
        conversation_json = json.dumps(conversationHistory)
        try:
            with self.conn:
                cursor = self.conn.execute(
                    """
                    INSERT INTO conversations (title, deployment_name, created_at, conversation_history, tokens)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (title, deploymentName, created_at, conversation_json, tokens),
                )
                logging.info(f"Inserted conversation '{title}' with ID {cursor.lastrowid}")
                return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Failed to add conversation '{title}' to database: {e}")
            return None
        except Exception as ex:
            logging.exception(f"Unexpected error when adding conversation '{title}': {ex}")
            return None

    def getAllConversations(self) -> List[Tuple[int, str, str, str, str, int]]:
        """
        Retrieves all conversations from the database.

        Returns:
            List[Tuple[int, str, str, str, str, int]]: A list of tuples containing conversation details.
        """
        cursor = self.conn.execute(
            """
            SELECT id, title, deployment_name, created_at, conversation_history, tokens FROM conversations ORDER BY created_at DESC
        """
        )
        return cursor.fetchall()

    def getConversationById(self, conversationId: int) -> Optional[dict]:
        """
        Retrieves a specific conversation by its ID.

        Args:
            conversationId (int): The ID of the conversation.

        Returns:
            Optional[dict]: A dictionary containing conversation details or None if not found.
        """
        cursor = self.conn.execute(
            """
            SELECT id, title, deployment_name, created_at, conversation_history, tokens FROM conversations
            WHERE id = ?
        """,
            (conversationId,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "deployment_name": row[2],
                "created_at": row[3],
                "conversation_history": json.loads(row[4]),
                "tokens": row[5],
            }
        else:
            return None

    def deleteConversationById(self, conversationId: int):
        """
        Deletes a conversation from the database by its ID.

        Args:
            conversationId (int): The ID of the conversation to delete.
        """
        with self.conn:
            self.conn.execute(
                """
                DELETE FROM conversations WHERE id = ?
            """,
                (conversationId,),
            )
        logging.info(f"Deleted conversation ID {conversationId} from the database.")
        self.deleteOrphanedFiles()

    def deleteOrphanedFiles(self):
        """
        Deletes files from the files table that are not referenced in any conversation_attachements.
        """
        try:
            with self.conn:
                cursor = self.conn.execute(
                    """
                    DELETE FROM files
                    WHERE id NOT IN (
                        SELECT DISTINCT file_id FROM conversation_attachements
                    )
                """
                )
                deleted_files_count = cursor.rowcount
                logging.info(f"Deleted {deleted_files_count} orphaned files from the database.")
        except sqlite3.Error as e:
            logging.error(f"Failed to delete orphaned files: {e}")

    def updateConversationHistory(self, conversationId: int, conversationHistory: list):
        """
        Updates the conversation history for a specific conversation.

        Args:
            conversationId (int): The ID of the conversation.
            conversationHistory (list): The updated conversation history.
        """
        conversation_json = json.dumps(conversationHistory)
        with self.conn:
            self.conn.execute(
                """
                UPDATE conversations
                SET conversation_history = ?
                WHERE id = ?
            """,
                (conversation_json, conversationId),
            )
        logging.info(f"Updated conversation history for ID {conversationId}.")

    def updateConversationTitle(self, conversationId: int, newTitle: str):
        """
        Updates the title of a specific conversation.

        Args:
            conversationId (int): The ID of the conversation.
            newTitle (str): The new title for the conversation.
        """
        with self.conn:
            self.conn.execute(
                """
                UPDATE conversations
                SET title = ?
                WHERE id = ?
            """,
                (newTitle, conversationId),
            )
        logging.info(f"Updated title for conversation ID {conversationId} to '{newTitle}'.")

    def updateConversationTokens(self, conversationId: int, tokens: int):
        """
        Updates the tokens count for a specific conversation.

        Args:
            conversationId (int): The ID of the conversation.
            tokens (int): The number of tokens to set.
        """
        try:
            with self.conn:
                self.conn.execute(
                    """
                    UPDATE conversations
                    SET tokens = ?
                    WHERE id = ?
                """,
                    (tokens, conversationId),
                )
                logging.info(f"Updated tokens for conversation ID {conversationId} to {tokens}.")
        except sqlite3.Error as e:
            logging.error(f"Failed to update tokens for conversation ID {conversationId}: {e}")

    def getConversationTokens(self, conversationId: int) -> Optional[int]:
        """
        Retrieves the tokens count for a specific conversation.

        Args:
            conversationId (int): The ID of the conversation.

        Returns:
            Optional[int]: The number of tokens, or None if not found.
        """
        cursor = self.conn.execute(
            """
            SELECT tokens FROM conversations WHERE id = ?
        """,
            (conversationId,),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None

    def addFileRecord(self, filePath: str) -> Optional[int]:
        """
        Inserts the given filePath into the files table if it does not already exist.
        Returns the id of the file record.
        """
        try:
            with self.conn:
                # Insert the file path if it does not exist.
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO files (file_path)
                    VALUES (?)
                """,
                    (filePath,),
                )
                # Retrieve the id whether newly inserted or already present.
                cursor = self.conn.execute(
                    """
                    SELECT id FROM files WHERE file_path = ?
                """,
                    (filePath,),
                )
                row = cursor.fetchone()
                if row:
                    return row[0]
                return None
        except Exception as ex:
            logging.error("Error adding file record: %s", ex)
            return None

    def recordConversationAttachment(self, conversationId: int, fileId: int):
        """
        Inserts a relationship entry into the conversation_attachements table.
        """
        try:
            with self.conn:
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO conversation_attachements (conversation_id, file_id)
                    VALUES (?, ?)
                """,
                    (conversationId, fileId),
                )
        except Exception as ex:
            logging.error("Error recording conversation attachment: %s", ex)

    def recordAttachmentsForConversation(self, conversationId: int, filePaths: list):
        """
        Loops through the list of file paths and records each file and its relationship to the conversation.
        """
        for filePath in filePaths:
            fileId = self.addFileRecord(filePath)
            if fileId:
                self.recordConversationAttachment(conversationId, fileId)

    def close(self):
        """
        Closes the database connection.
        """
        self.conn.close()

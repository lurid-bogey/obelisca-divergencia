import unittest
from unittest.mock import patch, MagicMock
import os
from obeliscaDivergencia.chatSession import ChatSession
from obeliscaDivergencia.utils.database import ConversationDatabase


class TestChatSession(unittest.TestCase):
    def setUp(self):
        self.systemPrompt = "You are a helpful assistant."
        self.deploymentConfig = {
            "type": "azure",
            "endpoint": "https://test-endpoint.openai.azure.com/",
            "deploymentName": "test-deployment",
            "apiVersion": "2024-12-01-preview",
        }
        self.db = MagicMock(spec=ConversationDatabase)
        self.chatSession = ChatSession(
            self.systemPrompt,
            self.deploymentConfig,
            conversationId=None,
            db=self.db,
            maxContextTokens=100000,
        )

    def test_initialization(self):
        # Test the initial state of ChatSession
        self.assertEqual(
            self.chatSession.conversationHistory, [{"role": "user", "content": self.systemPrompt}]
        )
        self.assertEqual(self.chatSession.deploymentName, self.deploymentConfig["deploymentName"])
        self.assertEqual(self.chatSession.lastTotalTokens, 0)
        self.assertEqual(self.chatSession.maxFileSize, 5 * 1024 * 1024)
        self.assertEqual(self.chatSession.maxContextTokens, 100000)

    @patch("obeliscaDivergencia.chatSession.Document")
    def test_extractTextFromDocx_valid(self, mock_document):
        # Test extracting text from a valid DOCX file
        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock(text="Paragraph 1"), MagicMock(text="Paragraph 2")]
        mock_document.return_value = mock_doc
        text = self.chatSession.extractTextFromDocx("dummy.docx")
        self.assertEqual(text, "\n".join(["Paragraph 1", "Paragraph 2"]))

    @patch("obeliscaDivergencia.chatSession.Document", side_effect=Exception("Failed to open DOCX"))
    def test_extractTextFromDocx_exception(self, mock_document):
        # Test extracting text from a DOCX file that raises an exception
        text = self.chatSession.extractTextFromDocx("dummy.docx")
        self.assertEqual(text, "")

    @patch("obeliscaDivergencia.chatSession.extract_text", return_value="Extracted PDF text")
    def test_extractTextFromPdf_valid(self, mock_extract_text):
        # Test extracting text from a valid PDF file
        text = self.chatSession.extractTextFromPdf("dummy.pdf")
        self.assertEqual(text, "Extracted PDF text")

    @patch("obeliscaDivergencia.chatSession.extract_text", side_effect=Exception("Failed to open PDF"))
    def test_extractTextFromPdf_exception(self, mock_extract_text):
        # Test extracting text from a PDF file that raises an exception
        text = self.chatSession.extractTextFromPdf("dummy.pdf")
        self.assertEqual(text, "")

    @patch("obeliscaDivergencia.chatSession.os.path.exists", return_value=True)
    @patch("obeliscaDivergencia.chatSession.os.path.isdir", return_value=False)
    @patch("obeliscaDivergencia.chatSession.ChatSession._readSingleFile", return_value="File Content")
    def test_readFilesContent_singleFile(self, mock_read_single_file, mock_isdir, mock_exists):
        # Test reading content from a single file
        content = self.chatSession.readFilesContent("dummy.txt")
        self.assertEqual(content, "File Content")
        mock_read_single_file.assert_called_with("dummy.txt")

    @patch("obeliscaDivergencia.chatSession.os.path.exists", return_value=True)
    @patch("obeliscaDivergencia.chatSession.os.path.isdir", side_effect=[False, False])
    @patch("obeliscaDivergencia.chatSession.ChatSession._readSingleFile", side_effect=["Content1", "Content2"])
    def test_readFilesContent_multipleFiles(self, mock_read_single_file, mock_isdir, mock_exists):
        # Test reading content from multiple files
        content = self.chatSession.readFilesContent("file1.txt,file2.txt")
        self.assertEqual(content, "Content1Content2")
        self.assertEqual(mock_read_single_file.call_count, 2)
        mock_read_single_file.assert_any_call("file1.txt")
        mock_read_single_file.assert_any_call("file2.txt")

    # @patch("obeliscaDivergencia.chatSession.initOpenAiClient")
    # @patch("obeliscaDivergencia.chatSession.os.environ", {})
    @patch.dict('obeliscaDivergencia.config.os.environ', {}, clear=True)
    def test_sendMessage_missing_api_key(self):
        # Ensure ValueError is raised when API key is missing
        with self.assertRaises(ValueError) as context:
            ChatSession(
                self.systemPrompt,
                self.deploymentConfig,
                conversationId=None,
                db=self.db,
                maxContextTokens=100000,
            )
        self.assertIn("API key environment variable is not set.", str(context.exception))

    @patch("obeliscaDivergencia.chatSession.initOpenAiClient")
    @patch("obeliscaDivergencia.chatSession.os.environ", {"AZURE_OPENAI_API_KEY": "test-api-key"})
    def test_sendMessage_api_exception(self, mock_init_openai_client):
        # Mock the OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_init_openai_client.return_value = mock_client

        reply = self.chatSession.sendMessage("Hello", [])
        self.assertEqual(reply[:21], "Error during API call")
        self.assertEqual(len(self.chatSession.conversationHistory), 2)  # system prompt and Hello

    @patch("obeliscaDivergencia.chatSession.tiktoken.get_encoding")
    def test_countTokens(self, mock_get_encoding):
        # Mock the tokenizer
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = [
            [0, 1, 2],  # system prompt
            [3, 4],     # user message
        ]
        mock_get_encoding.return_value = mock_encoder

        self.chatSession.conversationHistory.append({"role": "user", "content": "Test message"})
        token_count = self.chatSession.countTokens()
        self.assertEqual(token_count, 8)  # 3 + 2


if __name__ == "__main__":
    unittest.main()

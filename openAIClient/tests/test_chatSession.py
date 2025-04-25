import unittest
from unittest.mock import patch, MagicMock
import os
from openAIClient.chatSession import ChatSession


class TestChatSession(unittest.TestCase):
    def setUp(self):
        self.systemPrompt = "You are a helpful assistant."
        self.deploymentName = "test-deployment"
        self.chatSession = ChatSession(self.systemPrompt, self.deploymentName)

    def test_initialization(self):
        # Test the initial state of ChatSession
        self.assertEqual(self.chatSession.conversationHistory, [{"role": "user", "content": self.systemPrompt}])
        self.assertEqual(self.chatSession.deploymentName, self.deploymentName)
        self.assertEqual(self.chatSession.lastTotalTokens, 0)
        self.assertEqual(self.chatSession.maxFileSize, 5 * 1024 * 1024)
        self.assertEqual(self.chatSession.maxContextTokens, 100000)

    def test_extractTextFromDocx_valid(self):
        # Test extracting text from a valid DOCX file
        with patch('openAIClient.chatSession.Document') as MockDocument:
            mock_doc = MagicMock()
            mock_doc.paragraphs = [MagicMock(text="Paragraph 1"), MagicMock(text="Paragraph 2")]
            MockDocument.return_value = mock_doc
            text = self.chatSession.extractTextFromDocx("dummy.docx")
            self.assertEqual(text, "Paragraph 1\nParagraph 2")

    def test_extractTextFromDocx_exception(self):
        # Test extracting text from a DOCX file that raises an exception
        with patch('openAIClient.chatSession.Document', side_effect=Exception("Failed to open DOCX")):
            text = self.chatSession.extractTextFromDocx("dummy.docx")
            self.assertEqual(text, "")

    def test_extractTextFromPdf_valid(self):
        # Test extracting text from a valid PDF file
        with patch('openAIClient.chatSession.extract_text', return_value="Extracted PDF text"):
            text = self.chatSession.extractTextFromPdf("dummy.pdf")
            self.assertEqual(text, "Extracted PDF text")

    def test_extractTextFromPdf_exception(self):
        # Test extracting text from a PDF file that raises an exception
        with patch('openAIClient.chatSession.extract_text', side_effect=Exception("Failed to open PDF")):
            text = self.chatSession.extractTextFromPdf("dummy.pdf")
            self.assertEqual(text, "")

    def test_readFilesContent_singleFile(self):
        # Test reading content from a single file
        with patch('openAIClient.chatSession.os.path.exists', return_value=True), \
             patch('openAIClient.chatSession.os.path.isdir', return_value=False), \
             patch('openAIClient.chatSession.ChatSession._readSingleFile', return_value="File Content"):
            content = self.chatSession.readFilesContent("dummy.txt")
            self.assertEqual(content, "File Content")

    def test_readFilesContent_multipleFiles(self):
        # Test reading content from multiple files
        with patch('openAIClient.chatSession.os.path.exists', return_value=True), \
             patch('openAIClient.chatSession.os.path.isdir', side_effect=[False, False]), \
             patch('openAIClient.chatSession.ChatSession._readSingleFile', side_effect=["Content1", "Content2"]):
            content = self.chatSession.readFilesContent("file1.txt,file2.txt")
            self.assertEqual(content, "Content1Content2")

    @patch('openAIClient.chatSession.openai.chat.completions.create')
    def test_sendMessage_success(self, mock_create):
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Assistant reply"))]
        mock_response.usage = MagicMock(total_tokens=150)
        mock_create.return_value = mock_response

        reply = self.chatSession.sendMessage("Hello", [])
        self.assertEqual(reply, "Assistant reply")
        self.assertEqual(self.chatSession.lastTotalTokens, 150)
        self.assertEqual(len(self.chatSession.conversationHistory), 3)  # system message + user message + reply
        self.assertEqual(self.chatSession.conversationHistory[-1]["content"], "Assistant reply")

    @patch.dict(os.environ, {
        "AZURE_OPENAI_API_KEY": "test-api-key",
        "OPENAI_API_VERSION": "2024-12-01-preview"
    })
    @patch('openAIClient.chatSession.openai.chat.completions.create', side_effect=Exception("API Error"))
    def test_sendMessage_api_exception(self, mock_create):
        # Test sending message when OpenAI API raises an exception
        reply = self.chatSession.sendMessage("Hello", [])
        self.assertEqual(reply, "Error during API call: API Error")
        self.assertEqual(len(self.chatSession.conversationHistory), 2)  # Only system prompt and Hello

    def test_countTokens(self):
        # Test token counting
        self.chatSession.conversationHistory.append({"role": "user", "content": "Test message"})
        with patch('openAIClient.chatSession.tiktoken.get_encoding') as mock_encoding:
            mock_encoder = MagicMock()
            mock_encoder.encode.return_value = [0] * 3  # Assume 3 tokens
            mock_encoding.return_value = mock_encoder
            token_count = self.chatSession.countTokens()
            self.assertEqual(token_count, 8)

    def test_trimConversationHistory(self):
        # Test trimming conversation history
        self.chatSession.maxContextTokens = 10
        self.chatSession.conversationHistory = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Assistant reply"},
            {"role": "user", "content": "Second message"}
        ]
        with patch('openAIClient.chatSession.ChatSession.countTokens', return_value=20):
            self.chatSession.trimConversationHistory()
            self.assertEqual(len(self.chatSession.conversationHistory), 2)  # Should remove oldest user message


if __name__ == '__main__':
    unittest.main()

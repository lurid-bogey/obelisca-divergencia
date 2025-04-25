import unittest
from unittest.mock import patch, mock_open
import os
from openAIClient.config import initOpenAiClient
import configparser
import openai


class TestConfig(unittest.TestCase):
    @patch('openAIClient.config.configparser.ConfigParser.has_section')
    @patch('openAIClient.config.configparser.ConfigParser.read')
    @patch('openAIClient.config.configparser.ConfigParser.get')
    @patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test-api-key"})
    def test_initOpenAI_success(self, mock_get, mock_read, mock_has_section):
        # Mock the has_section method to return True for '[OpenAI]'
        mock_has_section.return_value = True

        # Mock configuration values
        mock_get.side_effect = [
            "https://test-endpoint.openai.azure.com/",
            "test-deployment",
            "2024-12-01-preview"
        ]

        # Initialize OpenAI
        initOpenAiClient()

        # Assert OpenAI configurations
        self.assertEqual(openai.api_type, "azure")
        self.assertEqual(openai.api_base, "https://test-endpoint.openai.azure.com/")
        self.assertEqual(openai.api_version, "2024-12-01-preview")
        self.assertEqual(openai.api_key, "test-api-key")

    @patch('openAIClient.config.configparser.ConfigParser.read')
    def test_initOpenAI_missing_section(self, mock_read):
        # Mock absence of [OpenAI] section
        mock_config = configparser.ConfigParser()
        mock_config.has_section = lambda section: False
        with patch('openAIClient.config.configparser.ConfigParser', return_value=mock_config):
            with self.assertRaises(ValueError) as context:
                initOpenAiClient()
            self.assertIn("Missing [OpenAI] section in settings.ini", str(context.exception))

    @patch('openAIClient.config.configparser.ConfigParser.has_section')
    @patch('openAIClient.config.configparser.ConfigParser.read')
    @patch('openAIClient.config.configparser.ConfigParser.get')
    def test_initOpenAI_missing_values(self, mock_get, mock_read, mock_has_section):
        # Mock the has_section method to return True for '[OpenAI]'
        mock_has_section.return_value = True

        # Mock missing azureEndpoint
        mock_get.side_effect = [
            "",  # azureEndpoint
            "test-deployment",
            "2024-12-01-preview"
        ]
        mock_config = configparser.ConfigParser()
        with patch('openAIClient.config.configparser.ConfigParser', return_value=mock_config):
            with self.assertRaises(ValueError) as context:
                initOpenAiClient()
            self.assertIn("azureEndpoint is not set", str(context.exception))

    @patch('openAIClient.config.configparser.ConfigParser.has_section')
    @patch('openAIClient.config.configparser.ConfigParser.read')
    @patch.dict(os.environ, {}, clear=True)
    @patch('openAIClient.config.configparser.ConfigParser.get')
    def test_initOpenAI_missing_api_key(self, mock_get, mock_read, mock_has_section):
        # Mock the has_section method to return True for '[OpenAI]'
        mock_has_section.return_value = True

        # Mock configuration values
        mock_get.side_effect = [
            "https://test-endpoint.openai.azure.com/",
            "test-deployment",
            "2024-12-01-preview"
        ]
        mock_config = configparser.ConfigParser()
        with patch('openAIClient.config.configparser.ConfigParser', return_value=mock_config):
            with self.assertRaises(ValueError) as context:
                initOpenAiClient()
            self.assertIn("AZURE_OPENAI_API_KEY environment variable is not set.", str(context.exception))


if __name__ == '__main__':
    unittest.main()

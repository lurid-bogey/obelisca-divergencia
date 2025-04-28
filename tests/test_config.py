import unittest
from unittest.mock import patch, MagicMock
import os
from obeliscaDivergencia.config import initOpenAiClient
import configparser
import openai


class TestConfig(unittest.TestCase):
    @patch("obeliscaDivergencia.config.openai.AzureOpenAI")
    @patch("obeliscaDivergencia.config.openai.OpenAI")
    @patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test-api-key"})
    def test_initOpenAI_azure_success(self, mock_openai_class, mock_azure_openai_class):
        # Mock the AzureOpenAI client
        mock_client = MagicMock()
        mock_azure_openai_class.return_value = mock_client

        deploymentConfig = {
            "type": "azure",
            "endpoint": "https://test-endpoint.openai.azure.com/",
            "deploymentName": "test-deployment",
            "apiVersion": "2024-12-01-preview",
        }

        client = initOpenAiClient(deploymentConfig)

        # Assert AzureOpenAI configurations
        mock_azure_openai_class.assert_called_once_with(api_version="2024-12-01-preview", azure_endpoint="https://test-endpoint.openai.azure.com/")
        self.assertEqual(client.api_type, "azure")
        self.assertEqual(client.api_key, "test-api-key")
        # self.assertEqual(client.api_base, "https://test-endpoint.openai.azure.com/")

    @patch("obeliscaDivergencia.config.openai.OpenAI")
    @patch("obeliscaDivergencia.config.openai.AzureOpenAI")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"})
    def test_initOpenAI_openai_success(self, mock_azure_openai_class, mock_openai_class):
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        deploymentConfig = {
            "type": "openai",
            "endpoint": "https://api.openai.com/v1",
            "deploymentName": "gpt-3.5-turbo",
            "apiVersion": "",  # Not required for openai
        }

        client = initOpenAiClient(deploymentConfig)

        # Assert OpenAI configurations
        mock_openai_class.assert_called_once()
        self.assertEqual(client.api_type, "openai")
        self.assertEqual(client.api_key, "test-openai-key")
        self.assertEqual(client.api_base, "https://api.openai.com/v1")

    def test_initOpenAI_missing_api_key(self):
        # Ensure ValueError is raised when API key is missing
        deploymentConfig = {
            "type": "azure",
            "endpoint": "https://test-endpoint.openai.azure.com/",
            "deploymentName": "test-deployment",
            "apiVersion": "2024-12-01-preview",
        }
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                initOpenAiClient(deploymentConfig)
            self.assertIn("API key environment variable is not set.", str(context.exception))

    def test_initOpenAI_missing_azure_config(self):
        # Test missing required Azure configuration
        deploymentConfig = {
            "type": "azure",
            "endpoint": "",
            "deploymentName": "test-deployment",
            "apiVersion": "2024-12-01-preview",
        }
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test-api-key"}):
            with self.assertRaises(ValueError) as context:
                initOpenAiClient(deploymentConfig)
            self.assertIn("Missing required Azure OpenAI configuration.", str(context.exception))

    def test_initOpenAI_missing_openai_deploymentName(self):
        # Test missing deploymentName for OpenAI configuration
        deploymentConfig = {
            "type": "openai",
            "endpoint": "https://api.openai.com/v1",
            "deploymentName": "",
            "apiVersion": "",
        }
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"}):
            with self.assertRaises(ValueError) as context:
                initOpenAiClient(deploymentConfig)
            self.assertIn("deploymentName is not set for OpenAI configuration.", str(context.exception))

    def test_initOpenAI_unknown_deployment_type(self):
        # Test unknown deployment type
        deploymentConfig = {
            "type": "unknown",
            "endpoint": "https://unknown-endpoint.com/api",
            "deploymentName": "unknown-deployment",
            "apiVersion": "2024-12-01-preview",
        }
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test-api-key"}):
            with self.assertRaises(ValueError) as context:
                initOpenAiClient(deploymentConfig)
            self.assertIn("Unknown deployment type: unknown", str(context.exception))


if __name__ == "__main__":
    unittest.main()

import os
import sys
import logging
import openai
from typing import List, Dict


def resourcePath(relativePath: str, forcedPath: bool = False) -> str:
    """
    Get absolute path to resource, works for development and for PyInstaller.

    Args:
        relativePath (str): The relative path to the resource.
        forcedPath (bool): If True, forces the baseDir to the current file's directory.

    Returns:
        str: The absolute path to the resource.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller creates a temp folder and stores path in sys._MEIPASS
        baseDir = os.path.dirname(sys.executable)
    else:
        baseDir = os.path.dirname(os.path.abspath(__file__))

    if forcedPath:
        baseDir = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(baseDir, relativePath)


def initOpenAiClient(deploymentConfig: Dict[str, str]) -> [openai.OpenAI | openai.AzureOpenAI]:
    """
    Initializes the OpenAI client based on a specific deployment configuration.

    Args:
        deploymentConfig (Dict[str, str]): The deployment configuration dictionary.

    Raises:
        ValueError: If any required settings are missing.
    """
    logging.info(f"Initializing OpenAI with deployment: {deploymentConfig['deploymentName']}")

    deployment_type = deploymentConfig["type"].lower()
    endpoint = deploymentConfig["endpoint"]
    deployment_name = deploymentConfig["deploymentName"]
    api_version = deploymentConfig["apiVersion"]

    api_key = os.environ.get("AZURE_OPENAI_API_KEY") if deployment_type == "azure" else os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key environment variable is not set.")

    if deployment_type == "azure":
        if not endpoint or not deployment_name or not api_version:
            raise ValueError("Missing required Azure OpenAI configuration.")
        client = openai.AzureOpenAI(api_version=api_version, azure_endpoint=endpoint)
        client.api_type = "azure"
        # client.api_base = endpoint
        # client.api_version = api_version
        client.api_key = api_key
        logging.info("Azure OpenAI client configured.")
    elif deployment_type == "openai":
        if not endpoint or not deployment_name:
            raise ValueError("deploymentName is not set for OpenAI configuration.")
        client = openai.OpenAI()
        client.api_type = "openai"
        client.api_base = endpoint
        client.api_key = api_key
        logging.info("Standard OpenAI client configured.")
    else:
        raise ValueError(f"Unknown deployment type: {deployment_type}")

    return client


def getDatabasePath() -> str:
    """
    Returns the path to the SQLite database file.

    Returns:
        str: The SQLite database file path.
    """
    baseDir = os.path.dirname(resourcePath(""))
    return os.path.join(baseDir, "conversations.db")

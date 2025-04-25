import os
from pathlib import Path


def normalizeFilePath(filePath: str) -> str:
    """
    Normalizes the file path to a standard format.
    """
    return os.path.normpath(filePath)


def isBinaryFile(filePath: str, binaryExtensions: tuple) -> bool:
    """
    Checks if the file has a binary extension.
    """
    ext = os.path.splitext(filePath)[1].lower()
    return ext in binaryExtensions


def getRelativePath(filePath: str, baseDir: str) -> str:
    """
    Returns the relative path of filePath with respect to baseDir.
    """
    return os.path.relpath(filePath, baseDir)

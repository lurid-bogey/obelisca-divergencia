import unittest
import os
from openAIClient.utils.fileUtils import normalizeFilePath, isBinaryFile, getRelativePath


class TestFileUtils(unittest.TestCase):
    def test_normalizeFilePath(self):
        # Test normalization of file paths
        path = "C:\\Users\\User\\..\\Documents\\file.txt"
        normalized = normalizeFilePath(path)
        self.assertEqual(normalized, "C:\\Users\\Documents\\file.txt")

    def test_isBinaryFile_true(self):
        # Test binary file detection
        binaryExtensions = (".png", ".exe")
        self.assertTrue(isBinaryFile("image.png", binaryExtensions))
        self.assertTrue(isBinaryFile("installer.EXE", binaryExtensions))

    def test_isBinaryFile_false(self):
        # Test non-binary file detection
        binaryExtensions = (".png", ".exe")
        self.assertFalse(isBinaryFile("document.txt", binaryExtensions))
        self.assertFalse(isBinaryFile("script.py", binaryExtensions))

    def test_getRelativePath(self):
        # Test relative path calculation
        filePath = "/home/user/projects/openAIClient/openAIClient/chatSession.py"
        baseDir = "/home/user/projects/openAIClient"
        relative = getRelativePath(filePath, baseDir)

        # Normalize both paths
        normalized_expected = os.path.normpath("openAIClient/chatSession.py")
        normalized_actual = os.path.normpath(relative)

        self.assertEqual(normalized_actual, normalized_expected)


if __name__ == "__main__":
    unittest.main()

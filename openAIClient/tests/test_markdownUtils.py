import unittest
from openAIClient.utils.markdownUtils import convertMarkdownToHtml


class TestMarkdownUtils(unittest.TestCase):
    def test_convertMarkdownToHtml_basic(self):
        # Test basic markdown conversion
        markdown_text = "# Heading\n\nThis is a paragraph."
        html = convertMarkdownToHtml(markdown_text)
        self.assertIn("<h1>Heading</h1>", html)
        self.assertIn("<p>This is a paragraph.</p>", html)

    def test_convertMarkdownToHtml_codeBlock(self):
        # Test markdown code block conversion with syntax highlighting
        markdown_text = "```python\nprint('Hello, World!')\n```"
        html = convertMarkdownToHtml(markdown_text)
        # self.assertIn("<code class=\"language-python\">", html)
        self.assertIn(".codehilite", html)
        self.assertIn('class="codehilite"', html)

    def test_convertMarkdownToHtml_empty(self):
        # Test empty markdown conversion
        markdown_text = ""
        html = convertMarkdownToHtml(markdown_text)

        # Check for the presence of the <style> tag
        self.assertIn("<style>", html)
        self.assertIn("</style>", html)

        # Check for essential CSS rules
        self.assertIn("word-wrap: break-word;", html)
        self.assertIn("white-space: pre-wrap;", html)
        self.assertIn(".codehilite {", html)
        self.assertIn("font-family: 'Consolas', monospace;", html)
        self.assertIn("background-color: #f0f0f0;", html)

        # # Optionally, ensure there's no additional HTML content
        # # This can be done by stripping the style block and checking the remainder
        # stripped_html = html.replace("<style>", "").replace("</style>", "").strip()
        # self.assertEqual(stripped_html, "")


if __name__ == "__main__":
    unittest.main()

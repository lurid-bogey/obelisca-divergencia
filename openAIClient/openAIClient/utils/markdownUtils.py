import markdown
from pygments.formatters import HtmlFormatter

# Generate styles once.
pygmentsCss = HtmlFormatter().get_style_defs('.codehilite')
additionalCss = """
    .codehilite {
        font-family: 'Consolas', monospace;
        background-color: #f0f0f0;
    }
"""
style = f"""
<style>
    body {{
        word-wrap: break-word;
        white-space: pre-wrap;
    }}
    {pygmentsCss}
    {additionalCss}
</style>
"""

# Create a global Markdown instance so that the extensions are loaded only once.
mdConverter = markdown.Markdown(
    extensions=['fenced_code', 'codehilite'],
    extension_configs={
        'codehilite': {
            'linenums': False,
            'guess_lang': False,
            'pygments_style': 'monokai',
            'noclasses': False,
        }
    }
)


def convertMarkdownToHtml(text: str) -> str:
    """
    Convert markdown text to HTML with enhanced CSS for code highlighting,
    using Consolas as the font for code blocks.
    """
    # Clear any previous state (if needed) before converting new text,
    # so that the converter works correctly on subsequent invocations.
    mdConverter.reset()
    htmlContent = mdConverter.convert(text)
    return f"{style}{htmlContent}"

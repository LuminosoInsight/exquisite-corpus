import json
import mistune
from ftfy.fixes import unescape_html


class TextRenderer(mistune.Renderer):
    """Renders Markdown to plain text."""

    def block_code(self, code, lang=None):
        return ''

    def block_quote(self, text):
        return text + ' '

    def block_html(self, html):
        # fixme
        return html

    def header(self, text, level, raw=None):
        return text + ' '

    def hrule(self):
        return ''

    def list(self, body, ordered=True):
        return body

    def list_item(self, text):
        return text + ' '

    def paragraph(self, text):
        return text + ' '

    def table(self, header, body):
        return body

    def table_row(self, content):
        return content

    def table_cell(self, content, **flags):
        return content + ' '

    def double_emphasis(self, text):
        return text

    def emphasis(self, text):
        return text

    def codespan(self, text):
        return text

    def linebreak(self):
        return ' '

    def strikethrough(self, text):
        return ''

    def text(self, text):
        return text

    def escape(self, text):
        return text

    def autolink(self, link, is_email=False):
        return ''

    def link(self, link, title, text):
        return text

    def image(self, src, title, text):
        return text

    def inline_html(self, html):
        return html

    def newline(self):
        """Rendering newline element."""
        return ''

    def footnote_ref(self, key, index):
        return ''

    def footnote_item(self, key, text):
        return ''

    def footnotes(self, text):
        return ''


def process_reddit_stream(stream):
    mdparser = mistune.Markdown(renderer=TextRenderer())
    for line in stream:
        data = json.loads(line)
        if data['score'] >= 1 and data['body'] != '[deleted]':
            md = data['body']
            text = mdparser(md)
            plain_text = unescape_html(text).replace('\n', ' ').strip('> ')
            if plain_text:
                print(plain_text)


if __name__ == '__main__':
    import sys
    process_reddit_stream(sys.stdin)
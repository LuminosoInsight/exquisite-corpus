import json
import regex
import mistune
import mmh3

from ftfy.fixes import fix_surrogates, unescape_html
from .language_detection import detect_language
from .reddit_ban_data import BANNED_SUBREDDITS

TWITTER_HANDLE_RE = regex.compile(r"@[\S--\p{punct}]+")
TCO_RE = regex.compile("http(?:s)?://t.co/[a-zA-Z0-9]+")
URL_RE = regex.compile(r"http(?:s)?://[^) ]*")


class TextRenderer(mistune.Renderer):
    """
    A custom Mistune renderer that renders Markdown to plain text (instead
    of HTML).
    """

    def block_code(self, code, lang=None):
        return ""

    def block_quote(self, text):
        return text + " "

    def block_html(self, html):
        # fixme
        return html

    def header(self, text, level, raw=None):
        return text + " "

    def hrule(self):
        return ""

    def list(self, body, ordered=True):
        return body

    def list_item(self, text):
        return text + " "

    def paragraph(self, text):
        return text + " "

    def table(self, header, body):
        return body

    def table_row(self, content):
        return content

    def table_cell(self, content, **flags):
        return content + " "

    def double_emphasis(self, text):
        return text

    def emphasis(self, text):
        return text

    def codespan(self, text):
        return text

    def linebreak(self):
        return " "

    def strikethrough(self, text):
        return ""

    def text(self, text):
        return text

    def escape(self, text):
        return text

    def autolink(self, link, is_email=False):
        return ""

    def link(self, link, title, text):
        return text

    def image(self, src, title, text):
        return text

    def inline_html(self, html):
        return html

    def newline(self):
        """Rendering newline element."""
        return ""

    def footnote_ref(self, key, index):
        return ""

    def footnote_item(self, key, text):
        return ""

    def footnotes(self, text):
        return ""


def preprocess_reddit(infile, outfile):
    """
    Read Reddit text from a JSON-lines file, parse the Markdown, and tag
    what language each post is in.
    """
    mdparser = mistune.Markdown(renderer=TextRenderer())
    for line in infile:
        data = json.loads(line)
        if data["score"] >= 1 and data["body"] != "[deleted]":
            subreddit = data["subreddit"]
            subreddit_hash = mmh3.hash(subreddit)
            if subreddit_hash not in BANNED_SUBREDDITS:
                md = fix_surrogates(unescape_html(data["body"]))
                text = mdparser(md).replace("\n", " ").replace("\u200b", "")
                text = URL_RE.sub("", text)
                if text:
                    lang, confident = detect_language(text)
                    if confident:
                        # There are more English posts than we need, so filter them
                        # for score >= 2
                        if lang != "en" or data["score"] > 1:
                            print(f"{lang}\t{text}", file=outfile)


def preprocess_twitter(infile, outfile):
    for line in infile:
        if "\t" in line:
            line = line.split("\t", 1)[1]
        text = line.rstrip()
        text = TWITTER_HANDLE_RE.sub("", text)
        text = TCO_RE.sub("", text)
        text = fix_surrogates(unescape_html(text)).replace("\n", " ")
        lang, confident = detect_language(text)
        if confident:
            print(f"{lang}\t{text}", file=outfile)

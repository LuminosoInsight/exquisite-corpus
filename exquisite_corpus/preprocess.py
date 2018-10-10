import json
import regex
import misaka
import mmh3

from ftfy.fixes import fix_surrogates, unescape_html
from .language_detection import detect_language
from .reddit_ban_data import BANNED_SUBREDDITS

TWITTER_HANDLE_RE = regex.compile(r"@[\S--\p{punct}]+")
TCO_RE = regex.compile("http(?:s)?://t.co/[a-zA-Z0-9]+")
URL_RE = regex.compile(r"http(?:s)?://[^) ]*")


class TextRenderer(misaka.BaseRenderer):
    """
    Render Markdown as plain text, skipping complex things such as tables and code.
    """
    def blockcode(self, text, language):
        return ''

    def blockquote(self, content):
        return content

    def header(self, content, level):
        return content

    def hrule(self):
        return ''

    def list(self, content, is_ordered, is_block):
        return content

    def listitem(self, content, is_ordered, is_block):
        return content

    def paragraph(self, text):
        return text

    def table(self, content):
        return ''

    def table_header(self, content):
        return ''

    def table_body(self, content):
        return ''

    def table_row(self, content):
        return ''

    def table_cell(self, text, align, is_header):
        return ''

    def footnotes(self, text):
        return text

    def footnote_def(self, text, number):
        return text

    def footnote_ref(self, number):
        return ''

    def blockhtml(self, text):
        return text

    def autolink(self, link, is_email):
        return ''

    def codespan(self, text):
        return text

    def double_emphasis(self, text):
        return text

    def emphasis(self, text):
        return text

    def underline(self, text):
        return text

    def highlight(self, text):
        return text

    def quote(self, text):
        return text

    def image(self, link, title, alt):
        return title

    def linebreak(self):
        return '\n'

    def link(self, content, link, title):
        return title

    def strikethrough(self, text):
        return text

    def superscript(self, text):
        return text

    def raw_html(self, text):
        return text

    def triple_emphasis(self, text):
        return text

    def math(self, text, displaymode):
        return text

    def superscript(self, text):
        return text

    def normal_text(self, text):
        return text


def preprocess_reddit(infile, outfile):
    """
    Read Reddit text from a JSON-lines file, parse the Markdown, and tag
    what language each post is in.
    """
    renderer = TextRenderer()
    mdparser = misaka.Markdown(renderer, extensions=['superscript'])
    for line in infile:
        data = json.loads(line)
        if (
            'score' in data and 'body' in data and
            data["score"] is not None and data["score"] >= 1 and
            data["body"] != "[deleted]"
        ):
            subreddit = data["subreddit"]
            subreddit_hash = mmh3.hash(subreddit)
            if subreddit_hash not in BANNED_SUBREDDITS:
                md = fix_surrogates(unescape_html(data["body"]))
                try:
                    text = mdparser(md)
                except RecursionError:
                    continue
                text = text.replace("\n", " ").replace("\u200b", "")
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

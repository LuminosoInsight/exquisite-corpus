import json
import regex
import mmh3

from ftfy.fixes import fix_surrogates, unescape_html, fix_line_breaks
from lumi_language_id import detect_language
from .reddit_ban_data import BANNED_SUBREDDITS


# This regex matches Twitter handles starting with @
TWITTER_HANDLE_RE = regex.compile(r"@[\S--\p{punct}]+")

# This regex matches Twitter URLs, which are always shortened with t.co
TCO_RE = regex.compile(r"http(?:s)?://t\.co/[a-zA-Z0-9]+")

# This regex matches all HTTP URLs, as strings without spaces that follow "http://" or
# "https://"
URL_RE = regex.compile(r"http(?:s)?://[^ ]*")

# This regex matches URLs in the Markdown [link title](url) syntax, which is how links
# usually appear on Reddit. It extracts the link title as \1\2 (where \2 contains
# any ambiguous right bracket characters).
MARKDOWN_URL_RE = regex.compile(r'''
    \[              # a literal left bracket, starting the link title
      (             # Capture the link title in group 1
        [^\]]+      # The title is made of anything but close brackets
      )
    \]              # A literal right bracket, ending the link title
    (               # Group 2 cleans up an edge case:
        \]*         # any extra right brackets that fell out due to people putting brackets in brackets
    )
    \(              # a literal left parenthesis, starting the link target
      (             # Capture the link target in group 3
        [^)]+       # Link targets are everything until the next close parenthesis
      )
    \)
''', regex.VERBOSE)

# This regex matches Markdown formatting such as _italic_, **bold**, or
# ~strikethrough~, and extracts the text inside it as \2.
MARKDOWN_FORMAT_RES = [
    regex.compile(rf"""
        (?<!\w)         # Look behind to make sure we don't start in the middle of a word
        ([{char}]+)     # The emphasis character we're handling, possibly repeated
        (
          [^{char}]+    # The content of the formatting, which doesn't contain that character
        )
        \1              # The same characters we started with, to end the formatting
        (?!\w)          # Look forward to make sure we don't end in the middle of a word
    """, regex.VERBOSE)
    for char in '*_~'
]


def strip_markdown(text):
    """
    Remove most Markdown formatting from text.

    Using a Markdown parser would spend a lot of cycles and end up producing HTML,
    not plain text, leaving us with a new problem. Instead, we approximate Markdown
    parsing with a combination of regular expressions and special rules for the
    starts of lines.
    """
    text = MARKDOWN_URL_RE.sub(r'\1\2', text)
    text = URL_RE.sub('', text)
    for format_re in MARKDOWN_FORMAT_RES:
        text = format_re.sub(r'\2', text)
    lines = [line.lstrip(">#*- ") for line in text.split('\n')]
    return ' '.join(lines)


def preprocess_reddit(infile, outfile):
    """
    Read Reddit text from a JSON-lines file, parse the Markdown, and tag
    what language each post is in.

    Filter the posts to enforce _some_ standard of quality:

    - Posts in English should have score >= 2 (they should have net upvotes)
    - Other posts should have score >= 1 (no net downvotes)
    - Posts from subreddits that are banned in 2018 are skipped
    """
    for line in infile:
        data = json.loads(line)
        if (
            'score' in data and 'body' in data and
            data["score"] is not None and data["score"] >= 2 and
            data["body"] != "[deleted]"
        ):
            subreddit = data["subreddit"].casefold()
            subreddit_hash = mmh3.hash(subreddit)
            if subreddit_hash not in BANNED_SUBREDDITS:
                md = fix_surrogates(unescape_html(fix_line_breaks(data["body"])))
                text = strip_markdown(md)
                text = text.replace("\n", " ").replace("\u200b", "")
                text = URL_RE.sub("", text)
                if text:
                    lang, _confidence = detect_language(text)
                    if lang != 'und':
                        # There are more English posts than we need, so filter them
                        # for score >= 3
                        if lang != "en" or data["score"] > 2:
                            print(f"{lang}\t{text}", file=outfile)


def preprocess_twitter(infile, outfile):
    """
    Read Twitter text from the format we collected it in, and produce language-tagged
    lines.

    In this format, each line might come with some metadata, such as the tweet ID,
    which appears before the text, separated from the text by a tab character. Or it
    might not contain any such data. We weren't very consistent about it over the years.

    This function reads just the text (the part after the tab, if there is a tab). It
    removes URLs and Twitter handles from the text. It then language-detects the
    text, and if it is confident about the language, it outputs a new tab-separated
    file containing the language code and the processed text.

    This format could be read again by the same function, because the language code
    is now the metadata, but we have no reason to actually do this.
    """
    for line in infile:
        if "\t" in line:
            line = line.split("\t", 1)[1]
        text = line.rstrip()
        text = TWITTER_HANDLE_RE.sub("", text)
        text = TCO_RE.sub("", text)
        text = fix_surrogates(unescape_html(text)).replace("\n", " ")
        lang, _confidence = detect_language(text)
        if lang != 'und':
            print(f"{lang}\t{text}", file=outfile)


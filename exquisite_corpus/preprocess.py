import json
import regex
import mmh3

from ftfy.fixes import fix_surrogates, unescape_html, fix_line_breaks
from .language_detection import detect_language
from .reddit_ban_data import BANNED_SUBREDDITS

TWITTER_HANDLE_RE = regex.compile(r"@[\S--\p{punct}]+")
TCO_RE = regex.compile("http(?:s)?://t.co/[a-zA-Z0-9]+")
URL_RE = regex.compile(r"http(?:s)?://[^ ]*")


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
            data["score"] is not None and data["score"] >= 1 and
            data["body"] != "[deleted]"
        ):
            subreddit = data["subreddit"]
            subreddit_hash = mmh3.hash(subreddit)
            if subreddit_hash not in BANNED_SUBREDDITS:
                md = fix_surrogates(unescape_html(fix_line_breaks(data["body"])))
                text = strip_markdown(md)
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

from wordfreq import tokenize
from ftfy.fixes import unescape_html
import regex
import pycld2
import langcodes

CLD2_BAD_CHAR_RANGE = "[%s]" % "".join(
    [
        '\x00-\x08',
        '\x0b',
        '\x0e-\x1f',
        '\x7f-\x9f',
        '\ud800-\udfff',
        '\ufdd0-\ufdef',
        '\N{HANGUL FILLER}',
        '\N{HANGUL CHOSEONG FILLER}',
        '\N{HANGUL JUNGSEONG FILLER}',
        '<>'
    ] +
    [chr(65534+65536*x+y) for x in range(17) for y in range(2)]
)
CLD2_BAD_CHARS_RE = regex.compile(CLD2_BAD_CHAR_RANGE)

TWITTER_HANDLE_RE = regex.compile(r'@[\S--\p{punct}]+')
TCO_RE = regex.compile('http(?:s)?://t.co/[a-zA-Z0-9]+')
URL_RE = regex.compile(r'http(?:s)?://[^) ]*')
MARKDOWN_URL_RESIDUE_RE = regex.compile(r'\]\(\)')


# Low-frequency languages tend to be detected incorrectly by cld2. The
# following list of languages are languages that appear in our data with any
# reasonable frequency.
#
# This list is larger than the list that wordfreq ultimately generates, so we
# can look here as a source of future data.


CLD2_LANGUAGE_MAP = {
    'tl': 'fil',
    'jw': 'jv',
    'iw': 'he',
    'no': 'nb',
    'hr': 'sh',
    'sr': 'sh',
    'bs': 'sh'
}

CLD2_LANGUAGES = sorted(set([
    CLD2_LANGUAGE_MAP.get(_lang, _lang)
    for _name, _lang in pycld2.LANGUAGES
    if not _lang.startswith('xx')
]))

# Problems to watch out for:
#
#   - Thai (seems to be detected whenever someone uses Thai characters in
#     an emoticon)
#   - Welsh (which is detected for "ohmygodohmygodohmygod")
#   - Turkmen (detected for ASCII art)
#   - Irish Gaelic (detected for Cthulhu-related text)
#   - Kannada (looks of disapproval)
#   - Lao, Tamil, Xhosa, Slovak (various emoticons and Internet memes)
#   - Breton (the word "memes" itself)


def tokenize_file(infile, outfile, language, check_language=False):
    """
    Take in a file of plain text, tokenize it as the given language, and write
    the result as lines of space-separated tokens.
    """
    for line in infile:
        line = unescape_html(line.rstrip())
        tokens = tokenize(line, language, include_punctuation=True, external_wordlist=True)
        checked_lang = None
        if check_language:
            checked_lang, _confident = cld2_detect_language(line.rstrip())
        if (not check_language) or langcodes.tag_match_score(checked_lang, language) >= 90:
            print(' '.join(tokens), file=outfile)


def cld2_detect_language(text):
    """
    Uses CLD2 to detect the language.
    """
    # Format of pycld2.detect:
    #   (Confident in result: bool,
    #   Number of bytes of text: Int,
    #   Triples of detected languages in order of certainty:
    #       (Language name: str,
    #       Language code: str
    #       Percent of text in this language: float
    #       Confidence score: float))

    text = CLD2_BAD_CHARS_RE.sub('', text)
    det_result = pycld2.detect(text)
    confident = det_result[0]
    lang = pycld2.detect(text)[2][0][1]

    # Normalize the language code: 'iw' becomes 'he', and 'zh-Hant'
    # becomes 'zh'
    code = CLD2_LANGUAGE_MAP.get(lang, lang)
    return code, confident


def tokenize_by_language(in_file, out_dir, mode='twitter'):
    """
    Uses CLD2 to detect the language and wordfreq tokenizer to create tokens.

    The `mode` can be 'twitter' or 'reddit', which slightly changes the
    pre-processing of the text.
    """
    out_files = {
        language: open('%s/%s.txt' % (out_dir, language), 'w', encoding='utf-8')
        for language in CLD2_LANGUAGES
    }
    try:
        for line in in_file:
            text = unescape_html(line.rstrip())
            if mode == 'twitter':
                text = TWITTER_HANDLE_RE.sub('', text)
                text = TCO_RE.sub('', text)
            elif mode == 'reddit':
                text = URL_RE.sub('', text)
                text = MARKDOWN_URL_RESIDUE_RE.sub(']', text)

            lang, confident = cld2_detect_language(text)
            if lang in CLD2_LANGUAGES:
                # Keep the line if 2 out of 3 of the following are true:
                #
                # - CLD2 is confident about the language it detected
                # - The language detected was English
                # - There are at least 50 bytes of input


                score = int(confident)
                score += (len(text.encode('utf-8')) >= 50)
                score += (lang == 'en')

                if score >= 2:
                    tokenized = tokenize(text, lang, include_punctuation=True, external_wordlist=True)
                    out_file = out_files[lang]
                    print(' '.join(tokenized), file=out_file)
    finally:
        for out_file in out_files.values():
            out_file.close()


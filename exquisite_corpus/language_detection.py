import pycld2
import regex


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
    [chr(65534 + 65536 * x + y) for x in range(17) for y in range(2)]
)

CLD2_BAD_CHARS_RE = regex.compile(CLD2_BAD_CHAR_RANGE)
CYRILLIC_RE = regex.compile(r'[А-Яа-я]')


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


CLD2_LANGUAGES = sorted(set([
    CLD2_LANGUAGE_MAP.get(_lang, _lang)
    for _name, _lang in pycld2.LANGUAGES
    if not _lang.startswith('xx')
]))


def detect_language(text):
    """
    Uses CLD2 to detect the language of text.

    Returns the BCP 47 language code, and a boolean indicating whether the
    result is confident.

    We modify CLD2's confidence value to say it's not confident if:

    - The detected language is a non-language placeholder like 'xx'
    - The detected language appears to be incorrect because it contains
      particular characters from a different script
    - The text is shorter than 50 bytes
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
    # becomes 'zh', for example
    code = CLD2_LANGUAGE_MAP.get(lang, lang)

    if len(text.encode('utf-8')) < 50:
        confident = False
    elif code not in CLD2_LANGUAGES:
        confident = False
    elif code == 'sh':
        # Fix cases of Arabic being detected as Bosnian
        if 'ا' in text:
            code = 'ar'
            confident = False
        # Fix cases of Russian being detected as Serbian
        if CYRILLIC_RE.search(text):
            confident = False

    return code, confident

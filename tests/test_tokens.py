import pytest
from io import StringIO

from exquisite_corpus.tokens import tokenize_file


def run_tokenize(func, test_obj, kwargs):
    input_file = [test_obj]
    output_file = StringIO()
    func(input_file, output_file, **kwargs)
    output_file.seek(0)
    result = output_file.read()
    return result


@pytest.mark.parametrize(
    'text, expected, kwargs',
    [
        pytest.param(
            'This is a sample, &lt;h1&gt; text in English\n\n',
            'this is a sample h1 text in english\n',
            {'ftfy': False, 'language': 'en'},
            id='Tokenize text with simple ftfy fixes'
        ),
        pytest.param(
            'This is a sample text with a mojibake dash â€”',
            'this is a sample text with a mojibake dash\n',
            {'ftfy': True, 'language': 'en'},
            id='Tokenize text will all ftfy fixes'
        ),
        pytest.param(
            'This is text with, some. punctuation;',
            'this is text with , some . punctuation ;\n',
            {'punctuation': True, 'language': 'en'},
            id='Keep punctuation with punctuation kwarg set to True'
        ),
        pytest.param(
            'A text which language is checked',
            '',
            {'language': 'cs', 'check_language': True},
            id='Ignore if a declared language is incorrect'
        ),
        pytest.param(
            'A text which language is checked',
            'a text which language is checked\n',
            {'language': 'eng', 'check_language': True},
            id='Output if a declared language is correct'
        ),
    ],
)
def test_tokenize_file(text, expected, kwargs):
    assert run_tokenize(tokenize_file, text, kwargs) == expected

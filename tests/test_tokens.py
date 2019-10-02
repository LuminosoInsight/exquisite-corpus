import pytest
from io import StringIO
from unittest.mock import mock_open, patch, call

from exquisite_corpus.tokens import tokenize_file, tokenize_by_language


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
            id='Tokenize text with all ftfy fixes'
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


@pytest.mark.parametrize(
    'in_file, expected, kwargs',
    [
        pytest.param(
            ['en\tsample text'],
            'sample text',
            {'languages': ['en']},
            id='Write text to a file for that language'
        ),
        pytest.param(
            ['pl\tsample text'],
            '',
            {'languages' : ['en']},
            id='Ignore if the language of a text is not in a desired language'
        )
    ]
)
def test_tokenize_by_language(in_file, expected, kwargs):
    m = mock_open()
    with patch('builtins.open', m):
        tokenize_by_language(in_file=in_file, out_dir='.', **kwargs)
        lang = kwargs['languages'][0]
        if expected:
            calls = [call(f'./{lang}.txt', 'w', encoding='utf-8'),
                 call().write(expected),
                 call().write('\n'),
                 call().close()]
        else:
            calls = [call(f'./{lang}.txt', 'w', encoding='utf-8'),
                     call().close()]
        m.assert_has_calls(calls) # TODO Uninformative error

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
    'text, kwargs, expected',
    [
        pytest.param(
            'This is a sample text in English',
            {'language': 'en'},
            'this is a sample text in english\n',
            id='Basic case'
        )
    ],
)
def test_tokenize_file(text, kwargs, expected):
    assert run_tokenize(tokenize_file, text, kwargs) == expected

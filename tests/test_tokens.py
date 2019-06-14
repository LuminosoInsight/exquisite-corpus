from io import StringIO

from exquisite_corpus.tokens import tokenize_file


def run_tokenize(func, test_obj):
    input_file = [test_obj]
    output_file = StringIO()
    func(input_file, output_file)
    output_file.seek(0)
    result = output_file.read()
    return result


def test_basic_tokenize_file():
    text = 'This is a sample text in English'

    


import os
import subprocess
from io import StringIO

import pytest
import sentencepiece

from exquisite_corpus.parallel_corpus import (
    cleanup_parallel_file, decode_pieces_with_sp, encode_with_sp_as_pieces,
    get_vocabulary_from_sp, train_sentencepiece
)

THIS_DIR = os.path.dirname(__file__)

DECODED = [
    'abcdefghijklmnopqrstuvwxyz',
    'this is a sample text'
]
ENCODED = [
    '▁ a b c d e f g h i j k l m n o p q r s t u v w x y z',
    '▁ t h i s ▁ i s ▁ a ▁ s a m p l e ▁ t e x t'
]


@pytest.fixture(scope="session")
def path_to_ft_model():
    # Download FastText model only if needed
    fasttext_model_dir = os.path.join(THIS_DIR, 'ft_model')
    fasttext_model_path = os.path.join(fasttext_model_dir, 'lid.176.bin')
    if not os.path.isfile(fasttext_model_path):
        if not os.path.exists(fasttext_model_dir):
            os.makedirs(fasttext_model_dir)
        subprocess.call(
            [
                'curl', '-Lf',
                'https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin',
                '-o', fasttext_model_path
            ]
        )
    return fasttext_model_path


@pytest.mark.parametrize(
    'text, expected, lang1, lang2',
    [
        pytest.param(
            'This is a sample text with a mojibake dash â€”\t'
            'Este es un texto de muestra con un guión mojibake â€”',
            'This is a sample text with a mojibake dash —\t'
            'Este es un texto de muestra con un guión mojibake —',
            'en', 'es'
        ),
        pytest.param(
            '♪ I am happy with these notes by my sides. ♪\t'
            '♪ Estoy feliz con estas notas a mi lado. ♪',
            '♪ I am happy with these notes by my sides. ♪\t'
            '♪ Estoy feliz con estas notas a mi lado. ♪',
            'en', 'es'
        ),
        pytest.param(
            '♪ Sadly, I will be missing a note on the other side. ♪\t'
            '♪ Lamentablemente, seré la misión una nota en el otro lado.',
            '',
            'en', 'es'
        ),
        pytest.param(
            'Short text.\tTexto corto.',
            'Short text.\tTexto corto.',
            'en', 'es'
        ),
        pytest.param(
            'This is a sample text with correct language on both sides.\t'
            'Este es un texto de muestra con el lenguaje correcto en ambos lados.',
            'This is a sample text with correct language on both sides.\t'
            'Este es un texto de muestra con el lenguaje correcto en ambos lados.',
            'en', 'es'
        ),
        pytest.param(
            'This is a sample text with wrong language on one side.\t'
            'これは、一方の言語が間違っているサンプルテキストです。',
            '',
            'en', 'es'
        ),
        pytest.param(
            'This is a sample text with length ratio exceeding 2.0.\t'
            'Texto corto.',
            '',
            'en', 'es'
        ),
        pytest.param(
            'This is a sample \t text with additional tab.\t'
            'Este es un texto de muestra con pestaña adicional.',
            '',
            'en', 'es'
        ),

    ]
)
def test_cleanup_parallel_file(text, expected, lang1, lang2, path_to_ft_model):
    in_file = [text]
    out_file = StringIO()

    cleanup_parallel_file(
        in_file, out_file, path_to_ft_model, lang1, lang2
    )
    out_file.seek(0)
    assert out_file.read() == expected


@pytest.fixture(scope="session")
def path_to_sp_model(tmpdir_factory):
    input_dir = tmpdir_factory.mktemp('input')
    input_file = input_dir.join('test_input.txt')
    input_file.write(
        'abcdefghijklmnopqrstuvwxyz\n'
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ\n'
    )

    model_dir = tmpdir_factory.mktemp('model')
    model_prefix = str(model_dir.join('m'))

    lang = 'en'
    train_sentencepiece(input_file, model_prefix, lang)
    return model_prefix + '.model'


def test_train_sentencepiece(path_to_sp_model):
    sp = sentencepiece.SentencePieceProcessor()

    # Check if the model exists and we can load it
    assert os.path.exists(path_to_sp_model)
    assert sp.Load(path_to_sp_model)


def test_get_vocabulary_from_sp(path_to_sp_model):
    out_file = StringIO()
    get_vocabulary_from_sp(out_file, path_to_sp_model)

    # Check if we get correct number of vocabulary
    # Should be 26 lower case alphabets + '▁'
    out_file.seek(0)
    count = len(out_file.readlines())
    assert count == 27


def test_encode_with_sp_as_pieces(path_to_sp_model):
    for text, expected in zip(DECODED, ENCODED):
        in_file = [text]
        out_file = StringIO()
        encode_with_sp_as_pieces(in_file, out_file, path_to_sp_model)
        out_file.seek(0)
        assert out_file.read().replace('\n', '') == expected


def test_decode_pieces_with_sp(path_to_sp_model):
    for text, expected in zip(ENCODED, DECODED):
        in_file = [text]
        out_file = StringIO()
        decode_pieces_with_sp(in_file, out_file, path_to_sp_model)
        out_file.seek(0)
        assert out_file.read().replace('\n', '') == expected

import os
import subprocess
from io import StringIO

import pytest
import sentencepiece
import fasttext

from exquisite_corpus.parallel_corpus import (
    clean_text_for_ft, cleanup_parallel_file, decode_pieces_with_sp,
    encode_with_sp_as_pieces, get_ft_lang_code_prob, get_vocabulary_from_sp,
    train_sentencepiece
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


def test_clean_text_for_ft():
    """
    Test if the text is cleaned as expected.
    """
    # Check if '\n' is removed
    text = 'This is a sample text with new line character.\n'
    text = clean_text_for_ft(text)
    assert '\n' not in text

    # Check if all the characters are lower case
    text = 'This is a sample text with Upper Case.'
    text = clean_text_for_ft(text)
    assert text.islower()

    # Check if punctuations and digits are removed
    text = 'This is 1 and only 1 text with punctuations and digits!!'
    text = clean_text_for_ft(text)
    assert '1' not in text and '!' not in text


def test_get_ft_lang_code_prob(path_to_ft_model):
    """
    Test if the language code and the corresponding probability of texts are as
    expected.
    """
    # Load the FastText's language identification model
    fasttext_model = fasttext.load_model(path_to_ft_model)

    # Check if an expected exception is raised for a non-string
    with pytest.raises(AssertionError):
        text = []
        _, _ = get_ft_lang_code_prob(text, fasttext_model)

    # FT's predict() exptects one line at a time. Test if '\n' is removed before
    # the prediction
    try:
        text = 'This test is in English.\n It contains newline character.'
        _, _ = get_ft_lang_code_prob(text, fasttext_model)
    except ValueError as err:
        pytest.fail(repr(err))

    # This should be identified with low probability
    text = ''
    _, lang_pred_prob = get_ft_lang_code_prob(text, fasttext_model)
    assert lang_pred_prob < 0.15


@pytest.mark.parametrize(
    'text, expected, lang1, lang2',
    [
        pytest.param(
            'This is a sample text with a mojibake dash â€”\t'
            'Este es un texto de muestra con un guión mojibake â€”',
            'This is a sample text with a mojibake dash —\t'
            'Este es un texto de muestra con un guión mojibake —\n',
            'en', 'es'
        ),
        pytest.param(
            'This is a sample text with\nnew line\t'
            'Este es un texto de muestra con una nueva línea.',
            'This is a sample text with new line\t'
            'Este es un texto de muestra con una nueva línea.\n',
            'en', 'es'
        ),
        pytest.param(
            '♪ I am happy with these notes by my sides. ♪\t'
            '♪ Estoy feliz con estas notas a mi lado. ♪',
            '♪ I am happy with these notes by my sides. ♪\t'
            '♪ Estoy feliz con estas notas a mi lado. ♪\n',
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
            'Short text.\tTexto corto.\n',
            'en', 'es'
        ),
        pytest.param(
            'This is a sample text with correct language on both sides.\t'
            'Este es un texto de muestra con el lenguaje correcto en ambos lados.',
            'This is a sample text with correct language on both sides.\t'
            'Este es un texto de muestra con el lenguaje correcto en ambos lados.\n',
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
            'This is a sample text with only one side.',
            '',
            'en', 'es'
        ),
        pytest.param(
            '\tThis is a sample text with only one side.',
            '',
            'es', 'en'
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

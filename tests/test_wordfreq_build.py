import pytest
from shutil import rmtree

from tests.testing_utils import (
    gzipped_result_dir_same_as_reference,
    result_dir_same_as_reference,
    run_snakemake,
)

RESULT_EXTRACTED = 'tests/data/extracted'
RESULT_TOKENIZED = 'tests/data/tokenized'
RESULT_MESSY_COUNTS = 'tests/data/messy-counts'
RESULT_COUNTS = 'tests/data/counts'
RESULT_FREQS = 'tests/data/freqs'
RESULT_WORDFREQ = 'tests/data/wordfreq'
REFERENCE_WORDFREQ = 'tests/reference/wordfreq'
REFERENCE_TOKENIZED = 'tests/reference/tokenized'
REFERENCE_EXTRACTED = 'tests/reference/extracted'
REFERENCE_FREQS = 'tests/reference/freqs'
REFERENCE_COUNTS = 'tests/reference/counts'
REFERENCE_MESSY_COUNTS = 'tests/reference/messy-counts'


@pytest.fixture(scope='session')
def run_build(test_env_variables, setup_input_files):
    run_snakemake(test_env_variables)
    yield
    rmtree(RESULT_EXTRACTED)
    rmtree(RESULT_TOKENIZED)
    rmtree(RESULT_COUNTS)
    rmtree(RESULT_MESSY_COUNTS)
    rmtree(RESULT_FREQS)
    rmtree(RESULT_WORDFREQ)


@pytest.mark.parametrize(
    'result, reference',
    [
        (RESULT_EXTRACTED, REFERENCE_EXTRACTED),
        (RESULT_TOKENIZED, REFERENCE_TOKENIZED),
        (RESULT_MESSY_COUNTS, REFERENCE_MESSY_COUNTS),
        (RESULT_COUNTS, REFERENCE_COUNTS),
        (RESULT_FREQS, REFERENCE_FREQS),
        (RESULT_WORDFREQ, REFERENCE_WORDFREQ),
    ],
)
def test_text_result_same_as_reference(run_build, result, reference):
    assert result_dir_same_as_reference(result, reference)


@pytest.mark.parametrize(
    'result, reference',
    [
        (RESULT_EXTRACTED, REFERENCE_EXTRACTED),
        (RESULT_TOKENIZED, REFERENCE_TOKENIZED),
        (RESULT_WORDFREQ, REFERENCE_WORDFREQ),
    ],
)
def test_gzipped_result_same_as_reference(run_build, result, reference):
    assert gzipped_result_dir_same_as_reference(result, reference)

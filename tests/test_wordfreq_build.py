import pytest
from shutil import rmtree

from tests.testing_utils import (
    gzipped_result_dir_same_as_reference,
    result_dir_same_as_reference,
    run_snakemake,
)


@pytest.fixture(scope='session')
def run_build(test_env_variables, setup_input_files):
    run_snakemake(test_env_variables)
    yield
    rmtree('tests/data/extracted')
    rmtree('tests/data/tokenized')
    rmtree('tests/data/counts')
    rmtree('tests/data/messy-counts')
    rmtree('tests/data/freqs')
    rmtree('tests/data/wordfreq')


@pytest.mark.parametrize(
    'result, reference',
    [
        ('tests/data/extracted', 'tests/reference/extracted'),
        ('tests/data/tokenized', 'tests/reference/tokenized'),
        ('tests/data/messy-counts', 'tests/reference/messy-counts'),
        ('tests/data/counts', 'tests/reference/counts'),
        ('tests/data/freqs', 'tests/reference/freqs'),
        ('tests/data/wordfreq', 'tests/reference/wordfreq'),
    ],
)
def test_text_result_same_as_reference(run_build, result, reference):
    assert result_dir_same_as_reference(result, reference)


@pytest.mark.parametrize(
    'result, reference',
    [
        ('tests/data/extracted', 'tests/reference/extracted'),
        ('tests/data/tokenized', 'tests/reference/tokenized'),
        ('tests/data/wordfreq', 'tests/reference/wordfreq'),
    ],
)
def test_gzipped_result_same_as_reference(run_build, result, reference):
    assert gzipped_result_dir_same_as_reference(result, reference)

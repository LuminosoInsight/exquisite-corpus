import pytest
import shutil

from tests.testing_utils import (
    gzipped_result_dir_same_as_reference,
    result_dir_same_as_reference,
    run_snakemake,
)


@pytest.fixture(scope='session')
def run_build(test_env_variables):
    run_snakemake(test_env_variables)
    yield
    shutil.rmtree('tests/data/extracted')
    shutil.rmtree('tests/data/tokenized')
    shutil.rmtree('tests/data/counts')
    shutil.rmtree('tests/data/messy-counts')
    shutil.rmtree('tests/data/freqs')
    shutil.rmtree('tests/data/wordfreq')


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

import pytest
from shutil import rmtree

from tests.testing_utils import (
    gzipped_result_dir_same_as_reference,
    result_dir_same_as_reference,
    run_snakemake,
)

directories = ['extracted', 'tokenized', 'wordfreq', 'messy-counts', 'counts', 'freqs']


@pytest.fixture(scope='session')
def run_build(test_env_variables, setup_input_files):
    run_snakemake(test_env_variables)
    yield
    for directory in directories:
        rmtree('tests/data/' + directory)


@pytest.mark.parametrize(
    'result, reference',
    [('tests/data/' + directory, 'tests/reference/' + directory)
     for directory in directories]
)
def test_text_result_same_as_reference(run_build, result, reference):
    assert result_dir_same_as_reference(result, reference)


@pytest.mark.parametrize(
    'result, reference',
    [
        ('tests/data' + directory, 'tests/reference' + directory)
        for directory in directories[:3]
    ]
)
def test_gzipped_result_same_as_reference(run_build, result, reference):
    assert gzipped_result_dir_same_as_reference(result, reference)

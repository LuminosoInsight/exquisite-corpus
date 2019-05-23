import pytest
import subprocess
import os
import shutil
from tests.testing_utils import directories_the_same, directories_with_gzipped_files_the_same


@pytest.fixture(scope='session')
def check_gzipped_files(run_build):
    print('checked')
    # check if all required gzipped files have been created.


# @pytest.fixture(scope='session')
# def unzip_gzipped_files():
#     print('unzipped')
    # unzip all of the gzipped files. Might be a mistake.

@pytest.fixture(scope='session')
def env_variables():
    env_variables = os.environ.copy()
    env_variables['TEST_BUILD_DATA'] = "tests/data"
    return env_variables


# @pytest.fixture(scope='session')
# def temp_data_directories(tmpdir_factory):
#     pass


@pytest.fixture(scope='session')
def run_build(env_variables):
    options = ['-j', '4']
    cmd_args = ["snakemake"] + options
    subprocess.call(cmd_args, env=env_variables)
    yield
    # teardown: remove directories
    shutil.rmtree('tests/data/extracted')
    shutil.rmtree('tests/data/tokenized')
    shutil.rmtree('tests/data/counts')
    shutil.rmtree('tests/data/messy-counts')
    shutil.rmtree('tests/data/freqs')
    shutil.rmtree('tests/data/wordfreq')


def test_extracted(run_build):
    assert directories_the_same('tests/data/extracted',
                                'tests/reference/extracted')

    assert directories_with_gzipped_files_the_same('tests/data/extracted',
                                                   'tests/reference/extracted')


def test_tokenized(run_build):
    assert directories_the_same('tests/data/tokenized',
                                'tests/reference/tokenized')
    assert directories_with_gzipped_files_the_same('tests/data/tokenized',
                                                   'tests/reference/tokenized')


def test_counts(run_build):
    assert  directories_the_same('tests/data/counts', 'tests/reference/counts')


def test_freqs(run_build):
    assert directories_the_same('tests/data/freqs', 'tests/reference/freqs')


def test_messy_counts(run_build):
    assert directories_the_same('tests/data/messy-counts',
                                'tests/reference/messy-counts')


def test_wordfreq(run_build):
    assert directories_the_same('tests/data/wordfreq',
                                'tests/reference/wordfreq')

    assert directories_with_gzipped_files_the_same('tests/data/wordfreq',
                                                   'tests/reference/wordfreq')

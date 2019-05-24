import os

import pytest
import shutil
import subprocess

from tests.testing_utils import directories_the_same, \
    directories_with_gzipped_files_the_same


@pytest.fixture(scope='session')
def env_variables():
    env_variables = os.environ.copy()
    env_variables['TEST_BUILD_DATA'] = 'tests/data'
    return env_variables


@pytest.fixture(scope='session')
def run_build(env_variables):
    options = ['-j', '4']
    cmd_args = ["snakemake"] + options
    subprocess.call(cmd_args, env=env_variables)
    yield
    shutil.rmtree('tests/data/extracted')
    shutil.rmtree('tests/data/tokenized')
    shutil.rmtree('tests/data/counts')
    shutil.rmtree('tests/data/messy-counts')
    shutil.rmtree('tests/data/freqs')
    shutil.rmtree('tests/data/wordfreq')


@pytest.mark.parametrize('output, reference',
                         [('tests/data/extracted', 'tests/reference/extracted'),
                          ('tests/data/tokenized', 'tests/reference/tokenized'),
                          ('tests/data/messy-counts',
                           'tests/reference/messy-counts'),
                          ('tests/data/counts', 'tests/reference/counts'),
                          ('tests/data/freqs', 'tests/reference/freqs'),
                          ('tests/data/wordfreq', 'tests/reference/wordfreq')
                          ])
def test_text_output_consistent_with_reference(run_build, output, reference):
    assert directories_the_same(output, reference)


@pytest.mark.parametrize('output, reference',
                         [
                             ('tests/data/extracted',
                              'tests/reference/extracted'),
                             ('tests/data/tokenized',
                              'tests/reference/tokenized'),
                             ('tests/data/wordfreq',
                              'tests/reference/wordfreq')
                         ])
def test_gzipped_output_consistent_with_reference(run_build, output,
                                                  reference):
    assert directories_with_gzipped_files_the_same(output, reference)

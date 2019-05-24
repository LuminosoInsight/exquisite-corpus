import os

import pytest


@pytest.fixture(scope='session')
def test_env_variables():
    env_variables = os.environ.copy()
    env_variables['TEST_BUILD_DATA'] = 'tests/data'
    return env_variables

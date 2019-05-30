import os

import pytest


@pytest.fixture(scope='session')
def test_env_variables():
    env_variables = os.environ.copy()
    env_variables['XC_BUILD_TEST'] = '1'
    return env_variables

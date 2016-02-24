import pytest
import os
from . import syncere


def find_tests():
    for entry in os.scandir('.'):
        if entry.is_dir() and entry.name != '__pycache__':
            yield entry


@pytest.mark.parametrize('entry', find_tests())
def test(entry):
    os.chdir(entry.name)
    assert syncere.Syncere('test.profile')
    os.chdir('..')

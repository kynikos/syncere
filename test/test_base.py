import pytest
import subprocess
import shlex

from . import syncere

# TODO: find . -printf "%i\t%k\t%M\t%n\t%u\t%g\t%s\t%A+\t%C+\t%T+\t//\t%P\t//->\t%l\t//\n"


def run_test(args):
    return subprocess.run(shlex.split('python -m syncere ' + args))


def test_help():
    assert run_test('--help').returncode == 0


def test_version():
    assert run_test('--version').returncode == 0

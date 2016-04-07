import pytest

from .syncere import Syncere, exceptions

# TODO: find . -printf "%i\t%k\t%M\t%n\t%u\t%g\t%s\t%A+\t%C+\t%T+\t//\t%P\t//->\t%l\t//\n"


def test_help():
    with pytest.raises(SystemExit) as excinfo:
        Syncere('--help')
    assert excinfo.value.code == 0


def test_version():
    with pytest.raises(SystemExit) as excinfo:
        Syncere('--version')
    assert excinfo.value.code == 0


@pytest.mark.parametrize('arg', ('--daemon', '--config', '-M', '--dparam',
                                 '--remote-option', '--no-detach'))
def test_unsupported(arg):
    with pytest.raises(exceptions.UnsupportedOptionError):
        Syncere('source destination -av {} --delete'.format(arg))

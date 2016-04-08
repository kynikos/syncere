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


@pytest.mark.parametrize('arg,dest', (('--daemon', 'daemon'),
                                      ('--config', 'config'),
                                      ('-M', 'remote_option'),
                                      ('--dparam', 'remote_option'),
                                      ('--remote-option', 'remote_option'),
                                      ('--no-detach', 'no_detach')))
def test_unsupported(arg, dest):
    with pytest.raises(exceptions.UnsupportedOptionError) as excinfo:
        Syncere('source destination -av {} --delete'.format(arg))
    assert excinfo.value.args[0] == dest


@pytest.mark.parametrize('arg,dest', (('-l', 'links'),
                                      ('--links', 'links'),
                                      ('--no-l', 'no_links'),
                                      ('--no-links', 'no_links'),
                                      ('-L', 'copy_links'),
                                      ('--copy-links', 'copy_links'),
                                      ('--copy-unsafe-links',
                                       'copy_unsafe_links'),
                                      ('--safe-links', 'safe_links'),
                                      ('--munge-links', 'munge_links'),
                                      ('-k', 'copy_dirlinks'),
                                      ('--copy-dirlinks', 'copy_dirlinks'),
                                      ('-K', 'keep_dirlinks'),
                                      ('--keep-dirlinks', 'keep_dirlinks'),
                                      ('-H', 'hard_links'),
                                      ('--hard-links', 'hard_links'),
                                      ('-a', 'archive'),
                                      ('--archive', 'archive'),
                                      ('--timeout=1', 'timeout'),
                                      ('--contimeout=1', 'contimeout'),
                                      ('-s', 'protect_args'),
                                      ('--protect-args', 'protect_args'),
                                      ('--no-s', 'no_protect_args'),
                                      ('--no-protect-args', 'no_protect_args'),
                                      ('--outbuf=1', 'outbuf'),
                                      ('-8', '_8_bit_output'),
                                      ('--8-bit-output', '_8_bit_output'),
                                      ('--log-file=1', 'log_file'),
                                      ('--log-file-format=1',
                                       'log_file_format'),
                                      ('--list-only', 'list_only'),
                                      ('-0', 'from0'),
                                      ('--from0', 'from0')))
def test_experimental_disabled(arg, dest):
    with pytest.raises(exceptions.ExperimentalOptionWarning) as excinfo:
        Syncere('source destination {}'.format(arg))
    assert excinfo.value.args[0] == dest

import pytest
import subprocess

from .syncere import Syncere, exceptions
from .conftest import Utils

# TODO: find . -printf "%i\t%k\t%M\t%n\t%u\t%g\t%s\t%A+\t%C+\t%T+\t//\t%P\t//->\t%l\t//\n"


class TestHelp(Utils):
    def test_help(self):
        with pytest.raises(SystemExit) as excinfo:
            Syncere('--help')
        assert excinfo.value.code == 0

    def test_version(self):
        with pytest.raises(SystemExit) as excinfo:
            Syncere('--version')
        assert excinfo.value.code == 0


class TestCliArgsErrors(Utils):
    @pytest.mark.parametrize('arg,dest', (('--daemon', 'daemon'),
                                          ('--config', 'config'),
                                          ('-M', 'remote_option'),
                                          ('--dparam', 'remote_option'),
                                          ('--remote-option', 'remote_option'),
                                          ('--no-detach', 'no_detach')))
    def test_unsupported(self, arg, dest):
        with pytest.raises(exceptions.UnsupportedOptionError) as excinfo:
            Syncere('./source/ ./destination/ -av {} --delete'.format(arg))
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
                                          ('--no-protect-args',
                                           'no_protect_args'),
                                          ('--outbuf=1', 'outbuf'),
                                          ('-8', '_8_bit_output'),
                                          ('--8-bit-output', '_8_bit_output'),
                                          ('--log-file=1', 'log_file'),
                                          ('--log-file-format=1',
                                           'log_file_format'),
                                          ('--list-only', 'list_only'),
                                          ('-0', 'from0'),
                                          ('--from0', 'from0')))
    def test_experimental_disabled(self, arg, dest):
        with pytest.raises(exceptions.ExperimentalOptionWarning) as excinfo:
            Syncere('./source/ ./destination/ {}'.format(arg))
        assert excinfo.value.args[0] == dest

    def test_missing_destination(self):
        with pytest.raises(exceptions.MissingDestinationError):
            Syncere('./source/')


class TestPreviewErrors(Utils):
    def test_non_existing_folders(self):
        with pytest.raises(exceptions.RsyncError) as excinfo:
            Syncere('./source/ ./destination/')
        retcode = excinfo.value.args[0]
        assert isinstance(retcode, int) and retcode > 0


class TestTransfers(Utils):
    def test_null_transfer(self):
        self.populate("""
        mkdir source
        mkdir destination
        """)
        with pytest.raises(SystemExit) as excinfo:
            Syncere('./source/ ./destination/')
        assert excinfo.value.code == 0

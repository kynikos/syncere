import pytest

from .syncere import Syncere, exceptions
from .conftest import Utils


class TestHelp(Utils):
    """
    Test the options that exit the application before anything else can be
    done.
    """
    def test_help(self):
        with pytest.raises(SystemExit) as excinfo:
            Syncere('--help')
        assert excinfo.value.code == 0
        # TODO #1: Test that preview hasn't been started

    def test_version(self):
        with pytest.raises(SystemExit) as excinfo:
            Syncere('--version')
        assert excinfo.value.code == 0
        # TODO #1: Test that preview hasn't been started


class TestCliArgsErrors(Utils):
    """
    Test the errors in the command line itself that lead to the program
    exiting before anything can be done.
    """
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


@pytest.mark.usefixtures('testdir')
class TestPreviewErrors(Utils):
    """
    Test the errors that can happen at the preview stage, leading the
    application to exit *before* the interactive interface is brought up.
    """
    def test_non_existing_folders(self):
        with pytest.raises(exceptions.RsyncError) as excinfo:
            Syncere('./source/ ./destination/')
        retcode = excinfo.value.args[0]
        assert isinstance(retcode, int) and retcode > 0
        # TODO #1: Test that the interface hasn't been started


@pytest.mark.usefixtures('testdir')
class TestTransferExecution(Utils):
    """
    Test that syncere does complete the rsync transfer command.

    Note: this must *not* be used to test the results of the rsync command
    itself, i.e. do not waste time and resources trying to test what the rsync
    developers already do upstream!
    """
    def test_null_transfer(self):
        self.populate("""
        mkdir source
        mkdir destination
        """)
        with pytest.raises(SystemExit) as excinfo:
            Syncere('./source/ ./destination/')
        assert excinfo.value.code == 0
        # TODO #1: Test that the application has exited at the correct stage

    def test_default_transfer(self):
        self.populate("""
        mkdir source
        mkdir destination
        cd source
        echo "foo" > foo.txt
        """)
        # TODO [#2]: Don't use an experimental option here
        Syncere('./source/ ./destination/ -avv --experimental',
                test=['>*', 'S'])
        # TODO #1: Test that the application has exited at the correct stage


@pytest.mark.usefixtures('testdir')
class TestInterface(Utils):
    """
    Test that the interactive interface actually works (in all the other tests
    the commands are entered automatically).
    """
    def test_basic_transfer(self):
        self.populate("""
        mkdir source
        mkdir destination
        cd source
        echo "foo" > foo.txt
        """)
        # TODO [#2]: Don't use an experimental option here
        Syncere('./source/ ./destination/ -avv --experimental')
        # TODO #1: Test that the application has exited at the correct stage

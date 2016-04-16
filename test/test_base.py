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
                                          ('--list-only', 'list_only'),
                                          ('--dparam', 'remote_option'),
                                          ('--remote-option', 'remote_option'),
                                          ('--no-detach', 'no_detach')))
    def test_unsupported(self, arg, dest):
        with pytest.raises(exceptions.UnsupportedOptionError) as excinfo:
            Syncere('./source/ ./destination/ -av {} --delete'.format(arg))
        assert excinfo.value.args[0] == dest

    @pytest.mark.parametrize('arg,dest', (('--timeout=1', 'timeout'),
                                          ('--contimeout=1', 'contimeout'),
                                          ('--outbuf=1', 'outbuf'),
                                          ('-8', '_8_bit_output'),
                                          ('--8-bit-output', '_8_bit_output'),
                                          ('--log-file=1', 'log_file'),
                                          ('--log-file-format=1',
                                           'log_file_format'),
                                          ('-0', 'from0'),
                                          ('--from0', 'from0')))
    def test_experimental_disabled(self, arg, dest):
        with pytest.raises(exceptions.ExperimentalOptionWarning) as excinfo:
            Syncere('./source/ ./destination/ -av {} --delete'.format(arg))
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
        command mkdir source
        command mkdir destination
        """)
        with pytest.raises(SystemExit) as excinfo:
            Syncere('./source/ ./destination/')
        assert excinfo.value.code == 0
        # TODO #1: Test that the application has exited at the correct stage

    def test_default_transfer(self):
        self.populate("""
        command mkdir source
        command mkdir destination
        command cd source
        command echo "foo" > foo.txt
        """)
        Syncere('./source/ ./destination/ -a', test=['>*', 'S'])
        # TODO #1: Test that the application has exited at the correct stage


# TODO #45
@pytest.mark.usefixtures('testdir')
class TestRsyncOptions(Utils):
    """
    Test specific rsync options whose effect on syncere is not so obvious.
    """
    def test_hard_links(self):
        """
        This test proves that excluding one of a series of hard links breaks
        them (known rsync behavior).
        """
        self.populate("""
        command mkdir source
        command mkdir destination
        command cd source
        command echo "foo" > foo.txt
        command ln foo.txt bar.txt
        """)
        self.verify("""
        command cd source
        [ foo.txt -ef bar.txt ]
        """)
        Syncere('./source/ ./destination/ -a', test=['>*', 'S'])
        self.verify("""
        command cd destination
        ! [ foo.txt -ef bar.txt ]
        """)
        Syncere('./source/ ./destination/ -aH', test=['>*', 'S'])
        self.verify("""
        command cd destination
        [ foo.txt -ef bar.txt ]
        """)
        self.populate("""
        command cd source
        command echo "bar" >> foo.txt
        """)
        self.verify("""
        command cd source
        [ foo.txt -ef bar.txt ]
        """)
        Syncere('./source/ ./destination/ -aH', test=['>*', 'S'])
        self.verify("""
        command cd destination
        [ foo.txt -ef bar.txt ]
        """)
        self.populate("""
        command cd source
        command echo "baz" >> foo.txt
        """)
        self.verify("""
        command cd source
        [ foo.txt -ef bar.txt ]
        """)
        Syncere('./source/ ./destination/ -aH', test=['>1', '!2', 'S'])
        self.verify("""
        command cd destination
        ! [ foo.txt -ef bar.txt ]
        """)


@pytest.mark.usefixtures('testdir')
class TestInterface(Utils):
    """
    Test that the interactive interface actually works (in all the other tests
    the commands are entered automatically).
    """
    def test_basic_transfer(self):
        self.populate("""
        command mkdir source
        command mkdir destination
        command cd source
        command echo "foo" > foo.txt
        """)
        Syncere('./source/ ./destination/ -a')
        # TODO #1: Test that the application has exited at the correct stage

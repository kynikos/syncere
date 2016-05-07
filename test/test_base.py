import pytest

from .syncere import Syncere, exceptions, _m_cmenu
from .conftest import Utils


class TestHelp(Utils):
    """
    Test the options that exit the application before anything else can be
    done.
    """
    def test_help(self):
        with pytest.raises(SystemExit) as excinfo:
            Syncere('--help', test=True)
        assert excinfo.value.code == 0
        # TODO #1: Test that preview hasn't been started

    def test_version(self):
        with pytest.raises(SystemExit) as excinfo:
            Syncere('--version', test=True)
        assert excinfo.value.code == 0
        # TODO #1: Test that preview hasn't been started


class TestCliArgsErrors(Utils):
    """
    Test the errors in the command line itself that lead to the program
    exiting before anything can be done.
    """
    @pytest.mark.parametrize('arg,dest', (('--list-only', 'list_only'),
                                          ('--daemon', 'daemon'),
                                          ('--config', 'config'),
                                          ('--dparam', 'dparam'),
                                          ('--no-detach', 'no_detach')))
    def test_unsupported(self, arg, dest):
        with pytest.raises(exceptions.UnsupportedOptionError) as excinfo:
            Syncere('./source/ ./destination/ -av {} --delete'.format(arg),
                    test=True)
        assert excinfo.value.args[0] == dest

    @pytest.mark.parametrize('arg,dest', (('-0', 'from0'),
                                          ('--from0', 'from0'),
                                          ('--outbuf=1', 'outbuf'),
                                          ('-8', '_8_bit_output'),
                                          ('--8-bit-output', '_8_bit_output'),
                                          ('-M=1', 'remote_option'),
                                          ('--remote-option=1',
                                           'remote_option')))
    def test_experimental_disabled(self, arg, dest):
        with pytest.raises(exceptions.ExperimentalOptionWarning) as excinfo:
            Syncere('./source/ ./destination/ -av {} --delete'.format(arg),
                    test=True)
        assert excinfo.value.args[0] == dest

    def test_missing_destination(self):
        with pytest.raises(exceptions.MissingDestinationError):
            Syncere('./source/', test=True)


@pytest.mark.usefixtures('testdir')
class TestPreviewErrors(Utils):
    """
    Test the errors that can happen at the preview stage, leading the
    application to exit *before* the interactive interface is brought up.
    """
    def test_non_existing_folders(self):
        with pytest.raises(SystemExit) as excinfo:
            Syncere('./source/ ./destination/', test=True)
        assert excinfo.value.code > 0
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
        Syncere('./source/ ./destination/', test=True)
        # TODO #1: Test that the application has exited at the correct stage

    def test_default_transfer(self):
        self.populate("""
        command mkdir source
        command mkdir destination
        command cd source
        command echo "foo" > foo.txt
        """)
        Syncere('./source/ ./destination/ -a', test=True,
                commands=['preview', 'include *', 'transfer', 'quit'])
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
        Syncere('./source/ ./destination/ -a', test=True,
                commands=['preview', 'include *', 'transfer', 'quit'])
        self.verify("""
        command cd destination
        ! [ foo.txt -ef bar.txt ]
        """)
        Syncere('./source/ ./destination/ -aH', test=True,
                commands=['preview', 'include *', 'transfer', 'quit'])
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
        Syncere('./source/ ./destination/ -aH', test=True,
                commands=['preview', 'include *', 'transfer', 'quit'])
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
        Syncere('./source/ ./destination/ -aH', test=True,
                commands=['preview', 'include 1', 'exclude 2',
                          'transfer', 'quit'])
        self.verify("""
        command cd destination
        ! [ foo.txt -ef bar.txt ]
        """)

    def test_log_file(self):
        """
        This test proves that writing a log file doesn't affect rsync's output
        on which syncere relies for providing the preview.
        """
        self.populate("""
        command mkdir source
        command mkdir destination
        command cd source
        command echo "foo" > foo.txt
        command echo "bar" > bar.txt
        """)
        Syncere('./source/ ./destination/ -a --log-file ./log '
                '--log-file-format="%C"', test=True,
                commands=['preview', 'include *', 'transfer', 'quit'])
        self.verify("""
        command cd destination
        [ -f foo.txt ]
        """)
        self.verify("""
        command cd destination
        [ -f bar.txt ]
        """)


@pytest.mark.usefixtures('testdir')
class TestComposedCommands(Utils):
    """
    Test that syncere composes the correct preview and transfer commands based
    on the passed command-line arguments and the entered interactive commands.
    """
    def test_checksum(self):
        self.populate("""
        command mkdir source
        command mkdir destination
        command cd source
        command echo "foo" > foo.txt
        command cd ../destination
        command echo "bar" > foo.txt
        command cd ..
        command touch source/foo.txt destination/foo.txt
        """)
        self.verify("""
        s=$(md5sum source/foo.txt | head -c 32)
        d=$(md5sum destination/foo.txt | head -c 32)
        [ $s != $d ]
        """)
        Syncere('./source/ ./destination/ -a', test=True,
                commands=['preview', 'include *', 'transfer', 'quit'])
        # TODO #1: Test that the application has exited at the correct stage
        self.verify("""
        s=$(md5sum source/foo.txt | head -c 32)
        d=$(md5sum destination/foo.txt | head -c 32)
        [ $s != $d ]
        """)
        Syncere('./source/ ./destination/ -a --checksum', test=True,
                commands=['preview', 'include *', 'transfer', 'quit'])
        # TODO #1: Test that the application has exited at the correct stage
        self.verify("""
        s=$(md5sum source/foo.txt | head -c 32)
        d=$(md5sum destination/foo.txt | head -c 32)
        [ $s == $d ]
        """)


@pytest.mark.usefixtures('testdir')
class TestSyncereOptions(Utils):
    """
    Test the specific syncere options.
    """
    def test_import(self):
        self.populate("""
        command mkdir source
        command mkdir destination
        command cd source
        command echo "foo" > foo.txt
        command echo "bar" > bar.txt
        command cd ..
        command echo "preview" >> script
        command echo "> 1" >> script
        command echo "! 2" >> script
        command echo "transfer" >> script
        command echo "quit" >> script
        """)
        Syncere('./source/ ./destination/ -a', test=True,
                commands=['import ./script'])
        # TODO #1: Test that the application has exited at the correct stage
        self.verify("""
        command cd destination
        ! [ -f foo.txt ]
        """)
        self.verify("""
        command cd destination
        [ -f bar.txt ]
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
        command echo "bar" > bar.txt
        command mkdir abc
        command cd abc
        command echo "blabla\nmorebla" > some.file
        command ln -s foo.txt some.symlink
        command ln some.file some.hardlink
        """)
        Syncere('./source/ ./destination/ -a', test=True,
                commands=[_m_cmenu.TestInteract(repeat=True,
                                                message="\nFree testing!"),
                          'quit'])

import pytest
import subprocess
import textwrap


@pytest.fixture
def testdir(tmpdir):
    # It's necessary to explicitly change into the temp directory
    tmpdir.chdir()


class Utils:
    def populate(self, commands):
        return subprocess.run(textwrap.dedent(commands), shell=True,
                              check=True)

    def verify(self, commands):
        # TODO: To retrieve a detailed list of the directory tree:
        #       find . -printf "%i\t%k\t%M\t%n\t%u\t%g\t%s\t%A+\t%C+\t%T+\t//\t%P\t//->\t%l\t//\n"
        assert subprocess.run(textwrap.dedent(commands), shell=True,
                              check=True).returncode == 0

# syncere - Interactive rsync-based data synchronization.
# Copyright (C) 2016 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of syncere.
#
# syncere is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# syncere is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with syncere.  If not, see <http://www.gnu.org/licenses/>.


# TODO #40
class SyncereError(Exception):
    """
    The base exception from which all other syncere exceptions are derived.
    """
    pass


class ExperimentalOptionWarning(SyncereError):
    pass


class DependencyError(SyncereError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = """\
syncere depends on the external 'forwarg' and 'typein' modules: if you are \
trying to run syncere simply after cloning its repository, please also clone \
'lib.py.forwarg' and 'lib.py.typein' in a folder as siblings (not children) \
of the folder where syncere was cloned:

  $ git clone https://github.com/kynikos/syncere.git
  $ cd syncere
  $ python -m syncere --help

  Here you see this very error, now do:

  $ cd ..
  $ git clone https://github.com/kynikos/lib.py.forwarg.git
  $ git clone https://github.com/kynikos/lib.py.typein.git
  $ cd syncere
  $ python -m syncere --help

  This should make syncere run.

"""


class InsufficientTestCommands(SyncereError):
    pass


class InvalidRuleError(SyncereError):
    pass


class MissingDestinationError(SyncereError):
    pass


class RsyncError(SyncereError):
    pass


class UnrecognizedItemizedChangeError(SyncereError):
    pass


class UnsupportedOptionError(SyncereError):
    pass

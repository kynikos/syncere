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

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

import sys as _m_sys
import shlex as _m_shlex

try:
    import forwarg as _m_forwarg
except ImportError:
    try:
        from . import forwarg as _m_forwarg
    except ImportError as excinfo:
        excinfo.msg = """\
syncere depends on the external 'forwarg' module: if you are trying to run \
syncere simply after cloning its repository, please also clone \
'lib.py.forwarg' in a folder as a sibling (not child) of the folder where \
syncere was cloned:

  $ git clone https://github.com/kynikos/syncere.git
  $ cd syncere
  $ python -m syncere --help

  Here you see this very error, now do:

  $ cd ..
  $ git clone https://github.com/kynikos/lib.py.forwarg.git
  $ cd syncere
  $ python -m syncere --help

  This should make syncere run.

"""
        raise

from .interface import Interface
from .exceptions import UnsupportedOptionError


class ActionHelp(_m_forwarg.Action):
    def _process_flag(self):
        # TODO #3: Note that there are some TODOs in the message
        print("""\
Usage: syncere [syncere_options] [rsync_options] [src [src]...] [dest]

syncere is a drop-in rsync wrapper that makes data synchronization sessions
interactive. The syntax is the same as rsync, with the addition of some
syncere-specific options; refer to rsync's documentation for details. Some
advanced rsync use cases are not supported; syncere will warn for the known
cases of incompatibility.

syncere uses 2 rsync commands internally: the first, which will be referred to
as the "preview" command, is a --dry-run command used to display the pending
changes; the second, which will be referred to as the "transfer" command, is
the command that will be used to transfer the files, properly modified to
exclude the interactively deselected pending changes.

Positional arguments:
    [src] and [dest] are the same arguments as rsync's.

Overridden options:
    These rsync options are completely overridden by syncere; to use their
    rsync version, a separate rsync command must be run.

    --help      Show this help message and exit. Unlike rsync, using -h
                without options is not supported.

    --version   Show syncere's version number, copyright and license
                information, then exit.

Syncere-specific options:
    These options are only used by syncere, they will not be passed to the
    internal rsync commands.

    --ruleset=FILE
                Load a pre-saved set of rules to automatically confirm or
                discard recurrent file transfers. Repeat the option to load
                more rule sets in the specified order. See syncere(1) for the
                used syntax.

    --default-mode=MODE
                Define which transfer mode is the one associated to the
                shortcut '{0}' interactive command; MODE is a string to be
                chosen among {1},
                {2}; the default MODE is '{3}'. See syncere(1) for details on
                transfer modes.

    --experimental
                Enable the experimentally-supported rsync options, see the
                relevant section below.

    --show-identical
                Also list files that are not going to be transferred because
                identical at the source and destination.

Shared options:
    These options are passed to the internal rsync commands, but they are also
    used by syncere. Below only the syncere meaning is explained; refer to the
    rsync documentation for details about their meaning in rsync.

    -v, --verbose
                Increase the verbosity of syncere's output.

    --info=FLAGS
                The internal "preview" rsync command needs to modify this
                option in order to ensure that the list of pending changes is
                retrieved correctly; the FLAGS are instead passed verbatim to
                the "transfer" command.

    -n, --dry-run
                The internal "preview" rsync command forces this option even
                if it is not specified in syncere's command line; if present,
                though, it is also passed to the "transfer" command.

    -i, --itemize-changes
                The internal "preview" rsync command uses a custom --out-format
                option, therefore this option will have no effect on the
                "preview" command; if present, though, it is normally passed to
                the "transfer" command.

    --out-format=FORMAT
                The internal "preview" rsync command needs to modify this
                option in order to ensure that the list of pending changes is
                retrieved correctly; the FORMAT is instead passed verbatim to
                the "transfer" command.

    --stats     The internal "preview" rsync command uses a custom --info
                option, therefore this option will have no effect on the
                "preview" command; if present, though, it will be normally
                passed to the "transfer" command.

Transfer-only options:
    These rsync options are removed from the "preview" command, and only passed
    to the "transfer" command, where their meaning is unchanged.

    --msgs2stderr
    -q, --quiet

Optimized options:
    syncere will offer to optimize the usage of these rsync options when
    possible.

    -c, --checksum
                TODO

Experimental options:
    These rsync options are disabled by default, as the effects in an
    interactive, "two-pass" rsync session are to be more thoroughly assessed.
    You can enable them by passing the --experimental flag. In a later syncere
    release, support for them will be either added or dropped definitively.

    --timeout
    --contimeout
    --outbuf
    -8, --8-bit-output
    -0, --from0

Unsupported options:
    These rsync options are not supported by syncere.

    --daemon
    --config
    -M, --dparam
    -M, --remote-option
    --list-only
    --no-detach

Fully-supported options:
    All the rsync options that are not listed above are fully supported and
    used by both the internal "preview" and the "transfer" commands.

    A special reminder must however be given for the -H/--hard-links option:
    as also pointed out in rsync(1), if a series of hard links are
    synchronized, they must be all included in the transfer command, otherwise
    the linkage will be broken. Just like rsync, syncere will not try to
    warn you if you partially exclude hard links from the synchronization.\
""".format(Interface.CMD_TRANSFER,
           ', '.join("'" + mode + "'" for mode in
                     tuple(Interface.TRANSFER_MODES.values())[:3]),
           ', '.join("'" + mode + "'" for mode in
                     tuple(Interface.TRANSFER_MODES.values())[3:]),
           tuple(Interface.TRANSFER_MODES.values())[0]))
        _m_sys.exit(0)

    def _store_value(self, newvalue):
        pass

    def check_flag(self):
        pass

    def check_value(self):
        pass


class ActionVersion(_m_forwarg.Action):
    def _process_flag(self):
        # Import here, otherwise there's a circular import
        from . import Syncere

        print("""\
syncere {0} {1}

Copyright (C) 2016 Dario Giovannetti <dev@dariogiovannetti.net>
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, you are welcome to redistribute it under the
conditions of the GNU General Public License version 3 or later.
See <http://gnu.org/licenses/gpl.html> for details.\
""".format(Syncere.VERSION_NUMBER, Syncere.VERSION_DATE))
        _m_sys.exit(0)

    def _store_value(self, newvalue):
        pass

    def check_flag(self):
        pass

    def check_value(self):
        pass


class ActionUnsupported(_m_forwarg.Action):
    def _process_flag(self):
        raise UnsupportedOptionError(self.argdef.dest)

    def _store_value(self, newvalue):
        pass

    def check_flag(self):
        pass

    def check_value(self):
        pass


class CLIArgs:
    def __init__(self):
        # args is useful when instantiating this programmatically for testing

        # There would also be the prefix_chars argument, but it would make
        #   using the program too confusing
        #  Anyway, in that case "=" couldn't be used because it's also used to
        #   pass  values to long options, e.g. ==option=value would be
        #   ambiguous
        #  Also other characters are reserved by the shell, e.g. "<" and ">"
        #  "~" would look too similar to the normal "-", and also some programs
        #   use it to indicate temporary files
        self.parser = _m_forwarg.ArgumentParser()

        self._overridden()
        self._syncere()
        self._shared()
        self._transfer_only()
        self._optimized()
        self._experimental()
        self._unsupported()
        self._safe()

    def parse(self, args):
        # There would also be 'parse_known_args' to forward unknown
        # arguments to the rsync commands, however it's buggy and
        # unreliable, especially for short options, see e.g.
        # https://bugs.python.org/issue16142
        return self.parser.parse_args(_m_shlex.split(args)) \
            if args is not None else self.parser.parse_args()

    def _overridden(self):
        group = self.parser.add_argument_group("overridden")

        group.add_argument('--version', action=ActionVersion)

        # TODO #27
        group.add_argument('--help', action=ActionHelp)

    def _syncere(self):
        group = self.parser.add_argument_group('syncere')

        # TODO #5
        group.add_argument('--ruleset', action='append', dest='rulesets',
                           default=[])
        group.add_argument('--default-mode',
                           default=tuple(Interface.TRANSFER_MODES.values())[0],
                           choices=Interface.TRANSFER_MODES.values())
        group.add_argument('--experimental', action='store_true')
        group.add_argument('--show-identical', action='store_true')

    def _shared(self):
        group = self.parser.add_argument_group('shared')

        # Note that differentiating between sources and destination isn't
        # supported yet by forwarg, since it would require sources to have a
        # '*?' (non-greedy) nargs to let the last value be assigned to
        # destination
        group.add_argument('locations', nargs='+')

        # TODO #28
        group.add_argument('-v', '--verbose', action='count')

        # TODO #28 #29
        group.add_argument('--info', action='append')

        # TODO #28
        group.add_argument('-n', '--dry-run', action='store_true')

        # TODO #28
        group.add_argument('-i', '--itemize-changes', action='store_true')

        # TODO #28
        group.add_argument('--out-format')

        # TODO #28
        group.add_argument('--stats', action='store_true')

    def _transfer_only(self):
        group = self.parser.add_argument_group('transfer-only')

        group.add_argument('--msgs2stderr', action='store_true')
        group.add_argument('-q', '--quiet', action='store_true')

    def _optimized(self):
        group = self.parser.add_argument_group('optimized')

        # TODO #3
        group.add_argument('-c', '--checksum', action='store_true')

    def _experimental(self):
        group = self.parser.add_argument_group('experimental')

        # TODO #37
        group.add_argument('--timeout')

        # TODO #37
        group.add_argument('--contimeout')

        # TODO #37
        group.add_argument('--outbuf')

        # TODO #37
        group.add_argument('-8', '--8-bit-output', action='store_true')

        # TODO #37: This can create problems if the generated files use
        #           different  delimiters
        group.add_argument('-0', '--from0', action='store_true')

    def _unsupported(self):
        group = self.parser.add_argument_group('unsupported')

        group.add_argument('--daemon', action=ActionUnsupported)
        group.add_argument('--config', action=ActionUnsupported)
        group.add_argument('-M', '--remote-option', '--dparam',
                           action=ActionUnsupported)
        group.add_argument('--list-only', action=ActionUnsupported)
        group.add_argument('--no-detach', action=ActionUnsupported)

    def _safe(self):
        group = self.parser.add_argument_group('safe')

        # TODO #29
        group.add_argument('--debug', action='append')

        group.add_argument('--no-motd', action='store_true')
        group.add_argument('-I', '--ignore-times', action='store_true')
        group.add_argument('--size-only', action='store_true')
        group.add_argument('--modify-window')
        group.add_argument('-a', '--archive', action='store_true')
        group.add_argument('-r', '--recursive', action='store_true')
        group.add_argument('--no-recursive', '--no-r', action='store_true')
        group.add_argument('--no-inc-recursive', '--no-i-r',
                           action='store_true')
        group.add_argument('-R', '--relative', action='store_true')
        group.add_argument('--no-relative', '--no-R', action='store_true')
        group.add_argument('--no-implied-dirs', action='store_true')
        group.add_argument('-b', '--backup', action='store_true')

        # TODO #29
        group.add_argument('--backup-dir')

        # TODO #29
        group.add_argument('--suffix')

        group.add_argument('-u', '--update', action='store_true')
        group.add_argument('--inplace', action='store_true')
        group.add_argument('--append', action='store_true')
        group.add_argument('--append-verify', action='store_true')
        group.add_argument('-d', '--dirs', action='store_true')
        group.add_argument('--no-dirs', '--no-d', action='store_true')
        group.add_argument('-l', '--links', action='store_true')
        group.add_argument('--no-links', '--no-l', action='store_true')
        group.add_argument('-L', '--copy-links', action='store_true')
        group.add_argument('--copy-unsafe-links', action='store_true')
        group.add_argument('--safe-links', action='store_true')
        group.add_argument('--munge-links', action='store_true')
        group.add_argument('-k', '--copy-dirlinks', action='store_true')
        group.add_argument('-K', '--keep-dirlinks', action='store_true')
        group.add_argument('-H', '--hard-links', action='store_true')
        group.add_argument('-p', '--perms', action='store_true')
        group.add_argument('--no-perms', '--no-p', action='store_true')
        group.add_argument('-E', '--executability', action='store_true')
        group.add_argument('-A', '--acls', action='store_true')
        group.add_argument('-X', '--xattrs', action='count')
        group.add_argument('--chmod', action='append')
        group.add_argument('-o', '--owner', action='store_true')
        group.add_argument('--no-owner', '--no-o', action='store_true')
        group.add_argument('-g', '--group', action='store_true')
        group.add_argument('--no-group', '--no-g', action='store_true')
        group.add_argument('--devices', action='store_true')
        group.add_argument('--specials', action='store_true')
        group.add_argument('-D', action='store_true')
        group.add_argument('--no-D', action='store_true')
        group.add_argument('-t', '--times', action='store_true')
        group.add_argument('--no-times', '--no-t', action='store_true')
        group.add_argument('-O', '--omit-dir-times', action='store_true')
        group.add_argument('-J', '--omit-link-times', action='store_true')
        group.add_argument('--super', action='store_true')
        group.add_argument('--no-super', action='store_true')
        group.add_argument('--fake-super', action='store_true')
        group.add_argument('-S', '--sparse', action='store_true')
        group.add_argument('--preallocate', action='store_true')
        group.add_argument('-W', '--whole-file', action='store_true')
        group.add_argument('--no-whole-file', '--no-W', action='store_true')
        group.add_argument('-x', '--one-file-system', action='store_true')
        group.add_argument('--no-one-file-system', '--no-x',
                           action='store_true')
        group.add_argument('--existing', '--ignore-non-existing',
                           action='store_true')
        group.add_argument('--ignore-existing', action='store_true')
        group.add_argument('--remove-source-files', action='store_true')
        group.add_argument('--delete', action='store_true')
        group.add_argument('--delete-before', action='store_true')
        group.add_argument('--delete-during', '--del', action='store_true')
        group.add_argument('--delete-delay', action='store_true')
        group.add_argument('--delete-after', action='store_true')
        group.add_argument('--delete-excluded', action='store_true')
        group.add_argument('--ignore-missing-args', action='store_true')
        group.add_argument('--delete-missing-args', action='store_true')
        group.add_argument('--ignore-errors', action='store_true')
        group.add_argument('--force', action='store_true')
        group.add_argument('--max-delete')
        group.add_argument('--max-size')
        group.add_argument('--min-size')
        group.add_argument('-B', '--block-size')
        group.add_argument('-e', '--rsh')
        group.add_argument('--rsync-path')
        group.add_argument('-C', '--cvs-exclude', action='store_true')
        group.add_argument('-f', '--filter', action='append')
        group.add_argument('-F', action='append')
        group.add_argument('--exclude', action='append')
        group.add_argument('--exclude-from', action='append')
        group.add_argument('--include', action='append')
        group.add_argument('--include-from', action='append')
        group.add_argument('--files-from', action='append')
        group.add_argument('-T', '--temp-dir')
        group.add_argument('-s', '--protect-args', action='store_true')
        group.add_argument('--no-protect-args', '--no-s', action='store_true')

        # TODO #36
        group.add_argument('-y', '--fuzzy', action='count')

        group.add_argument('--compare-dest', action='append')
        group.add_argument('--copy-dest', action='append')
        group.add_argument('--link-dest', action='append')
        group.add_argument('-z', '--compress', action='count')
        group.add_argument('--new-compress', action='store_true')
        group.add_argument('--old-compress', action='store_true')
        group.add_argument('--compress-level')

        # TODO #29
        group.add_argument('--skip-compress', action='append')

        group.add_argument('--numeric-ids', action='store_true')

        # TODO #29
        group.add_argument('--usermap', action='append')

        # TODO #29
        group.add_argument('--groupmap', action='append')

        group.add_argument('--chown')
        group.add_argument('--address')
        group.add_argument('--port')

        # TODO #29
        group.add_argument('--sockopts', action='append')

        group.add_argument('--blocking-io', action='store_true')
        group.add_argument('--no-blocking-io', action='store_true')
        group.add_argument('--log-file')

        # TODO #46
        group.add_argument('--log-file-format')

        group.add_argument('-h', '--human-readable', action='count')
        group.add_argument('--no-human-readable', '--no-h',
                           action='store_true')
        group.add_argument('--partial', action='store_true')
        group.add_argument('--partial-dir')
        group.add_argument('--delay-updates', action='store_true')
        group.add_argument('-m', '--prune-empty-dirs', action='store_true')
        group.add_argument('--progress', action='store_true')
        group.add_argument('-P', action='store_true')
        group.add_argument('--password-file')
        group.add_argument('--bwlimit')
        group.add_argument('--write-batch')
        group.add_argument('--only-write-batch')
        group.add_argument('--read-batch')
        group.add_argument('--protocol')
        group.add_argument('--iconv')
        group.add_argument('--no-iconv', action='store_true')
        group.add_argument('-4', '--ipv4', action='store_true')
        group.add_argument('-6', '--ipv6', action='store_true')
        group.add_argument('--checksum-seed')

# syncere - Turn rsync commands interactive.
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
import subprocess as _m_subprocess
import re as _m_re

from .cliargs import CLIArgs
from .interface import MainMenu
from . import exceptions


class Syncere:
    """
    The main class, primarily responsible for managing the internal rsync
    commands.
    """
    VERSION_NUMBER = '0.1.0'
    VERSION_DATE = '2016-04-17'

    def __init__(self, cliargs=None, commands=[], test=False):
        self.cliargs = CLIArgs().parse(cliargs)
        self._check_arguments()

        # If experimental is disabled and some of its options have been
        # specified, the program has already exited in _check_arguments
        self.previewargs = self.cliargs.filter_whitelist(groups=(
                                'shared', 'optimized', 'experimental', 'safe'))
        self.transferargs = self.cliargs.filter_whitelist(groups=(
                                'shared', 'transfer-only', 'optimized',
                                'experimental', 'safe'))

        self._preview()
        self._parse_pending_changes()
        if self.pending_changes:
            interface = MainMenu(self.pending_changes)
            interface.start_loop(self.cliargs, commands, test)
            self._transfer(interface.transfer_mode)
        else:
            print("Nothing to do")
            _m_sys.exit(0)

    def _check_arguments(self):
        if self.cliargs.namespace.experimental is not True:
            for argdef in self.cliargs.parser.title_to_group[
                                    'experimental'].dest_to_argdef.values():
                if self.cliargs.argdef_to_argholder[argdef].value is not None:
                    raise exceptions.ExperimentalOptionWarning(argdef.dest)
        if len(self.cliargs.namespace.locations) < 2:
            raise exceptions.MissingDestinationError()

    def _preview(self):
        # TODO #14
        call = _m_subprocess.Popen(['rsync', *self.previewargs, '--dry-run',
                                    '--info',
                                    'backup4,copy4,del4,flist4,misc4,'
                                    'mount4,name4,remove4,skip4,symsafe4',
                                    '--out-format',
                                    '{syncere}%i '  # itemized changes
                                    '%o '  # operation
                                    '%B '  # permissions
                                    '%U '  # uid
                                    '%G '  # gid
                                    '%l '  # length (bytes)
                                    '{//}%M'  # last mod timestamp
                                    '{//}%f'  # filename (long)
                                    '{//}%n'  # filename (short)
                                    '{//}%L'  # link string
                                    '{//}%C'  # md5
                                    '{/syncere}'],
                                   stdout=_m_subprocess.PIPE,
                                   universal_newlines=True)

        # Popen.communicate already waits for the process to terminate, there's
        # no need to call wait
        # TODO #12 #13 #22
        self.stdout = call.communicate()[0]

        if call.returncode != 0:
            # TODO #15: Use sys.exit(call.returncode)?
            raise exceptions.RsyncError(call.returncode)

    def _parse_pending_changes(self):
        self.pending_changes = []

        for ln, line in enumerate(self.stdout.splitlines()):
            if line[:9] == '{syncere}':
                match = _m_re.match('\{syncere}(.{11}) '
                                    '(send|recv|del\.) '
                                    # TODO #42: test if %B shows ACLs like
                                    #           ls -l
                                    '(.+?) '
                                    '([0-9]+) '
                                    '([0-9]+|DEFAULT) '
                                    '([0-9]+) '
                                    '\{//\}(.+?)'
                                    '\{//\}(.+?)'
                                    '\{//\}(.+?)'
                                    '\{//\}(.*?)'
                                    '\{//\}([0-9a-fA-F]{32}| {32})'
                                    '\{/syncere\}',
                                    line)

                if match:
                    self.pending_changes.append(Change(
                                                len(self.pending_changes) + 1,
                                                *match.groups()))
                else:
                    raise exceptions.UnrecognizedItemizedChangeError(line)
            else:
                # TODO #28: Allow suppressing these lines
                print(line)

    def _transfer(self, mode):
        # TODO #17
        args = {'exclude': self._transfer_exclude,
                'exclude-from': self._transfer_exclude_from,
                'include': self._transfer_include,
                'include-from': self._transfer_include_from,
                'files-from': self._transfer_files_from}[mode]()
        # TODO #14 #18
        call = _m_subprocess.Popen(args)

        # TODO #19 #23 (otherwise maybe calling 'wait' is unneeded?)
        call.wait()

    def _transfer_exclude(self):
        # TODO #24

        # Note that Popen already does all the necessary escaping on the
        # arguments
        excludes = []
        for change in self.pending_changes:
            if not change.included:
                excludes.extend(['--exclude', change.sfilename])

        # Prepend, not append, excludes, since the original rsync command may
        # have other include/exclude/filter rules, and rsync stops at the first
        # match that it finds
        return ['rsync', *excludes, *self.transferargs]

    def _transfer_exclude_from(self):
        # TODO #23
        FILE = './exclude_from'

        with open(FILE, 'w'):
            # First make sure the file is empty
            pass
        with open(FILE, 'a') as filefrom:
            for change in self.pending_changes:
                if not change.included:
                    filefrom.write(change.sfilename + '\n')

        # Prepend, not append, excludes, since the original rsync command may
        # have other include/exclude/filter rules, and rsync stops at the first
        # match that it finds
        return ['rsync', '--exclude-from', FILE, *self.transferargs]

    def _transfer_include(self):
        # TODO #24

        # Note that Popen already does all the necessary escaping on the
        # arguments
        includes = []
        for change in self.pending_changes:
            if change.included:
                includes.extend(['--include', change.sfilename])

        # Prepend, not append, includes, since the original rsync command may
        # have other include/exclude/filter rules, and rsync stops at the first
        # match that it finds
        return ['rsync', *includes, '--exclude', '*', *self.transferargs]

    def _transfer_include_from(self):
        # TODO #23
        FILE = './include_from'

        with open(FILE, 'w'):
            # First make sure the file is empty
            pass
        with open(FILE, 'a') as filefrom:
            for change in self.pending_changes:
                if change.included:
                    filefrom.write(change.sfilename + '\n')

        # Prepend, not append, includes, since the original rsync command may
        # have other include/exclude/filter rules, and rsync stops at the first
        # match that it finds
        return ['rsync', '--include-from', FILE, '--exclude', '*',
                *self.transferargs]

    def _transfer_files_from(self):
        # TODO #23
        FILE = './files_from'

        with open(FILE, 'w'):
            # First make sure the file is empty
            pass
        with open(FILE, 'a') as filefrom:
            for change in self.pending_changes:
                if change.included:
                    filefrom.write(change.sfilename + '\n')

        return ['rsync', '--files-from', FILE, *self.transferargs]


class Change:
    """
    Objects of this class represent pending changes.
    """
    STATUS = {
        # TODO #56
        None: ' ? ',
        True: '  >',
        False: '!  ',
    }

    def __init__(self, id_, ichange, operation, permissions, uid, gid,
                 length, tstamp, lfilename, sfilename, link, checksum):
        self.id_ = id_
        self.ichange = ichange
        self.operation = operation
        self.permissions = permissions
        self.uid = uid
        self.gid = gid
        self.length = length
        self.tstamp = tstamp
        self.lfilename = lfilename
        self.sfilename = sfilename
        self.link = link
        self.checksum = checksum

        self.reset()

    def get_summary(self, width):
        pad = width - len(str(self.id_))
        return '[{0}{1}] {2} {3}   {4}{5}'.format(' ' * pad, self.id_,
                                                  self.STATUS[self.included],
                                                  self.operation,
                                                  self.sfilename, self.link)

    def get_details(self, width):
        return ' ' * (7 + width) + ' '.join((self.ichange, self.permissions,
                                             self.uid, self.gid, self.length,
                                             self.tstamp, self.checksum))

    def include(self):
        self.included = True

    def exclude(self):
        self.included = False

    def reset(self):
        self.included = None

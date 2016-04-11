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
# TODO: Use proper logging

from .cliargs import CLIArgs
from .rules import Rules
from .interface import Interface
from . import exceptions


class Syncere:
    """
    The main class, primarily responsible for managing the internal rsync
    commands.
    """
    # TODO: Remind to keep up to date
    VERSION_NUMBER = '0.1.0'
    VERSION_DATE = '(2016-04-06)'

    def __init__(self, cliargs=None, test=False):
        # TODO: Support instantiation without cli arguments (e.g. using
        #       **kwargs)
        # TODO: Use fnmatch for globbing patterns
        # TODO: Rulesets should be looked for in .config etc.
        self.cliargs = CLIArgs().parse(cliargs)
        self._check_arguments()

        self._preview()
        self._store_rules()
        self._parse_pending_changes()
        # TODO: Also allow optionally bypassing the interface if there are no
        #       undecided pending changes left after applying the rules (i.e.
        #       sync without confirmation)
        if self.pending_changes:
            Interface(self.pending_changes, test)
            self._synchronize()
        else:
            # FIXME
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
        # If experimental is disabled and some of its options have been
        # specified, the program has already exited by now
        rsyncargs = self.cliargs.filter_whitelist(groups=('shared',
                                                          'optimized',
                                                          'experimental',
                                                          'safe'))

        # TODO:
        #  * Reflect rsync commands' error exit values
        #  * Also capture stderr?
        #  * What is the maximum size of the data that stdout can host?
        #  * Support terminating with Ctrl+c or in some other way
        call = _m_subprocess.Popen(['rsync', *rsyncargs, '--dry-run', '--info',
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
        # TODO: Display a dynamic "processing..." message in a separate thread,
        #       using \r to refresh the line
        # TODO: Print the process' output in real time, but watch out for the
        #       deadlock problems!!!
        #       https://docs.python.org/3.5/library/subprocess.html
        self.stdout = call.communicate()[0]

        if call.returncode != 0:
            # TODO: Use sys.exit(call.returncode)?
            raise exceptions.RsyncError(call.returncode)

    def _store_rules(self):
        self.rules = Rules()

        # TODO: support all the ways to add rules and rulesets
        for setname in self.cliargs.namespace.rulesets:
            self.rules.parse_ruleset(setname)

    def _parse_pending_changes(self):
        # TODO: Here the rulesets should be loaded and compared against the
        #       parsed changes to set their self.included attribute
        #       Or maybe this can be done later and merged with the function
        #       that applies the rules from a file created dynamically to edit
        #       them
        self.pending_changes = []

        for ln, line in enumerate(self.stdout.splitlines()):
            if line[:9] == '{syncere}':
                match = _m_re.match('\{syncere}(.{11}) '
                                    '(send|recv|del\.) '
                                    # TODO: test if %B shows ACLs like ls -l
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
                                                self.rules,
                                                len(self.pending_changes) + 1,
                                                *match.groups()))
                else:
                    raise exceptions.UnrecognizedItemizedChangeError()
            else:
                # TODO: Allow suppressing these lines
                # FIXME
                print(line)

    def _synchronize(self):
        # TODO: Allow choosing the method from the interface or the command
        #       line options; it should also be possible to set a default
        #       method to a shortcut interface command, e.g. 'X'
        #       Each has its advantages and disadvantages (see e.g. --checksum
        #       and problems with (hard) links)
        # TODO: Also allow writing file objects and feeding them to the
        #       transfer command with stdinput; of course this requires that
        #       stdinput is not used for some other reason
        for args in (self._synchronize_exclude(),
                     self._synchronize_exclude_from(),
                     self._synchronize_include(),
                     self._synchronize_include_from(),
                     self._synchronize_files_from()):
            # FIXME
            print(' '.join(args))
            # TODO: Support terminating with Ctrl+c or in some other way
            # TODO: Pass the original sys.stdin, if present, to the command
            # TODO: Test what happens in case of an rsync error here
            call = _m_subprocess.Popen(args)

            # TODO: unneeded in production? Or needed to return rsync's return
            #       code?
            call.wait()

    def _synchronize_exclude(self):
        # TODO: Also consider the maximum length of a command, default to
        #  _synchronize_exclude_from if too long

        # Note that Popen already does all the necessary escaping on the
        # arguments
        excludes = []
        for change in self.pending_changes:
            if not change.included:
                excludes.extend(['--exclude', change.sfilename])

        # Prepend, not append, excludes, since the original rsync command may
        # have other include/exclude/filter rules, and rsync stops at the first
        # match that it finds
        # TODO: Still allow appending them optionally?
        return ['rsync', *excludes, *self.rsyncargs]

    def _synchronize_exclude_from(self):
        # TODO: Allow choosing the path
        FILE = './exclude_from'

        # TODO: Protect from exceptions (permissions...)
        # TODO: Warn if the file already exists
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
        # TODO: Still allow appending them optionally?
        return ['rsync', '--exclude-from', FILE, *self.rsyncargs]

    def _synchronize_include(self):
        # TODO: Also consider the maximum length of a command, default to
        #  _synchronize_include_from if too long

        # Note that Popen already does all the necessary escaping on the
        # arguments
        includes = []
        for change in self.pending_changes:
            if change.included:
                includes.extend(['--include', change.sfilename])

        # Prepend, not append, includes, since the original rsync command may
        # have other include/exclude/filter rules, and rsync stops at the first
        # match that it finds
        # TODO: Still allow appending them optionally?
        return ['rsync', *includes, '--exclude', '*', *self.rsyncargs]

    def _synchronize_include_from(self):
        # TODO: Allow choosing the path
        FILE = './include_from'

        # TODO: Protect from exceptions (permissions...)
        # TODO: Warn if the file already exists
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
        # TODO: Still allow appending them optionally?
        return ['rsync', '--include-from', FILE, '--exclude', '*',
                *self.rsyncargs]

    def _synchronize_files_from(self):
        # TODO: Allow choosing the path
        FILE = './files_from'

        # TODO: Protect from exceptions (permissions...)
        # TODO: Warn if the file already exists
        with open(FILE, 'w'):
            # First make sure the file is empty
            pass
        with open(FILE, 'a') as filefrom:
            for change in self.pending_changes:
                if change.included:
                    filefrom.write(change.sfilename + '\n')

        # TODO: Allow appending --files-from instead of prepending it?
        return ['rsync', '--files-from', FILE, *self.rsyncargs]


class Change:
    """
    Objects of this class represent pending changes.
    """
    STATUS = {
        # TODO: All these strings should be defined in a central place instead
        #       of hardcoding them everywhere
        None: ' ? ',
        True: '  >',
        False: '!  ',
    }
    INV_STATUS = {v.strip(): k for k, v in STATUS.items()}

    def __init__(self, rules, id_, ichange, operation, permissions, uid, gid,
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

        self.included = self.INV_STATUS[rules.decide_change(self.ichange,
                                                            self.sfilename)]

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

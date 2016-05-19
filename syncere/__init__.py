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
import os as _m_os
import subprocess as _m_subprocess
import re as _m_re
import fnmatch as _m_fnmatch

from .cliargs import _m_forwarg, CLIArgs
from . import exceptions

try:
    import cmenu as _m_cmenu
except ImportError:
    try:
        from . import cmenu as _m_cmenu
    except ImportError:
        raise exceptions.DependencyError()


class Syncere:
    """
    The main class, primarily responsible for managing the internal rsync
    commands.
    """
    VERSION_NUMBER = '0.8.0'
    VERSION_DATE = '2016-05-07'
    DEFAULT_STARTUP_COMMANDS = ['preview quit', 'list']
    DEFAULT_CONFIG = {
        'max-inline-filters': '12',
        'preview-info-flags': 'backup4,copy4,del4,flist4,misc4,mount4,name1,'
                              'remove4,symsafe4',
    }

    def __init__(self, cliargs=None, commands=[], test=False):
        self._parse_arguments(cliargs)
        self.configuration = self.DEFAULT_CONFIG.copy()
        self.messages = Messages(self)
        self.preview_needed = True
        self.pending_changes = []
        self._start_interface(commands, test)

    def _parse_arguments(self, cliargs):
        self.cliargs = CLIArgs().parse(cliargs)

        if self.cliargs.namespace.experimental is not True:
            for argdef in self.cliargs.parser.title_to_group[
                                    'experimental'].dest_to_argdef.values():
                if self.cliargs.argdef_to_argholder[argdef].value is not None:
                    raise exceptions.ExperimentalOptionWarning(argdef.dest)
        if len(self.cliargs.namespace.locations) < 2:
            raise exceptions.MissingDestinationError()

    def _start_interface(self, commands, test):
        # TODO #30 #31 #33
        self.mainmenu = MainMenu(self, test).menu

        # When testing, we don't want the original DEFAULT_STARTUP_COMMANDS to
        # be modified directly by the tests, so clone it
        commands = commands or self.cliargs.namespace.commands or \
            self.DEFAULT_STARTUP_COMMANDS[:]
        # This can raise _m_cmenu.InsufficientTestCommands: if testing, the
        # last command should be one that quits syncere
        self.mainmenu.loop(intro="Type 'help' to list available commands\n",
                           cmdlines=commands, test=test)

    def clear_preview(self):
        self.pending_changes.clear()
        self.preview_needed = True


class Messages:
    COLOR_RESET = "\033[0m"
    COLOR_ERROR = "\033[0;31m"  # red fg
    COLOR_PROMPT = "\033[0;32m"  # green fg
    COLOR_CHANGE_UNDECIDED = "\033[1;33m"  # yellow fg
    COLOR_CHANGE_INCLUDED = "\033[1;32m"  # green fg
    COLOR_CHANGE_EXCLUDED = "\033[1;31m"  # red fg

    ICON_CHANGE_UNDECIDED = '?'
    ICON_CHANGE_INCLUDED = '>'
    ICON_CHANGE_EXCLUDED = '!'
    STATUS_TO_ICON_COL = {
        None: ' {}{}{} '.format(COLOR_CHANGE_UNDECIDED,
                                ICON_CHANGE_UNDECIDED,
                                COLOR_RESET),
        True: '  {}{}{}'.format(COLOR_CHANGE_INCLUDED,
                                ICON_CHANGE_INCLUDED,
                                COLOR_RESET),
        False: '{}{}{}  '.format(COLOR_CHANGE_EXCLUDED,
                                 ICON_CHANGE_EXCLUDED,
                                 COLOR_RESET),
    }
    STATUS_TO_ICON_NOCOL = {
        None: ' {} '.format(ICON_CHANGE_UNDECIDED),
        True: '  {}'.format(ICON_CHANGE_INCLUDED),
        False: '{}  '.format(ICON_CHANGE_EXCLUDED),
    }

    file_cannot_be_written = 'cannot be written:'
    nothing_to_do = 'Nothing to do'
    preview_needed = 'The preview command must be executed first'
    rsync_error = 'rsync error:'
    selection_bad_args = 'Unrecognized selection'
    selection_bad_syntax = 'Bad filter syntax'
    selection_no_changes = 'There are no pending changes'
    selection_null = 'No changes selected'
    transfer_ambiguous_mode = 'Transfer modes are mutually exclusive'
    transfer_no_changes = 'There are no pending changes'
    transfer_selection_null = 'All changes have been excluded'
    transfer_selection_undecided = 'There are still undecided changes'
    unrecognized_arguments = 'Unrecognized arguments:'
    wrong_syntax = 'Wrong syntax'

    def __init__(self, rootapp):
        self.rootapp = rootapp

        self.error_prefix = self.COLOR_ERROR
        self.reset_suffix = self.COLOR_RESET
        self._error_prefix = self.error_prefix
        self._reset_suffix = self.reset_suffix

        self.cmenu = _m_cmenu.MessagesColorable(self.error_prefix,
                                                self.reset_suffix)
        self.status_to_icon = self.STATUS_TO_ICON_COL

    def enable_colors(self):
        self._error_prefix = self.error_prefix
        self._reset_suffix = self.reset_suffix

        for menu in self.rootapp.mainmenu.iter_walk_menus():
            menu.prompt.enable_colors()
        self.cmenu.enable_colors()
        self.status_to_icon = self.STATUS_TO_ICON_COL

    def disable_colors(self):
        self._error_prefix = ''
        self._reset_suffix = ''

        for menu in self.rootapp.mainmenu.iter_walk_menus():
            menu.prompt.disable_colors()
        self.cmenu.disable_colors()
        self.status_to_icon = self.STATUS_TO_ICON_NOCOL

    def info(self, message, *args):
        print(message, *args)

    def error(self, message, *args):
        print(message.join((self._error_prefix, self._reset_suffix)), *args)


class Prompt(_m_cmenu.DynamicPromptColorable):
    MON_PREFIX = '('
    MON_SEPARATOR = '>'
    MON_SUFFIX = ') '
    COL_PREFIX = MON_PREFIX.join((Messages.COLOR_PROMPT, Messages.COLOR_RESET))
    COL_SEPARATOR = MON_SEPARATOR.join((Messages.COLOR_PROMPT,
                                        Messages.COLOR_RESET))
    COL_SUFFIX = MON_SUFFIX.join((Messages.COLOR_PROMPT, Messages.COLOR_RESET))


class Change:
    """
    Objects of this class represent pending changes.
    """
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

    def get_summary(self):
        return (self.ichange, )

    def get_details(self):
        return (self.ichange, self.permissions, self.uid, self.gid,
                self.length, self.tstamp)

    def include(self):
        self.included = True

    def exclude(self):
        self.included = False

    def reset(self):
        self.included = None


class _ChangeFilter:
    BadFilter = type('BadFilter', (Exception, ), {})

    def __init__(self, rootapp):
        self.rootapp = rootapp
        self.pending_changes = rootapp.pending_changes

        self.parser = _m_forwarg.ArgumentParser()
        self.parser.add_argument('ids', nargs='*')
        self.parser.add_argument('-i', '--itemized-change', action='append')
        self.parser.add_argument('-o', '--operation', action='append')
        self.parser.add_argument('-p', '--permissions', action='append')
        self.parser.add_argument('-u', '--owner-id', action='append')
        self.parser.add_argument('-g', '--group-id', action='append')
        self.parser.add_argument('-s', '--size', action='append')
        self.parser.add_argument('-t', '--timestamp', action='append')
        self.parser.add_argument('-f', '--exact-path', action='append')
        self.parser.add_argument('-F', '--exact-path-icase', action='append')
        self.parser.add_argument('-x', '--regex-path', action='append')
        self.parser.add_argument('-X', '--regex-path-icase', action='append')
        self.parser.add_argument('-w', '--glob-path', action='append')
        self.parser.add_argument('-W', '--glob-path-icase', action='append')

        self.arg_to_filter = {
            'itemized_change': self._select_changes_by_itemized_change,
            'operation': self._select_changes_by_operation,
            'permissions': self._select_changes_by_permissions,
            'owner_id': self._select_changes_by_owner_id,
            'group_id': self._select_changes_by_group_id,
            'size': self._select_changes_by_size,
            'timestamp': self._select_changes_by_timestamp,
            'exact_path': self._select_changes_by_exact_path,
            'exact_path_icase': self._select_changes_by_exact_path_icase,
            'regex_path': self._select_changes_by_regex_path,
            'regex_path_icase': self._select_changes_by_regex_path_icase,
            'glob_path': self._select_changes_by_glob_path,
            'glob_path_icase': self._select_changes_by_glob_path_icase,
        }

    def select(self, *args):
        if self.rootapp.preview_needed:
            self.rootapp.messages.error(self.rootapp.messages.preview_needed)
            return self.pending_changes

        if not self.pending_changes:
            self.rootapp.messages.error(
                                    self.rootapp.messages.selection_no_changes)
            return self.pending_changes

        try:
            sargs = self.parser.parse_args(args)
        except _m_forwarg.ForwargError:
            self.rootapp.messages.error(
                                    self.rootapp.messages.selection_bad_syntax)
            return []

        try:
            # Process id ranges first, thus initializing the changes list
            # All the other filters will instead subtract from it
            changes = self._select_changes_by_id(sargs.namespace.ids)

            for change in changes[:]:
                for arg, filter_ in self.arg_to_filter.items():
                    tests = vars(sargs.namespace)[arg]
                    if tests:
                        for test in tests:
                            if filter_(change, test) is True:
                                break
                        else:
                            changes.remove(change)
                            break
        except self.BadFilter:
            self.rootapp.messages.error(
                                    self.rootapp.messages.selection_bad_args)
            return []

        if not changes:
            self.rootapp.messages.error(self.rootapp.messages.selection_null)

        return changes

    @staticmethod
    def _get_0_based_id(selid):
        # This line itself can raise ValueError
        id0 = int(selid) - 1
        if id0 < 0:
            raise ValueError()
        return id0

    def _select_changes_by_id(self, ids):
        if not ids:
            return self.pending_changes[:]

        changes = []

        for rawsel in ids:
            if rawsel == '*':
                return self.pending_changes[:]

            lsel = rawsel.split(',')

            for isel in lsel:
                rsel = isel.split('-')

                if len(rsel) == 1:
                    try:
                        id0 = self._get_0_based_id(isel)
                        change = self.pending_changes[id0]
                    except (ValueError, IndexError):
                        raise self.BadFilter()
                    else:
                        if change not in changes:
                            changes.append(change)

                elif len(rsel) == 2:
                    try:
                        ids, ide = [self._get_0_based_id(rid) for rid in rsel]
                    except ValueError:
                        raise self.BadFilter()
                    else:
                        for change in self.pending_changes[ids:ide + 1]:
                            if change not in changes:
                                changes.append(change)

                else:
                    raise self.BadFilter()

        return changes

    def _select_changes_by_itemized_change(self, change, test):
        return test == change.ichange

    def _select_changes_by_operation(self, change, test):
        return test == change.operation

    def _select_changes_by_permissions(self, change, test):
        return test == change.permissions

    def _select_changes_by_owner_id(self, change, test):
        return test == change.uid

    def _select_changes_by_group_id(self, change, test):
        return test == change.gid

    def _select_changes_by_size(self, change, test):
        return test == change.length

    def _select_changes_by_timestamp(self, change, test):
        return test == change.tstamp

    def _select_changes_by_exact_path(self, change, test):
        return test == change.sfilename

    def _select_changes_by_exact_path_icase(self, change, test):
        return test.lower() == change.sfilename.lower()

    def _select_changes_by_regex_path(self, change, test):
        try:
            return bool(_m_re.search(test, change.sfilename))
        except _m_re.error:
            raise self.BadFilter()

    def _select_changes_by_regex_path_icase(self, change, test):
        try:
            return bool(_m_re.search(test, change.sfilename, flags=_m_re.I))
        except _m_re.error:
            raise self.BadFilter()

    def _select_changes_by_glob_path(self, change, test):
        return _m_fnmatch.fnmatch(change.sfilename, test)

    def _select_changes_by_glob_path_icase(self, change, test):
        return _m_fnmatch.fnmatch(change.sfilename.lower(), test.lower())


class TransferCommand:
    DEFAULT_EXCLUDE_FROM_FILE = './exclude-from'
    DEFAULT_INCLUDE_FROM_FILE = './include-from'
    DEFAULT_FILES_FROM_FILE = './files-from'

    def __init__(self, rootapp, menu):
        self.rootapp = rootapp
        self.menu = menu

        self.parser = _m_forwarg.ArgumentParser()
        self.parser.add_argument('-e', '--exclude', action='store_true')
        # Don't define a default file name here, e.g. const='./exclude-from'
        # because otherwise when no mode is specified and the mode to use is
        # chosen automatically, and max-inline-filters is exceeded, the
        # automatic mode won't be able to see the default file name
        self.parser.add_argument('-E', '--exclude-from', nargs='?', const=True)
        self.parser.add_argument('-i', '--include', action='store_true')
        # Don't define a default file name here, e.g. const='./exclude-from'
        # because otherwise when no mode is specified and the mode to use is
        # chosen automatically, and max-inline-filters is exceeded, the
        # automatic mode won't be able to see the default file name
        self.parser.add_argument('-I', '--include-from', nargs='?', const=True)
        # Don't define a default file name here, e.g. const='./exclude-from'
        # because otherwise when no mode is specified and the mode to use is
        # chosen automatically, and max-inline-filters is exceeded, the
        # automatic mode won't be able to see the default file name
        self.parser.add_argument('-F', '--files-from', nargs='?', const=True)
        self.parser.add_argument('-c', '--checksum', action='store_true')
        # Don't define a default file name here, e.g. const='./exclude-from'
        # because otherwise when no mode is specified and the mode to use is
        # chosen automatically, and max-inline-filters is exceeded, the
        # automatic mode won't be able to see the default file name
        self.parser.add_argument('-C', '--checksum-from', nargs='?',
                                 const=True)
        self.parser.add_argument('-k', '--keep-list', action='store_true')
        self.parser.add_argument('-v', '--view-only', action='store_true')
        self.parser.add_argument('-n', '--dry-run', action='store_true')
        self.parser.add_argument('-q', '--quit', action='store_true')

    def execute(self, *args):
        """
        Start the synchronization.

        Start the synchronization in exclude mode.

        The original rsync command will be executed, but --exclude options will
        be prepended to its options, one for each file interactively excluded.


        Start the synchronization in exclude-from mode.

        The original rsync command will be executed, but a file will be written
        with a list of the files interactively excluded, and an --exclude-from
        option will be prepended to the original command's options to read the
        exclude file.


        Start the synchronization in include mode.

        The original rsync command will be executed, but --include options will
        be prepended to its options, one for each file interactively included,
        terminated by an --exclude=* option.


        Start the synchronization in include-from mode.

        The original rsync command will be executed, but a file will be written
        with a list of the files interactively included, and an --include-from
        option will be prepended to the original command's options to read the
        include file.


        Start the synchronization in files-from mode.

        The original rsync command will be executed, but a file will be written
        with a list of the files interactively included, and an --files-from
        option will be prepended to the original command's options to read the
        created file.
        """
        try:
            pargs = self.parser.parse_args(args)
        except _m_forwarg.ForwargError:
            self.rootapp.messages.error(self.rootapp.messages.wrong_syntax)
            return False

        if self.rootapp.preview_needed:
            self.rootapp.messages.error(self.rootapp.messages.preview_needed)
            return False

        if not self.rootapp.pending_changes:
            self.rootapp.messages.error(
                                    self.rootapp.messages.transfer_no_changes)
            return False

        included_changes = []
        excluded_changes = []
        for change in self.rootapp.pending_changes:
            if change.included is True:
                included_changes.append(change)
            # There's also the None case, i.e. undecided
            elif change.included is False:
                excluded_changes.append(change)

        # TODO #31: This should also warn if some files are included, but their
        #       parent directories are not, resulting in the files actually
        #       being excluded
        if len(self.rootapp.pending_changes) - len(included_changes) - \
                len(excluded_changes) > 0:
            self.rootapp.messages.error(
                            self.rootapp.messages.transfer_selection_undecided)
            return False
        elif len(included_changes) == 0:
            self.rootapp.messages.error(
                                self.rootapp.messages.transfer_selection_null)
            return False

        modecheck = set(['exclude', 'exclude_from', 'include', 'include_from',
                         'files_from', 'checksum', 'checksum_from']) & \
            set(key for key, value in vars(pargs.namespace).items()
                if value is not None)
        if len(modecheck) == 0:
            # Choose the best method automatically
            if self.rootapp.cliargs.namespace.checksum:
                if len(included_changes) <= int(self.rootapp.configuration[
                                                        'max-inline-filters']):
                    mode = 'checksum'
                else:
                    mode = 'checksum_from'
            elif len(included_changes) < len(excluded_changes):
                if len(included_changes) <= int(self.rootapp.configuration[
                                                        'max-inline-filters']):
                    mode = 'include'
                else:
                    mode = 'include_from'
            else:
                if len(excluded_changes) <= int(self.rootapp.configuration[
                                                        'max-inline-filters']):
                    mode = 'exclude'
                else:
                    mode = 'exclude_from'
        elif len(modecheck) == 1:
            mode = modecheck.pop()
        else:
            self.rootapp.messages.error(
                                self.rootapp.messages.transfer_ambiguous_mode)
            return False

        if mode in ('checksum', 'checksum_from'):
            transferargs = self.rootapp.cliargs.filter_whitelist(groups=(
                                'shared', 'transfer-only',
                                'experimental', 'safe'))
        else:
            transferargs = self.rootapp.cliargs.filter_whitelist(groups=(
                                'shared', 'transfer-only', 'checksum',
                                'experimental', 'safe'))

        # TODO #17
        targs, file = {
            'exclude': self._exclude,
            'exclude_from': self._exclude_from,
            'include': self._include,
            'include_from': self._include_from,
            'files_from': self._files_from,
            'checksum': self._checksum,
            'checksum_from': self._checksum_from,
        }[mode](included_changes, excluded_changes, pargs, transferargs)

        if pargs.namespace.dry_run:
            targs.append('--dry-run')

        if pargs.namespace.view_only:
            print(' '.join(targs))
            if file and not pargs.namespace.keep_list:
                _m_os.remove(file)
        else:
            # Pressing Ctrl+c should normally terminate both rsync and syncere
            # TODO #18
            call = _m_subprocess.Popen(targs)
            call.wait()

            if file and not pargs.namespace.keep_list:
                _m_os.remove(file)

            self.rootapp.clear_preview()

            if call.returncode != 0:
                self.rootapp.messages.error(
                            self.rootapp.messages.rsync_error, call.returncode)
                if pargs.namespace.quit:
                    _m_sys.exit(call.returncode)
            elif pargs.namespace.quit:
                self.menu.break_loops(True)

    def _exclude(self, included_changes, excluded_changes, pargs,
                 transferargs):
        # TODO #24

        # Note that Popen already does all the necessary escaping on the
        # arguments
        excludes = []
        for change in excluded_changes:
            excludes.extend(['--exclude', change.sfilename])

        # Prepend, not append, excludes, since the original rsync command
        # may have other include/exclude/filter rules, and rsync stops at
        # the first match that it finds
        return (['rsync', *excludes, *transferargs], None)

    def _exclude_from(self, included_changes, excluded_changes, pargs,
                      transferargs):
        # Don't define a default file name in the const argument of the
        # --exclude-from option, e.g. const='./exclude-from', and then read it
        # here from there, because this method can also be executed when the
        # mode is chosen automatically because it hasn't been specified through
        # options, and max-inline-filters is exceeded, which would leave the
        # value of the option as None
        # TODO #23
        file = self.DEFAULT_EXCLUDE_FROM_FILE

        try:
            # Use 'w' instead of 'a' to make sure the file is empty
            filefrom = open(file, 'w')
        except OSError as exc:
            self.rootapp.messages.error(
                                file,
                                self.rootapp.messages.file_cannot_be_written,
                                exc.strerror)
        else:
            with filefrom:
                for change in excluded_changes:
                    filefrom.write(change.sfilename + '\n')

        # Prepend, not append, excludes, since the original rsync command
        # may have other include/exclude/filter rules, and rsync stops at
        # the first match that it finds
        return (['rsync', '--exclude-from', file, *transferargs],
                file)

    def _include(self, included_changes, excluded_changes, pargs,
                 transferargs):
        # TODO #24

        # Note that Popen already does all the necessary escaping on the
        # arguments
        includes = []
        for change in included_changes:
            includes.extend(['--include', change.sfilename])

        # Prepend, not append, includes, since the original rsync command
        # may have other include/exclude/filter rules, and rsync stops at
        # the first match that it finds
        return (['rsync', *includes, '--exclude', '*', *transferargs], None)

    def _include_from(self, included_changes, excluded_changes, pargs,
                      transferargs):
        # Don't define a default file name in the const argument of the
        # --exclude-from option, e.g. const='./exclude-from', and then read it
        # here from there, because this method can also be executed when the
        # mode is chosen automatically because it hasn't been specified through
        # options, and max-inline-filters is exceeded, which would leave the
        # value of the option as None
        # TODO #23
        file = self.DEFAULT_INCLUDE_FROM_FILE

        try:
            # Use 'w' instead of 'a' to make sure the file is empty
            filefrom = open(file, 'w')
        except OSError as exc:
            self.rootapp.messages.error(
                                file,
                                self.rootapp.messages.file_cannot_be_written,
                                exc.strerror)
        else:
            with filefrom:
                for change in included_changes:
                    filefrom.write(change.sfilename + '\n')

        # Prepend, not append, includes, since the original rsync command
        # may have other include/exclude/filter rules, and rsync stops at
        # the first match that it finds
        return (['rsync', '--include-from', file, '--exclude', '*',
                 *transferargs], file)

    def _files_from(self, included_changes, excluded_changes, pargs,
                    transferargs):
        # Don't define a default file name in the const argument of the
        # --exclude-from option, e.g. const='./exclude-from', and then read it
        # here from there, because this method can also be executed when the
        # mode is chosen automatically because it hasn't been specified through
        # options, and max-inline-filters is exceeded, which would leave the
        # value of the option as None
        # TODO #23
        file = self.DEFAULT_FILES_FROM_FILE

        try:
            # Use 'w' instead of 'a' to make sure the file is empty
            filefrom = open(file, 'w')
        except OSError as exc:
            self.rootapp.messages.error(
                                file,
                                self.rootapp.messages.file_cannot_be_written,
                                exc.strerror)
        else:
            with filefrom:
                for change in included_changes:
                    filefrom.write(change.sfilename + '\n')

        return (['rsync', '--files-from', file, *transferargs], file)

    def _checksum(self, included_changes, excluded_changes, pargs,
                  transferargs):
        # TODO #24

        # Note that Popen already does all the necessary escaping on the
        # arguments
        includes = []
        for change in included_changes:
            includes.extend(['--include', change.sfilename])

        # Prepend, not append, includes, since the original rsync command
        # may have other include/exclude/filter rules, and rsync stops at
        # the first match that it finds
        return (['rsync', *includes, '--exclude', '*', *transferargs,
                 '--ignore-times'], None)

    def _checksum_from(self, included_changes, excluded_changes, pargs,
                       transferargs):
        # Don't define a default file name in the const argument of the
        # --exclude-from option, e.g. const='./exclude-from', and then read it
        # here from there, because this method can also be executed when the
        # mode is chosen automatically because it hasn't been specified through
        # options, and max-inline-filters is exceeded, which would leave the
        # value of the option as None
        # TODO #23
        file = self.DEFAULT_INCLUDE_FROM_FILE

        try:
            # Use 'w' instead of 'a' to make sure the file is empty
            filefrom = open(file, 'w')
        except OSError as exc:
            self.rootapp.messages.error(
                                file,
                                self.rootapp.messages.file_cannot_be_written,
                                exc.strerror)
        else:
            with filefrom:
                for change in included_changes:
                    filefrom.write(change.sfilename + '\n')

        # Prepend, not append, includes, since the original rsync command
        # may have other include/exclude/filter rules, and rsync stops at
        # the first match that it finds
        return (['rsync', '--include-from', file, '--exclude', '*',
                 *transferargs, '--ignore-times'], file)


class MainMenu:
    def __init__(self, rootapp, test):
        """
        Type 'help <command>' for more information.
        Tab completion is available.

        {command_list}
        """
        self.rootapp = rootapp

        self.change_filter = _ChangeFilter(rootapp)

        # TODO #2: Introduce filters syntax in the specific 'help' messages of
        #          the commands that do support filters
        self.menu = _m_cmenu.RootMenu(
                    'syncere', helpfull=self.__init__, prompt=Prompt,
                    messages=self.rootapp.messages.cmenu)

        self.transfer = TransferCommand(rootapp, self.menu)

        _m_cmenu.Action(self.menu, 'preview', self.preview,
                        accepted_flags=['quit'])
        _m_cmenu.RunScript(self.menu, 'import', helpfull=self.import_)
        _m_cmenu.Action(self.menu, 'list', self.list_)
        _m_cmenu.Action(self.menu, 'details', self.details)
        ConfigMenu(self.menu, 'config', self.menu, rootapp)
        _m_cmenu.Action(self.menu, 'include', self.include)
        # Don't use an Alias because this shouldn't be editable
        _m_cmenu.Action(self.menu, Messages.ICON_CHANGE_INCLUDED, self.include,
                        helpshort='Built-in alias for <include>')
        _m_cmenu.Action(self.menu, 'exclude', self.exclude)
        # Don't use an Alias because this shouldn't be editable
        _m_cmenu.Action(self.menu, Messages.ICON_CHANGE_EXCLUDED, self.exclude,
                        helpshort='Built-in alias for <exclude>')
        _m_cmenu.Action(self.menu, 'reset', self.reset)
        # Don't use an Alias because this shouldn't be editable
        _m_cmenu.Action(self.menu, Messages.ICON_CHANGE_UNDECIDED, self.reset,
                        helpshort='Built-in alias for <reset>')
        _m_cmenu.Action(self.menu, 'transfer', self.transfer.execute)
        if test:
            _m_cmenu.ResumeTest(self.menu, 'resume-test',
                                helpfull=self.resume_test)
        _m_cmenu.Help(self.menu, 'help', helpfull=self.help)
        _m_cmenu.Quit(self.menu, 'quit', helpfull=self.quit)

    def preview(self, *args):
        """
        Launch the preview rsync command.

        Create or refresh the list of pending changes.
        If a 'quit' argument is given, syncere will quit if no changes are
        found.
        """
        quit = False
        if len(args) == 1 and args[0] == 'quit':
            quit = True
        elif len(args) > 0:
            self.rootapp.messages.error(
                        self.rootapp.messages.unrecognized_arguments, *args)
            return False

        # If experimental is disabled and some of its options have been
        # specified, the program has already exited in _check_arguments
        previewargs = self.rootapp.cliargs.filter_whitelist(groups=(
                                'shared', 'checksum', 'experimental', 'safe'))

        # Pressing Ctrl+c should normally terminate both rsync and syncere
        call = _m_subprocess.Popen(['rsync', *previewargs,
                                    '--dry-run',
                                    '--info={}'.format(
                                                    self.rootapp.configuration[
                                                        'preview-info-flags']),
                                    '--out-format='
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
        # According to the docs, Popen.communicate reads from stdout and
        # buffers the data in memory, so there shouldn't be problems with long
        # rsync outputs
        # TODO #12 #22
        self.stdout = call.communicate()[0]

        if call.returncode != 0:
            _m_sys.exit(call.returncode)

        self.rootapp.pending_changes.clear()

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
                    self.rootapp.pending_changes.append(Change(
                                        len(self.rootapp.pending_changes) + 1,
                                        *match.groups()))
                else:
                    raise exceptions.UnrecognizedItemizedChangeError(line)
            else:
                # TODO #28: Allow suppressing these lines
                print(line)

        self.rootapp.preview_needed = False

        if not self.rootapp.pending_changes:
            self.rootapp.messages.info(self.rootapp.messages.nothing_to_do)
            if quit:
                self.menu.break_loops(True)

    def import_(self, *args):
        """
        Run a series of commands from a script.
        """
        pass

    def list_(self, *args):
        """
        List a selection of pending changes.
        """
        changes = self.change_filter.select(*args)
        if changes:
            width = len(str(changes[-1].id_))
            # TODO #10
            for change in changes:
                print('[{0}] {1} {2} {3}'.format(
                    str(change.id_).rjust(width),
                    self.rootapp.messages.status_to_icon[change.included],
                    ' '.join(change.get_summary()),
                    ''.join((change.sfilename, change.link))))

    def details(self, *args):
        """
        List a selection of pending changes with details.
        """
        changes = self.change_filter.select(*args)
        if changes:
            rows = []
            maxw_id = 0
            maxw_uid = 0
            maxw_gid = 0
            maxw_size = 0
            # TODO #10
            for change in changes:
                row = (str(change.id_), self.rootapp.messages.status_to_icon[
                                                            change.included],
                       *change.get_details(),
                       ''.join((change.sfilename, change.link)))
                rows.append(row)
                if len(row[0]) > maxw_id:
                    maxw_id = len(row[0])
                if len(row[4]) > maxw_uid:
                    maxw_uid = len(row[4])
                if len(row[5]) > maxw_gid:
                    maxw_gid = len(row[5])
                if len(row[6]) > maxw_size:
                    maxw_size = len(row[6])
            for row in rows:
                print(' '.join(('[{}]'.format(row[0].rjust(maxw_id)),
                      row[1], row[2], row[3], row[4].rjust(maxw_uid),
                      row[5].rjust(maxw_gid), row[6].rjust(maxw_size),
                      row[7], row[8])))

    def include(self, *args):
        """
        Include (confirm) the changes in the synchronization.
        """
        # TODO #31: This should also ask to include all the ancestor
        #       directories, if they aren't included already
        for change in self.change_filter.select(*args):
            change.include()

    def exclude(self, *args):
        """
        Exclude (except) the changes from the synchronization.
        """
        # TODO #31: If this is a directory, this should also ask to exclude all
        #       the descendant files and directories, if they are still
        #       included
        for change in self.change_filter.select(*args):
            change.exclude()

    def reset(self, *args):
        """
        Reset the changes to an undecided status.
        """
        # TODO #31: If the path was included and was a directory, this should
        #       ask to reset all the descendants; if the path was excluded,
        #       this should ask to reset all the ancestor directories
        for change in self.change_filter.select(*args):
            change.reset()

    def resume_test(self):
        """
        Resume the automatic execution of test commands.
        """
        pass

    def help(self):
        """
        Show this help screen.

        Type 'help <command>' for more information on a specific command.
        Tab completion is always available in the menus.
        """
        pass

    def quit(self):
        """
        Quit syncere without synchronizing anything.
        """
        pass


class ConfigMenu:
    def __init__(self, parent, name, rootmenu, rootapp):
        """
        Open the configuration menu or execute a configuration command.

        {command_list}
        """
        self.rootapp = rootapp

        menu = _m_cmenu.SubMenu(parent, name, helpfull=self.__init__)
        _m_cmenu.AliasConfig(menu, 'alias', rootmenu, helpfull=self.alias)
        for option in rootapp.configuration:
            _m_cmenu.LineEditorDefault(menu, option, self.value_in(option),
                                       self.value_out(option),
                                       self.value_restore(option))
        _m_cmenu.Choice(menu, 'colors', "Use colors? [Y/n] ", self.colors)
        _m_cmenu.Help(menu, 'help', helpfull=self.help)
        _m_cmenu.Exit(menu, 'exit', helpfull=self.exit)

    def alias(self, *args):
        """
        Manage command aliases.

        Syntax: alias set alias_name "command arg arg ..."
        Syntax: alias unset alias_name
        Syntax: alias unset-all
        """
        pass

    def value_in(self, option):
        def inner():
            """
            Edit the current option's value.
            """
            return self.rootapp.configuration[option]
        return inner

    def value_out(self, option):
        def inner(string):
            self.rootapp.configuration[option] = string
        return inner

    def value_restore(self, option):
        def inner():
            self.rootapp.configuration[option] = \
                self.rootapp.DEFAULT_CONFIG[option]
        return inner

    def colors(self, choice):
        """
        Choose whether to use colors in the program's output.
        """
        if choice is False:
            self.rootapp.messages.disable_colors()
        else:
            self.rootapp.messages.enable_colors()

    def help(self):
        """
        Show this help screen.

        Type 'help <command>' for more information on a specific command.
        Tab completion is always available in the menus.
        """
        pass

    def exit(self):
        """
        Go back to the parent configuration menu.
        """
        pass

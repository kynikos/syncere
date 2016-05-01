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

import subprocess as _m_subprocess
import re as _m_re

from .cliargs import CLIArgs
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
    VERSION_NUMBER = '0.1.0'
    VERSION_DATE = '2016-04-17'
    DEFAULT_STARTUP_COMMANDS = ['preview quit', 'list']
    DEFAULT_CONFIG = {
        'preview-info-flags': 'backup4,copy4,del4,flist4,misc4,mount4,name1,'
                              'remove4,symsafe4',
    }

    def __init__(self, cliargs=None, commands=[], test=False):
        self._parse_arguments(cliargs)
        self.configuration = self.DEFAULT_CONFIG.copy()
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

        # If experimental is disabled and some of its options have been
        # specified, the program has already exited in _check_arguments
        self.previewargs = self.cliargs.filter_whitelist(groups=(
                                'shared', 'optimized', 'experimental', 'safe'))
        self.transferargs = self.cliargs.filter_whitelist(groups=(
                                'shared', 'transfer-only', 'optimized',
                                'experimental', 'safe'))

    def _start_interface(self, commands, test):
        # TODO #4 #30 #31 #33 #34 #35 #56
        self.mainmenu = MainMenu(self, test).menu

        # When testing, we don't want the original DEFAULT_STARTUP_COMMANDS to
        # be modified directly by the tests, so clone it
        commands = commands or self.cliargs.namespace.commands or \
            self.DEFAULT_STARTUP_COMMANDS[:]
        # This can raise _m_cmenu.InsufficientTestCommands: if testing, the
        # last command should be one that quits syncere
        self.mainmenu.loop(intro="Type 'help' to list available commands\n",
                           cmdlines=commands, test=test)


class MainMenu:
    def __init__(self, rootapp, test):
        """
        Type 'help <command>' for more information.
        Tab completion is available.

        {command_list}
        """
        self.rootapp = rootapp

        # TODO #4: Introduce filters syntax in the specific 'help' messages of
        #          the commands that do support filters
        self.menu = _m_cmenu.RootMenu('syncere', helpfull=self.__init__)
        _m_cmenu.Action(self.menu, 'preview', self.preview)
        _m_cmenu.RunScript(self.menu, 'import', helpfull=self.import_)
        _m_cmenu.Action(self.menu, 'list', self.list_)
        _m_cmenu.Action(self.menu, 'details', self.details)
        ConfigMenu(self.menu, 'config', self.menu, rootapp)
        _m_cmenu.Action(self.menu, 'include', self.include)
        # Don't use an Alias because this shouldn't be editable
        _m_cmenu.Action(self.menu, '>', self.include,
                        helpshort='Built-in alias for <include>')
        _m_cmenu.Action(self.menu, 'exclude', self.exclude)
        # Don't use an Alias because this shouldn't be editable
        _m_cmenu.Action(self.menu, '!', self.exclude,
                        helpshort='Built-in alias for <exclude>')
        _m_cmenu.Action(self.menu, 'reset', self.reset)
        # Don't use an Alias because this shouldn't be editable
        _m_cmenu.Action(self.menu, '?', self.reset,
                        helpshort='Built-in alias for <reset>')
        TransferMenu(self.menu, 'transfer', rootapp)
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
        if len(args) > 0:
            if args[0] == 'quit':
                quit = True
            else:
                print('Unrecognized arguments:', *args)
                return False

        # TODO #14
        call = _m_subprocess.Popen(['rsync', *self.rootapp.previewargs,
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
        # TODO #12 #13 #22
        self.stdout = call.communicate()[0]

        if call.returncode != 0:
            # TODO #15: Use sys.exit(call.returncode)?
            raise exceptions.RsyncError(call.returncode)

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

        if not self.rootapp.pending_changes:
            # TODO #21
            print('Nothing to do')
            if quit:
                self.menu.break_loops(True)

    def import_(self, *args):
        """
        Run a series of commands from a script.
        """
        pass

    def _select_changes(self, *args):
        if not self.rootapp.pending_changes:
            print('There are no pending changes')
            return self.rootapp.pending_changes

        rawsel = ' '.join(args)

        if rawsel in ('', '*'):
            return self.rootapp.pending_changes

        changes = []
        lsel = rawsel.split(',')
        for isel in lsel:
            rsel = isel.split('-')

            if len(rsel) == 1:
                try:
                    id0 = self._get_0_based_id(isel)
                    change = self.rootapp.pending_changes[id0]
                except (ValueError, IndexError):
                    print('Unrecognized selection')
                    return []
                else:
                    changes.append(change)

            elif len(rsel) == 2:
                try:
                    ids, ide = [self._get_0_based_id(rid) for rid in rsel]
                except ValueError:
                    print('Unrecognized selection')
                    return []
                else:
                    for change in self.rootapp.pending_changes[ids:ide + 1]:
                        changes.append(change)

            else:
                print('Unrecognized selection')
                return []

        if not changes:
            print('No changes selected')

        return changes

    @staticmethod
    def _get_0_based_id(selid):
        # This line itself can raise ValueError
        id0 = int(selid) - 1
        if id0 < 0:
            raise ValueError()
        return id0

    def list_(self, *args):
        """
        List a selection of pending changes.
        """
        changes = self._select_changes(*args)
        if changes:
            print()
            width = len(str(changes[-1].id_))
            # TODO #10 #11
            for change in changes:
                print(change.get_summary(width))
            print()

    def details(self, *args):
        """
        List a selection of pending changes with details.
        """
        changes = self._select_changes(*args)
        if changes:
            print()
            width = len(str(changes[-1].id_))
            # TODO #10 #11
            for change in changes:
                print(change.get_summary(width))
                print(change.get_details(width))
            print()

    def include(self, *args):
        """
        Include (confirm) the changes in the synchronization.
        """
        # TODO #31: This should also ask to include all the ancestor
        #       directories, if they aren't included already
        for change in self._select_changes(*args):
            change.include()

    def exclude(self, *args):
        """
        Exclude (except) the changes from the synchronization.
        """
        # TODO #31: If this is a directory, this should also ask to exclude all
        #       the descendant files and directories, if they are still
        #       included
        for change in self._select_changes(*args):
            change.exclude()

    def reset(self, *args):
        """
        Reset the changes to an undecided status.
        """
        # TODO #31: If the path was included and was a directory, this should
        #       ask to reset all the descendants; if the path was excluded,
        #       this should ask to reset all the ancestor directories
        for change in self._select_changes(*args):
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
        menu = _m_cmenu.SubMenu(parent, name, helpfull=self.__init__)
        AliasMenu(menu, 'alias', rootmenu)
        for option in rootapp.configuration:
            ConfigOptionMenu(menu, option, rootapp)
        _m_cmenu.Help(menu, 'help', helpfull=self.help)
        _m_cmenu.Exit(menu, 'exit', helpfull=self.exit)

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


class AliasMenu:
    def __init__(self, parent, name, rootmenu):
        """
        Open the alias menu or execute an alias configuration command.

        {command_list}
        """
        menu = _m_cmenu.SubMenu(parent, name, helpfull=self.__init__)
        _m_cmenu.AliasSet(menu, 'set', rootmenu, helpfull=self.set_)
        _m_cmenu.AliasUnset(menu, 'unset', rootmenu, helpfull=self.unset)
        _m_cmenu.AliasUnsetAll(menu, 'unset-all', rootmenu,
                               helpfull=self.unset_all)
        _m_cmenu.Help(menu, 'help', helpfull=self.help)
        _m_cmenu.Exit(menu, 'exit', helpfull=self.exit)

    def set_(self, *args):
        """
        Set a command alias.

        Syntax: set alias_name "command arg arg ..."
        """
        pass

    def unset(self, *args):
        """
        Unset a command alias.

        Syntax: unset alias_name
        """
        pass

    def unset_all(self, *args):
        """
        Unset all command aliases.
        """
        pass

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


class ConfigOptionMenu:
    def __init__(self, parent, name, rootapp):
        """
        Open the configuration option's menu or execute an option command.

        {command_list}
        """
        self.name = name
        self.rootapp = rootapp

        menu = _m_cmenu.SubMenu(parent, name, helpfull=self.__init__)
        _m_cmenu.LineEditor(menu, 'change', self.value_in, self.value_out)
        _m_cmenu.Action(menu, 'default', self.default)
        _m_cmenu.Help(menu, 'help', helpfull=self.help)
        _m_cmenu.Exit(menu, 'exit', helpfull=self.exit)

    def value_in(self):
        """
        Edit the current option's value.
        """
        return self.rootapp.configuration[self.name]

    def value_out(self, string):
        self.rootapp.configuration[self.name] = string

    def default(self, *args):
        """
        Restore the default option's value.
        """
        if len(args) > 0:
            print('Unrecognized arguments')
            return False
        self.rootapp.configuration[self.name] = self.rootapp.DEFAULT_CONFIG[
                                                                    self.name]

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


class TransferMenu:
    def __init__(self, parent, name, rootapp):
        """
        Open the transfer menu or execute a transfer command.

        {command_list}
        """
        self.rootapp = rootapp

        # TODO #17
        menu = _m_cmenu.SubMenu(parent, name, helpfull=self.__init__)
        _m_cmenu.Action(menu, 'exclude', self.exclude)
        _m_cmenu.Action(menu, 'exclude-from', self.exclude_from)
        _m_cmenu.Action(menu, 'include', self.include)
        _m_cmenu.Action(menu, 'include-from', self.include_from)
        _m_cmenu.Action(menu, 'files-from', self.files_from)
        _m_cmenu.Help(menu, 'help', helpfull=self.help)
        _m_cmenu.Exit(menu, 'exit', helpfull=self.exit)

    def _pre_transfer_checks(self, *args):
        # TODO #31: This should also warn if some files are included, but their
        #       parent directories are not, resulting in the files actually
        #       being excluded
        if len(args) > 0:
            print('No arguments are accepted')
            return False
        for change in self.rootapp.pending_changes:
            if change.included not in (True, False):
                print('There are still undecided changes')
                return False

    def _transfer(self, *args):
        # TODO #14 #18
        call = _m_subprocess.Popen(args)

        # TODO #19 #23 (otherwise maybe calling 'wait' is unneeded?)
        call.wait()

    def exclude(self, *args):
        """
        Start the synchronization in exclude mode.

        The original rsync command will be executed, but --exclude options will
        be prepended to its options, one for each file interactively excluded.
        """
        if self._pre_transfer_checks(*args) is not False:
            # TODO #24

            # Note that Popen already does all the necessary escaping on the
            # arguments
            excludes = []
            for change in self.rootapp.pending_changes:
                if not change.included:
                    excludes.extend(['--exclude', change.sfilename])

            # Prepend, not append, excludes, since the original rsync command
            # may # have other include/exclude/filter rules, and rsync stops at
            # the first match that it finds
            self._transfer('rsync', *excludes, *self.rootapp.transferargs)

    def exclude_from(self, *args):
        """
        Start the synchronization in exclude-from mode.

        The original rsync command will be executed, but a file will be written
        with a list of the files interactively excluded, and an --exclude-from
        option will be prepended to the original command's options to read the
        exclude file.
        """
        if self._pre_transfer_checks(*args) is not False:
            # TODO #23
            FILE = './exclude_from'

            with open(FILE, 'w'):
                # First make sure the file is empty
                pass
            with open(FILE, 'a') as filefrom:
                for change in self.rootapp.pending_changes:
                    if not change.included:
                        filefrom.write(change.sfilename + '\n')

            # Prepend, not append, excludes, since the original rsync command
            # may have other include/exclude/filter rules, and rsync stops at
            # the first match that it finds
            self._transfer('rsync', '--exclude-from', FILE,
                           *self.rootapp.transferargs)

    def include(self, *args):
        """
        Start the synchronization in include mode.

        The original rsync command will be executed, but --include options will
        be prepended to its options, one for each file interactively included,
        terminated by an --exclude=* option.
        """
        if self._pre_transfer_checks(*args) is not False:
            # TODO #24

            # Note that Popen already does all the necessary escaping on the
            # arguments
            includes = []
            for change in self.rootapp.pending_changes:
                if change.included:
                    includes.extend(['--include', change.sfilename])

            # Prepend, not append, includes, since the original rsync command
            # may have other include/exclude/filter rules, and rsync stops at
            # the first match that it finds
            self._transfer('rsync', *includes, '--exclude', '*',
                           *self.rootapp.transferargs)

    def include_from(self, *args):
        """
        Start the synchronization in include-from mode.

        The original rsync command will be executed, but a file will be written
        with a list of the files interactively included, and an --include-from
        option will be prepended to the original command's options to read the
        include file.
        """
        if self._pre_transfer_checks(*args) is not False:
            # TODO #23
            FILE = './include_from'

            with open(FILE, 'w'):
                # First make sure the file is empty
                pass
            with open(FILE, 'a') as filefrom:
                for change in self.rootapp.pending_changes:
                    if change.included:
                        filefrom.write(change.sfilename + '\n')

            # Prepend, not append, includes, since the original rsync command
            # may # have other include/exclude/filter rules, and rsync stops at
            # the first match that it finds
            self._transfer('rsync', '--include-from', FILE, '--exclude', '*',
                           *self.rootapp.transferargs)

    def files_from(self, *args):
        """
        Start the synchronization in files-from mode.

        The original rsync command will be executed, but a file will be written
        with a list of the files interactively included, and an --files-from
        option will be prepended to the original command's options to read the
        created file.
        """
        if self._pre_transfer_checks(*args) is not False:
            # TODO #23
            FILE = './files_from'

            with open(FILE, 'w'):
                # First make sure the file is empty
                pass
            with open(FILE, 'a') as filefrom:
                for change in self.rootapp.pending_changes:
                    if change.included:
                        filefrom.write(change.sfilename + '\n')

            self._transfer('rsync', '--files-from', FILE,
                           *self.rootapp.transferargs)

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

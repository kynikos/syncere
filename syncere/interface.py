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

from . import exceptions

try:
    import cmenu as _m_cmenu
except ImportError:
    try:
        from . import cmenu as _m_cmenu
    except ImportError as excinfo:
        raise exceptions.DependencyError()


class Configuration:
    # TODO ***************************************************************************
    pass


class Interface:
    def __init__(self, pending_changes):
        # TODO #4 #25 #30 #31 #33 #34 #35 #56
        self.pending_changes = pending_changes
        self.mainmenu = MainMenu(self).menu
        self.transfer_mode = None

    def start(self, cliargs, commands, test):
        self.mainmenu.run_line('list')
        print("Type 'help' to list available commands\n")

        commands = commands or cliargs.namespace.commands
        if test:
            # TODO #60
            # This can raise _m_cmenu.InsufficientTestCommands: if testing, the
            # last command should be 'transfer' or 'quit'
            self.mainmenu.loop_test(commands)
        else:
            self.mainmenu.loop_lines(commands)
            self.mainmenu.loop_input()


class MainMenu:
    def __init__(self, interface):
        """
        Type 'help <command>' for more information. Tab completion is
        available.

        {command_list}
        """
        self.interface = interface

        # TODO #4: Introduce filters syntax in the specific 'help' messages of
        #          the commands that do support filters
        self.menu = _m_cmenu.RootMenu('syncere', helpfull=self.__init__)
        _m_cmenu.RunScript(self.menu, 'import', helpfull=self.import_)
        _m_cmenu.Action(self.menu, 'list', self.list_)
        _m_cmenu.Action(self.menu, 'details', self.details)
        ConfigMenu(self.menu, 'config', self.menu)
        _m_cmenu.Action(self.menu, 'include', self.include)
        # Don't use an Alias because this shouldn't be editable
        _m_cmenu.Action(self.menu, '>', self.include)
        _m_cmenu.Action(self.menu, 'exclude', self.exclude)
        # Don't use an Alias because this shouldn't be editable
        _m_cmenu.Action(self.menu, '!', self.exclude)
        _m_cmenu.Action(self.menu, 'reset', self.reset)
        # Don't use an Alias because this shouldn't be editable
        _m_cmenu.Action(self.menu, '?', self.reset)
        TransferMenu(self.menu, 'transfer', interface)
        _m_cmenu.Help(self.menu, 'help', helpfull=self.help)
        _m_cmenu.Quit(self.menu, 'quit', helpfull=self.quit)

    def _select_changes(self, *args):
        rawsel = ' '.join(args)

        if rawsel in ('', '*'):
            return self.interface.pending_changes

        changes = []
        lsel = rawsel.split(',')
        for isel in lsel:
            rsel = isel.split('-')

            if len(rsel) == 1:
                try:
                    id0 = self._get_0_based_id(isel)
                    change = self.interface.pending_changes[id0]
                except (ValueError, IndexError):
                    print('Unrecognized selection')
                else:
                    changes.append(change)

            elif len(rsel) == 2:
                try:
                    ids, ide = [self._get_0_based_id(rid) for rid in rsel]
                except ValueError:
                    print('Unrecognized selection')
                else:
                    for change in self.interface.pending_changes[ids:ide + 1]:
                        changes.append(change)

            else:
                print('Unrecognized selection')

        return changes

    @staticmethod
    def _get_0_based_id(selid):
        # This line itself can raise ValueError
        id0 = int(selid) - 1
        if id0 < 0:
            raise ValueError()
        return id0

    def import_(self, *args):
        """
        Run a series of commands from a script.
        """
        pass

    def list_(self, *args):
        """
        List a selection of pending changes.
        """
        print()

        changes = self._select_changes(*args)
        width = len(str(changes[-1].id_))

        # TODO #10 #11
        for change in changes:
            print(change.get_summary(width))

        print()

    def details(self, *args):
        """
        List a selection of pending changes with details.
        """
        print()

        changes = self._select_changes(*args)
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
        Exclude (cancel) the changes from the synchronization.
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
    def __init__(self, parent, name, rootmenu):
        """
        Open the configuration menu or execute a configuration command.

        {command_list}
        """
        menu = _m_cmenu.SubMenu(parent, name, helpfull=self.__init__)
        AliasMenu(menu, 'alias', rootmenu)
        _m_cmenu.LineEditor(menu, 'filter', self.filter_in, self.filter_out)
        _m_cmenu.Help(menu, 'help', helpfull=self.help)
        _m_cmenu.Exit(menu, 'exit', helpfull=self.exit)

    def filter_in(self):
        """
        Edit the current list filter.
        """
        # TODO: ************************************************************************
        return 'foobar'

    def filter_out(self, string):
        # TODO: Hide files that are not going to be transferred because ***************
        #       identical at the source and destination.
        #       Predefined rule: _m_re.match('\.[fdLDS] {9}$', match.group(1))
        # FIXME
        print(string)

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


class TransferMenu:
    def __init__(self, parent, name, interface):
        """
        Open the transfer menu or execute a transfer command and quit syncere.

        {command_list}
        """
        self.interface = interface

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
        for change in self.interface.pending_changes:
            if change.included not in (True, False):
                print('There are still undecided changes')
                return False

    def exclude(self, *args):
        """
        Start the synchronization in exclude mode, then quit syncere.

        The original rsync command will be executed, but --exclude options will
        be prepended to its options, one for each file interactively excluded.
        """
        if self._pre_transfer_checks(*args) is not False:
            self.interface.transfer_mode = 'exclude'
            raise self.interface.mainmenu.EndLoops(2)

    def exclude_from(self, *args):
        """
        Start the synchronization in exclude-from mode, then quit syncere.

        The original rsync command will be executed, but a file will be written
        with a list of the files interactively excluded, and an --exclude-from
        option will be prepended to the original command's options to read the
        exclude file.
        """
        if self._pre_transfer_checks(*args) is not False:
            self.interface.transfer_mode = 'exclude-from'
            raise self.interface.mainmenu.EndLoops(2)

    def include(self, *args):
        """
        Start the synchronization in include mode, then quit syncere.

        The original rsync command will be executed, but --include options will
        be prepended to its options, one for each file interactively included,
        terminated by an --exclude=* option.
        """
        if self._pre_transfer_checks(*args) is not False:
            self.interface.transfer_mode = 'include'
            raise self.interface.mainmenu.EndLoops(2)

    def include_from(self, *args):
        """
        Start the synchronization in include-from mode, then quit syncere.

        The original rsync command will be executed, but a file will be written
        with a list of the files interactively included, and an --include-from
        option will be prepended to the original command's options to read the
        include file.
        """
        if self._pre_transfer_checks(*args) is not False:
            self.interface.transfer_mode = 'include-from'
            raise self.interface.mainmenu.EndLoops(2)

    def files_from(self, *args):
        """
        Start the synchronization in files-from mode, then quit syncere.

        The original rsync command will be executed, but a file will be written
        with a list of the files interactively included, and an --files-from
        option will be prepended to the original command's options to read the
        created file.
        """
        if self._pre_transfer_checks(*args) is not False:
            self.interface.transfer_mode = 'files-from'
            raise self.interface.mainmenu.EndLoops(2)

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

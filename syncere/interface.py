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
from collections import OrderedDict
from inspect import getdoc as DOC

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
        self.mainmenu = MainMenu(pending_changes).menu

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
    def __init__(self, pending_changes):
        """
        Type 'help <command>' for more information. Tab completion is
        available.
        """
        self.pending_changes = pending_changes

        self.menu = _m_cmenu.RootMenu('syncere', DOC(self.__init__))
        _m_cmenu.Action(self.menu, 'import', self.import_, DOC(self.import_))
        _m_cmenu.Action(self.menu, 'list', self.list_, DOC(self.list_))
        _m_cmenu.Action(self.menu, 'details', self.details, DOC(self.details))
        ConfigMenu(self.menu, 'config')
        _m_cmenu.Action(self.menu, 'include', self.include, DOC(self.include))
        _m_cmenu.Alias(self.menu, '>', 'include')
        _m_cmenu.Action(self.menu, 'exclude', self.exclude, DOC(self.exclude))
        _m_cmenu.Alias(self.menu, '!', 'exclude')
        _m_cmenu.Action(self.menu, 'reset', self.reset, DOC(self.reset))
        _m_cmenu.Alias(self.menu, '?', 'reset')
        _m_cmenu.Action(self.menu, 'transfer', self.transfer,
                        DOC(self.transfer))
        _m_cmenu.Help(self.menu, 'help', DOC(self.help))
        _m_cmenu.Action(self.menu, 'quit', self.quit, DOC(self.quit))

    def _select_changes(self, *args):
        # TODO: Is this safe? ************************************************************
        rawsel = ' '.join(args)

        if rawsel in ('', '*'):
            return self.pending_changes

        changes = []
        lsel = rawsel.split(',')
        for isel in lsel:
            rsel = isel.split('-')

            if len(rsel) == 1:
                try:
                    id0 = self._get_0_based_id(isel)
                    change = self.pending_changes[id0]
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
                    for change in self.pending_changes[ids:ide + 1]:
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
        # TODO: Check args len ******************************************************
        with open(*args, 'r') as script:
            for line in script:
                self.onecmd(line)

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

        return False

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

        return False

    def include(self, *args):
        """
        Include (confirm) the changes in the synchronization.
        """
        # TODO #31: This should also ask to include all the ancestor
        #       directories, if they aren't included already
        for change in self._select_changes(*args):
            change.include()
        return False

    def exclude(self, *args):
        """
        Exclude (cancel) the changes from the synchronization.
        """
        # TODO #31: If this is a directory, this should also ask to exclude all
        #       the descendant files and directories, if they are still
        #       included
        for change in self._select_changes(*args):
            change.exclude()
        return False

    def reset(self, *args):
        """
        Reset the changes to an undecided status.
        """
        # TODO #31: If the path was included and was a directory, this should
        #       ask to reset all the descendants; if the path was excluded,
        #       this should ask to reset all the ancestor directories
        for change in self._select_changes(*args):
            change.reset()
        return False

    def transfer(self, *args):
        """
        Start the synchronization, then quit syncere.
        """
        # TODO: Allow setting the mode, or use a submenu *****************************************
        TRANSFER_MODES = OrderedDict((
            # The first item is considered the default mode
            ('e', 'exclude'),
            ('ef', 'exclude-from'),
            ('i', 'include'),
            ('if', 'include-from'),
            ('ff', 'files-from'),
        ))
        # TODO #31: This should also warn if some files are included, but their
        #       parent directories are not, resulting in the files actually
        #       being excluded
        for change in self.pending_changes:
            if change.included not in (True, False):
                print('There are still undecided changes')
                return False
        if not args:
            self.transfer_mode = tuple(TRANSFER_MODES.values())[0]
        elif len(args) == 1:
            try:
                self.transfer_mode = self.TRANSFER_MODES[args[0]]
            except KeyError:
                print('Unrecognized transfer mode')
                return False
        else:
            print('Unrecognized transfer mode')
            return False
        return True

    def help(self):
        """
        Show this help screen.

        Type 'help <command>' for more information on a specific command.
        Tab completion is always available in the menus.
        """
        pass
        # TODO #4: Briefly introduce filters syntax
        #          Or maybe do it in the specific 'command help' menus of
        #          the commands that do support filters
        print("""Filters syntax:
        TODO

Aliases:""")
        # TODO: List aliases in a separate table? *********************************

    def quit(self, *args):
        """
        Quit syncere without synchronizing anything.
        """
        # TODO: Make a preset action in typein.cmenu *********************************
        if not args:
            _m_sys.exit(0)
        # TODO: error doesn't exist anymore ******************************************
        self.error(*args)


class ConfigMenu:
    def __init__(self, parent, name):
        """
        Open the configuration menu or execute a configuration command.
        """
        menu = _m_cmenu.SubMenu(parent, name, DOC(self.__init__))
        _m_cmenu.Action(menu, 'alias', self.alias, DOC(self.alias))
        _m_cmenu.Action(menu, 'unalias', self.unalias, DOC(self.unalias))
        _m_cmenu.Action(menu, 'unalias-all', self.unalias_all,
                        DOC(self.unalias_all))
        _m_cmenu.Action(menu, 'filter', self.filter_, DOC(self.filter_))
        _m_cmenu.Help(menu, 'help', DOC(self.help))
        _m_cmenu.Action(menu, 'exit', self.exit, DOC(self.exit))

    def alias(self, *args):
        """
        Set a command alias.
        """
        # TODO Check that it's not overriding a built-in command ************************
        pass

    def unalias(self, *args):
        """
        Unset a command alias.
        """
        # TODO *************************************************************************
        pass

    def unalias_all(self, *args):
        """
        Unset all command aliases.
        """
        # TODO *************************************************************************
        pass

    def filter_(self, *args):
        """
        Edit the current list filter.
        """
        # TODO: Hide files that are not going to be transferred because ***************
        #       identical at the source and destination.
        #       Predefined rule: _m_re.match('\.[fdLDS] {9}$', match.group(1))
        print('filter', *args)
        # From http://stackoverflow.com/a/2533142/645498
        _m_readline.set_startup_hook(lambda: _m_readline.insert_text('prefill'))
        try:
            input()
        finally:
            _m_readline.set_startup_hook()
        return False

    def help(self):
        """
        Show this help screen.

        Type 'help <command>' for more information on a specific command.
        Tab completion is always available in the menus.
        """
        pass

    def exit(self, *args):
        """
        Go back to the parent configuration menu.
        """
        # TODO: Make a preset action in typein.cmenu *********************************
        if not args:
            return True
        # TODO: error doesn't exist anymore ******************************************
        self.error(*args)

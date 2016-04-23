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

from . import exceptions

try:
    import typein as _m_typein
except ImportError:
    try:
        from . import typein as _m_typein
    except ImportError as excinfo:
        raise exceptions.DependencyError()


class Configuration:
    # There's no point in making separate aliases for submenus like ConfigMenu
    # *Warning:* if some built-in commands are overridden here, no warning is
    #            issued, unlike when setting new aliases interactively!
    # End the commands with a space next to the aliases that should allow
    # the arguments to start without a separating space
    aliases = {
        '>': 'include ',
        '!': 'exclude ',
        '?': 'reset ',
        'q': 'quit ',
    }


class _Menu(_m_cmd.Cmd):
    empty = "Type 'help' to list available commands"

    def emptyline(self):
        # Override this method, otherwise the last non-empty command entered
        # is repeated by default
        print(self.empty)

    def error(self, line):
        # This method in practice does the job that normally 'default' does in
        # cmd.Cmd, but 'default' is used to find aliases in this case
        # There's no point in rewriting the command in the error message, the
        # bad command is just above next to the prompt
        print("Unrecognized command")
        self.emptyline()

    def do_help(self, args):
        """
        Show this help screen.

        Type 'help <command>' for more information on a specific command.
        Tab completion is always available in the menus.
        """
        if args:
            super().do_help(args)
        else:
            print("""
Type 'help <command>' for more information. Tab completion is available.
""")

            table = OrderedDict()
            for attr in dir(self):
                if attr[:3] == 'do_':
                    table[attr[3:]] = _m_inspect.getdoc(getattr(self, attr)
                                                        ).split('\n', 1)[0]
            width = max(len(command) for command in table)
            for command in table:
                print('        {}    {}'.format(command.ljust(width),
                                                table[command]))

            try:
                print(self.doc_notes)
            except AttributeError:
                print()


class MainMenu(_Menu):
    intro = _Menu.empty + '\n'
    prompt = '(syncere) '

    def __init__(self, pending_changes):
        # TODO #4 #25 #30 #31 #33 #34 #35 #56
        super().__init__()
        self.pending_changes = pending_changes
        self.configuration = Configuration()
        self.configmenu = ConfigMenu()

    def start_loop(self, cliargs, commands, test):
        commands = commands or cliargs.namespace.commands
        self.onecmd('list')
        for command in commands:
            # TODO #60
            print(self.prompt, command, sep='')
            if self.onecmd(command) is True:
                return True
        if test:
            # If testing, the last command should be 'transfer' or 'quit'
            raise exceptions.InsufficientTestCommands()
        self.cmdloop()

    def default(self, line):
        L = max(len(alias) for alias in self.configuration.aliases)
        while L > 0:
            try:
                alias = line[:L]
            except IndexError:
                L -= 1
                continue
            try:
                command = self.configuration.aliases[alias]
            except KeyError:
                L -= 1
                continue
            self.onecmd(command + line[L:])
            break
        else:
            self.error(line)

    def precmd(self, line):
        # Aliases must be handled in self.default, otherwise if they are a
        # substring of a built-in command, they will always override it, using
        # the rest of the string as an argument; for example, if 'q' is an
        # alias for 'quit', issuing 'quit' would be translated to 'quituit'
        # Nonetheless, handle '?' here because otherwise it's translated to
        # 'help' by cmd.Cmd by default; if self.do_shell was defined, also '!'
        # should be handled here
        try:
            qm = line[0]
        except IndexError:
            # Empty line
            pass
        else:
            if qm == '?':
                try:
                    command = self.configuration.aliases['?']
                except KeyError:
                    pass
                else:
                    line = command + line[1:]
        return line

    def _select_changes(self, rawsel):
        rawsel = rawsel.strip()

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

    def do_import(self, args):
        """
        Run a series of commands from a script.
        """
        with open(args, 'r') as script:
            for line in script:
                self.onecmd(line)

    def do_list(self, args):
        """
        List a selection of pending changes.
        """
        print()

        changes = self._select_changes(args)
        width = len(str(changes[-1].id_))

        # TODO #10 #11
        for change in changes:
            print(change.get_summary(width))

        print()

        return False

    def do_details(self, args):
        """
        List a selection of pending changes with details.
        """
        print()

        changes = self._select_changes(args)
        width = len(str(changes[-1].id_))

        # TODO #10 #11
        for change in changes:
            print(change.get_summary(width))
            print(change.get_details(width))

        print()

        return False

    def do_configure(self, args):
        """
        Open the configuration menu or execute a configuration command.
        """
        if args:
            self.configmenu.onecmd(args)
        else:
            self.configmenu.cmdloop()
        return False

    def complete_configure(self, text, line, begidx, endidx):
        # TODO: Return a 1-item iterable to autocomplete ******************************
        print()
        print('text', text)
        print('line', line)
        print('begidx', begidx)
        print('endidx', endidx)
        return [attr[3:] for attr in dir(self.configmenu) if attr[:3] == 'do_']

    def do_include(self, args):
        """
        Include (confirm) the changes in the synchronization.
        """
        # TODO #31: This should also ask to include all the ancestor
        #       directories, if they aren't included already
        for change in self._select_changes(args):
            change.include()
        return False

    def do_exclude(self, args):
        """
        Exclude (cancel) the changes from the synchronization.
        """
        # TODO #31: If this is a directory, this should also ask to exclude all
        #       the descendant files and directories, if they are still
        #       included
        for change in self._select_changes(args):
            change.exclude()
        return False

    def do_reset(self, args):
        """
        Reset the changes to an undecided status.
        """
        # TODO #31: If the path was included and was a directory, this should
        #       ask to reset all the descendants; if the path was excluded,
        #       this should ask to reset all the ancestor directories
        for change in self._select_changes(args):
            change.reset()
        return False

    def do_transfer(self, args):
        """
        Start the synchronization, then exit syncere.
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
        if args == '':
            self.transfer_mode = tuple(TRANSFER_MODES.values())[0]
        else:
            try:
                self.transfer_mode = self.TRANSFER_MODES[args]
            except KeyError:
                print('Unrecognized transfer mode')
                return False
        return True

    def do_quit(self, args):
        """
        Exit syncere without synchronizing anything.
        """
        if args == '':
            _m_sys.exit(0)
        self.error(args)

    def do_help(self, args):
        super().do_help(args)

        if not args:
            # TODO #4: Briefly introduce filters syntax
            #          Or maybe do it in the specific 'command help' menus of
            #          the commands that do support filters
            print("""Filters syntax:
            TODO

    Aliases:""")
            width = max(len(alias) for alias in self.configuration.aliases)
            for alias in sorted(self.configuration.aliases.keys()):
                print('        {}    {}'.format(
                      alias.ljust(width), self.configuration.aliases[alias]))
            print()


class ConfigMenu(_Menu):
    prompt = '(syncere>config) '

    def default(self, line):
        # Note that there's no point in making separate aliases for submenus
        # like ConfigMenu
        self.error(line)

    def do_alias(self, args):
        """
        Set a command alias.
        """
        # TODO Check that it's not overriding a built-in command ************************
        pass

    def do_unalias(self, args):
        """
        Unset a command alias.
        """
        # TODO *************************************************************************
        pass

    def do_unalias_all(self, args):
        """
        Unset all command aliases.
        """
        # TODO *************************************************************************
        pass

    def do_filter(self, args):
        """
        Edit the current list filter.
        """
        # TODO: Hide files that are not going to be transferred because ***************
        #       identical at the source and destination.
        #       Predefined rule: _m_re.match('\.[fdLDS] {9}$', match.group(1))
        print('filter', args)
        # From http://stackoverflow.com/a/2533142/645498
        _m_readline.set_startup_hook(lambda: _m_readline.insert_text('prefill'))
        try:
            input()
        finally:
            _m_readline.set_startup_hook()
        return False

    def do_exit(self, args):
        """
        Exit the configuration menu.
        """
        return True

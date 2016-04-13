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
# simply importing readline is enough to enable command history by pressing
# the up and down keys
# TODO #80
import readline as _m_readline  # NOQA <- this hides the lint error [F401]

from . import exceptions


class Interface:
    """
    This is the interface for interactively filtering the pending changes.
    """
    Proceed = type('Proceed', (Exception, ), {})
    Quit = type('Quit', (Exception, ), {})
    PROMPT = 'Command (h for help): '

    def __init__(self, pending_changes, test):
        self.pending_changes = pending_changes
        self.test = test

        # TODO #4 #30 #31 #32 #33 #34 #35 #56
        self.actions = OrderedDict((
            ('l', (self.list_summary, 'list pending changes')),
            ('d', (self.list_details, 'list pending changes with details')),
            ('>', (self.include_change, 'include (confirm) the changes in the '
                   'synchronization')),
            ('!', (self.exclude_change, 'exclude (cancel) the changes from '
                   'the synchronization')),
            ('?', (self.reset_change, 'reset the changes to an undecided '
                   'status')),
            ('S', (self.synchronize, 'start the synchronization, then exit '
                   'syncere')),
            ('q', (self.quit, 'exit syncere without synchronizing anything')),
            ('h', (self.help, 'show this help screen')),
        ))

        self.list_summary('')

        try:
            if self.test is False:
                while True:
                    command = input(self.PROMPT)
                    try:
                        action = self.actions[command[0]]
                    except IndexError:
                        # IndexError is raised if command is an empty string
                        pass
                    except KeyError:
                        print("Unrecognized command, enter 'h' for help")
                    else:
                        action[0](command[1:])
            else:
                while True:
                    try:
                        command = test.pop(0)
                    except IndexError:
                        raise exceptions.InsufficientTestCommands()
                    # TODO #60
                    print(self.PROMPT, command, sep='')
                    try:
                        action = self.actions[command[0]]
                    except (IndexError, KeyError):
                        # IndexError is raised if command is an empty string
                        raise exceptions.UnrecognizedTestCommand(command)
                    action[0](command[1:])
        except self.Quit:
            _m_sys.exit(0)
        except self.Proceed:
            pass

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

    def list_summary(self, args):
        print()

        changes = self._select_changes(args)
        width = len(str(changes[-1].id_))

        # TODO #10 #11
        for change in changes:
            print(change.get_summary(width))

        print()

    def list_details(self, args):
        print()

        changes = self._select_changes(args)
        width = len(str(changes[-1].id_))

        # TODO #10 #11
        for change in changes:
            print(change.get_summary(width))
            print(change.get_details(width))

        print()

    def include_change(self, args):
        # TODO #31: This should also ask to include all the ancestor
        #       directories, if they aren't included already
        for change in self._select_changes(args):
            change.include()

    def exclude_change(self, args):
        # TODO #31: If this is a directory, this should also ask to exclude all
        #       the descendant files and directories, if they are still
        #       included
        for change in self._select_changes(args):
            change.exclude()

    def reset_change(self, args):
        # TODO #31: If the path was included and was a directory, this should
        #       ask to reset all the descendants; if the path was excluded,
        #       this should ask to reset all the ancestor directories
        for change in self._select_changes(args):
            change.reset()

    def synchronize(self, args):
        # TODO #31: This should also warn if some files are included, but their
        #       parent directories are not, resulting in the files actually
        #       being excluded
        for change in self.pending_changes:
            if change.included not in (True, False):
                print('There are still undecided changes')
                break
        else:
            raise self.Proceed()

    def help(self, args):
        print()

        for akey in self.actions:
            print('   {0}   {1}'.format(akey, self.actions[akey][1]))

        print()

    def quit(self, args):
        raise self.Quit()

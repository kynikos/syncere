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
# TODO: it's possible to go beyond this and enable a completer etc., see the
#       documentation
import readline as _m_readline  # NOQA <- this hides the lint error [F401]


class Interface:
    """
    This is the interface for interactively filtering the pending changes.
    """
    Proceed = type('Proceed', (Exception, ), {})
    Quit = type('Quit', (Exception, ), {})

    def __init__(self, pending_changes):
        self.pending_changes = pending_changes

        # TODO: Document that some options take parameters (#,#-#,#,# or *)
        self.actions = OrderedDict((
            # TODO: It should be possible to use filters, e.g. only show
            #       included, excluded or undecided changes
            # TODO: Show only the root items; show only the children of a
            #       directory; show only the descendants of a directory
            #       Maybe a directory tree should be created during the
            #       initial parse of the --itemize-changes output
            ('l', (self.list_summary, 'list pending changes')),
            ('d', (self.list_details, 'list pending changes with details')),
            # TODO: When acting on a directory, it should be possible to apply
            #       the change recursively to its descendants
            ('>', (self.include_change, 'include (confirm) the changes in the '
                   'synchronization')),
            ('!', (self.exclude_change, 'exclude (cancel) the changes from '
                   'the synchronization')),
            ('?', (self.reset_change, 'reset the changes to an undecided '
                   'status')),

            # TODO: raw mode:
            #  The same arguments are passed
            #  to both rsync internal commands;
            #  only those strictly unsupported
            #  are rejected; this maximizes the
            #  compatibility with complex rsync
            #  commands but disables some of
            #  syncere features.

            # TODO: optimized mode:
            #  The arguments passed to the
            #  rsync commands are optimized
            #  according to known use cases;
            #  this means that some complex
            #  combinations of rsync arguments
            #  may not be supported.

            # TODO: advanced mode:
            #  All the given rsync arguments
            #  are also parsed by syncere in
            #  order to identify the source and
            #  destination locations, hence
            #  allowing syncere to enable some
            #  advanced features; only a subset
            #  of rsync arguments is supported
            #  by this mode, therefore some
            #  less common rsync use cases may
            #  not be supported.

            ('S', (self.synchronize, 'start the synchronization, then exit '
                   'syncere')),
            # TODO: Allow editing the pending changes in an external text
            #       editor (chosen with the $EDITOR environment variable)
            # TODO: Add a command to preview the actual rsync command that
            #       would be used with S, but remind that Popen takes care of
            #       escaping characters
            # TODO: It should be possible to write a files-from or exclude-from
            #       file from the menu
            ('q', (self.quit, 'exit syncere without synchronizing anything')),
            ('h', (self.help, 'show this help screen')),
        ))

        self.list_summary('')

        try:
            while True:
                inp = input('Command (h for help): ')
                try:
                    action = self.actions[inp[0]]
                except KeyError:
                    # FIXME
                    print("Unrecognized command, enter 'h' for help")
                else:
                    action[0](inp[1:])

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
                    # FIXME
                    print('Unrecognized selection')
                else:
                    changes.append(change)

            elif len(rsel) == 2:
                # TODO: It would be nice to also recognize e.g. "3-" as "select
                #       from 3 to the end"
                try:
                    ids, ide = [self._get_0_based_id(rid) for rid in rsel]
                except ValueError:
                    # FIXME
                    print('Unrecognized selection')
                else:
                    for change in self.pending_changes[ids:ide + 1]:
                        changes.append(change)

            else:
                # FIXME
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
        # FIXME
        print()

        changes = self._select_changes(args)
        width = len(str(changes[-1].id_))

        # TODO: Paginate; allow setting the limit
        # TODO: Use colors; allow disabling them
        for change in changes:
            # FIXME
            print(change.get_summary(width))

        # FIXME
        print()

    def list_details(self, args):
        # FIXME
        print()

        changes = self._select_changes(args)
        width = len(str(changes[-1].id_))

        # TODO: Paginate; allow setting the limit
        # TODO: Use colors; allow disabling them
        for change in changes:
            # FIXME
            print(change.get_summary(width))
            print(change.get_details(width))

        # FIXME
        print()

    def include_change(self, args):
        # TODO: This should also ask to include all the ancestor directories,
        #       if they aren't included already
        for change in self._select_changes(args):
            change.include()

    def exclude_change(self, args):
        # TODO: If this is a directory, this should also ask to exclude all the
        #       descendant files and directories, if they are still included
        for change in self._select_changes(args):
            change.exclude()

    def reset_change(self, args):
        # TODO: If the path was included and was a directory, this should ask
        #       to reset all the descendants; if the path was excluded, this
        #       should ask to reset all the ancestor directories
        for change in self._select_changes(args):
            change.reset()

    def synchronize(self, args):
        # TODO: This should also warn if some files are included, but their
        #       parent directories are not, resulting in the files actually
        #       being excluded
        for change in self.pending_changes:
            if change.included not in (True, False):
                # FIXME
                print('There are still undecided changes')
                break
        else:
            raise self.Proceed()

    def help(self, args):
        # FIXME
        print()

        for akey in self.actions:
            # FIXME
            print('   {0}   {1}'.format(akey, self.actions[akey][1]))

        # FIXME
        print()

    def quit(self, args):
        raise self.Quit()

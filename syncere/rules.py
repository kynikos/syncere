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

import re as _m_re

from . import exceptions

# TODO *******************************************************************************
"""
# Rules example

? .d..t...... p:./

 ?  >f+++++++++ p:aaa

 ? cd+++++++++p: dir with spaces /
!   >f+++++++++ p: dir with spaces / file with spaces

>cd+++++++++   p:one space/
  > >f+++++++++ p:one space/file 1 2 3

?cd+++++++++p:test1/
?  >f+++++++++ p:test1/foo1
?  cd+++++++++   p:test1/somedir33/
 ?>f+++++++++ p:test1/somedir33/blabla
"""


class Rules:
    """
    Main rule container: parses rulesets and applies rules to pending changes.
    """
    # TODO *************************************************************************
    IGNORE = r'(#|\s*$)'

    def __init__(self):
        self.rules = []

    def parse_ruleset(self, setname):
        # TODO *************************************************************************
        with open(setname, 'r') as ruleset:
            for line in ruleset:
                if not _m_re.match(self.IGNORE, line):
                    self.rules.append(Rule(line))

    def decide_change(self, ichange, sfilename):
        # TODO *************************************************************************
        # TODO #56
        dec = '?'

        for rule in self.rules:
            # TODO #20
            if ichange == rule.itemized and sfilename == rule.path:
                dec = rule.action

        return dec


class Rule:
    """
    Parse a rule line.
    """
    # TODO #6 #8
    ITEMIZED = (r'[<>ch.*][fdLDS](?:[.c][.s][.tT][.p][.o][.g][.u][.a][.x]|'
                r'[+ ?]{9}|\*deleting)')
    SYNTAX = r'\s*([!?>])\s*({0})\s*(pi?|P|gi?|G|ri?|R):(.+)$'.format(ITEMIZED)

    def __init__(self, line):
        match = _m_re.match(self.SYNTAX, line)
        if not match:
            # TODO #40
            raise exceptions.InvalidRuleError(line)

        self.action = match.group(1)
        self.itemized = match.group(2)
        self.path_type = match.group(3)
        self.path = match.group(4)

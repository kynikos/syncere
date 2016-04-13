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


class Rules:
    """
    Main rule container: parses rulesets and applies rules to pending changes.
    """
    IGNORE = r'(#|\s*$)'

    def __init__(self):
        self.rules = []

    def parse_ruleset(self, setname):
        # TODO #5
        with open(setname, 'r') as ruleset:
            for line in ruleset:
                if not _m_re.match(self.IGNORE, line):
                    self.rules.append(Rule(line))

    def decide_change(self, ichange, sfilename):
        # TODO #56
        dec = '?'

        for rule in self.rules:
            # TODO #6 #20
            if ichange == rule.itemized and sfilename == rule.path:
                dec = rule.action

        return dec


class Rule:
    """
    Parse a rule line.
    """
    # TODO #7 #8
    ITEMIZED = (r'[<>ch.*][fdLDS](?:[.c][.s][.tT][.p][.o][.g][.u][.a][.x]|'
                r'[+ ?]{9}|\*deleting)')
    SYNTAX = r'\s*([!?>])\s*({0})\s*(pi?|P|gi?|G|ri?|R):(.+)$'.format(ITEMIZED)

    def __init__(self, line):
        match = _m_re.match(self.SYNTAX, line)
        if not match:
            # TODO #40
            raise exceptions.InvalidRuleError(line)

        # TODO #6
        self.action = match.group(1)
        self.itemized = match.group(2)
        self.path_type = match.group(3)
        self.path = match.group(4)

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
        # TODO: The set must be searched in the configured ruleset directories
        with open(setname, 'r') as ruleset:
            for line in ruleset:
                if not _m_re.match(self.IGNORE, line):
                    self.rules.append(Rule(line))

    def decide_change(self, ichange, sfilename):
        # TODO: All the '!', '?', and '>' shouldn't be hardcoded everywhere...
        dec = '?'

        for rule in self.rules:
            # TODO: Allow choosing whether rules are applied in a cascading
            #       (last one wins) or rsync mode (first one wins)
            # TODO: Support all the path types and the itemized wildcards
            if ichange == rule.itemized and sfilename == rule.path:
                dec = rule.action

        return dec


class Rule:
    """
    Parse a rule line.
    """
    # TODO: Allow wildcards in the itemized representation
    # TODO: Allow to omit the itemized representation if only the path should
    #       be tested
    ITEMIZED = (r'[<>ch.*][fdLDS](?:[.c][.s][.tT][.p][.o][.g][.u][.a][.x]|'
                r'[+ ?]{9}|\*deleting)')
    # TODO: Allow enclosing the path in some character, e.g. in quotes, for
    #       example for paths that end with spaces, since they would be at risk
    #       of being trimmed by text editors
    #       The syntax could be e.g. 'p"path/to/file"', i.e. if a colon is
    #       used, than the path is expected to end at the line break; if a
    #       double quote is used, then the path is expected to end with '"$"
    #       Other supported characters/separators can be <>, all parentheses,
    #       or the path could be always started with '/', etc.
    SYNTAX = r'\s*([!?>])\s*({0})\s*(pi?|P|gi?|G|ri?|R):(.+)$'.format(ITEMIZED)

    def __init__(self, line):
        match = _m_re.match(self.SYNTAX, line)
        if not match:
            # TODO: Include the invalid rule and the line number in the error
            #       message
            raise exceptions.InvalidRuleError()

        # TODO: Support all the path types
        self.action = match.group(1)
        self.itemized = match.group(2)
        self.path_type = match.group(3)
        self.path = match.group(4)

        # FIXME
        print(self.action, self.itemized, self.path_type, self.path)

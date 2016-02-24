#! /usr/bin/env python3

# syncere - Interactive data synchronization through rsync or rdiff-backup.
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

import argparse
import subprocess


class Syncere:
    def __init__(self, profile):
        with open(profile, 'r') as profs:
            for line in profs:
                if line[:2] == '1:':
                    subprocess.call(line[3:], shell=True)


def main():
    cliparser = argparse.ArgumentParser(description="syncere - Interactive "
                                        "data synchronization through rsync "
                                        "or rdiff-backup.", add_help=True)
    cliparser.add_argument('profile', metavar='PATH',
                           help='the profile to use for this session')
    cliargs = cliparser.parse_args()
    Syncere(cliargs.profile)


if __name__ == '__main__':
    main()

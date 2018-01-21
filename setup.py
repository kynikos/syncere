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

from setuptools import setup

setup(
    name='syncere',
    version='0.8.0',
    description='Interactive rsync-based data synchronization.',
    long_description='Interactive rsync-based data synchronization.',
    author='Dario Giovannetti',
    author_email='dev@dariogiovannetti.net',
    url='https://github.com/kynikos/syncere',
    license='GPLv3+',
    packages=['syncere'],
    install_requires=['forwarg', 'cmenu'],
    entry_points={
        'console_scripts': ['syncere = syncere:Syncere']
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Archiving :: Mirroring',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',  # noqa
        'Programming Language :: Python :: 3',
    ],
    keywords='rsync synchronization backup files transfer mirroring',
)

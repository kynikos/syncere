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

import argparse

from . import Syncere


def main():
    # There would also be the prefix_chars argument, but it would make using
    #  the program too confusing
    #  Anyway, in that case "=" couldn't be used because it's also used to pass
    #   values to long options, e.g. ==option=value would be ambiguous
    #  Also other characters are reserved by the shell, e.g. "<" and ">"
    #  "~" would look too similar to the normal "-", and also some programs use
    #   it to indicate temporary files
    parser_root = argparse.ArgumentParser(description="syncere is a "
                                          "drop-in rsync wrapper that makes "
                                          "data synchronization sessions "
                                          "interactive.",
                                          # rsync's -h option has an
                                          # ambiguous meaning, don't deal
                                          # with it automatically
                                          add_help=False)

    # TODO: expand the version message
    parser_root.add_argument('--version', action='version',
                             version='%(prog)s {0}'.format(Syncere.VERSION))

    parser_root.add_argument('-h', '--help', action='help',
                             help="Show this help message and exit.")

    parsers_modes = parser_root.add_subparsers(title='modes of operation',
                                               description="These are the "
                                               "modes in which syncere can "
                                               "work: they determine the "
                                               "compatibility with the native "
                                               "rsync options.",
                                               dest='subparser_name')

    parser_raw = parsers_modes.add_parser('raw', aliases=['R', '0'],
                                          usage='%(prog)s [OPTION...] SRC... '
                                          '[DEST]',
                                          help="The same arguments are passed "
                                          "to both rsync internal commands; "
                                          "only those strictly unsupported "
                                          "are rejected; this maximizes the "
                                          "compatibility with complex rsync "
                                          "commands but disables some of "
                                          "syncere features.",
                                          # Don't use parser_root as a parent,
                                          # or the subparsers will be inherited
                                          # too
                                          add_help=False)

    parser_raw_syncere_group = parser_raw.add_argument_group(
                                'syncere arguments',
                                "These are the arguments specific to syncere.")

    # TODO: Implement
    parser_raw_syncere_group.add_argument('--ruleset',
                                          metavar='NAME', action='append',
                                          dest='rulesets', default=[],
                                          help="Load a pre-saved set of rules "
                                          "to automatically confirm or "
                                          "discard recurrent file transfers. "
                                          "Repeat the option to load more "
                                          "rule sets in the specified order.")
    # TODO: Also allow passing rules from a file with --rules-from and
    #       directly with a --rule option, similar to --exclude-from and
    #       --exclude

    parser_raw_overridden_group = parser_raw.add_argument_group(
                                       "overridden arguments",
                                       "This section explains how syncere "
                                       "supports the original rsync "
                                       "arguments, and passes them on to "
                                       "the internal rsync commands. See "
                                       "rsync(1) for information about "
                                       "their usage. Note that for obvious "
                                       "reasons the --daemon mode and "
                                       "related options are not supported.")

    # TODO: properly reflect rsync's ambivalent meaning of -h, and update
    #       --help's description to mention that it's supported
    #       At least check that -h works as --human-readable
    parser_raw_overridden_group.add_argument(
                                    '--help', action='help',
                                    help="Show this help message and exit. "
                                    "Unlike rsync, using -h without "
                                    "options is not supported.")

    parser_raw_shared_group = parser_raw.add_argument_group(
                        'shared arguments',
                        "These arguments are used by syncere but also passed "
                        "to the rsync commands.")

    # TODO
    parser_raw_shared_group.add_argument('-v --verbose', action='count',
                                         help="Passed verbatim to both the "
                                         "internal rsync commands, but it "
                                         "also has an effect on the details "
                                         "of syncere's specific messages.")

    parser_raw_semisupported_group = parser_raw.add_argument_group(
                            'semisupported arguments',
                            "These rsync arguments are somewhat supported.")

    # TODO
    parser_raw_semisupported_group.add_argument(
                            '--msgs2stderr', action='store_true',
                            help="Passed verbatim to the transfer rsync "
                            "command, but it is incompatible with the "
                            "preview command.")
    # TODO
    parser_raw_semisupported_group.add_argument(
                            '-q', '--quiet', action='store_true',
                            help="Passed verbatim to the transfer rsync "
                            "command, but it is incompatible with the "
                            "preview command.")

    parser_raw_unsupported_group = parser_raw.add_argument_group(
                                'unsupported arguments',
                                "These rsync arguments are unsupported, i.e. "
                                "they will prevent syncere from running.")

    # TODO
    parser_raw_unsupported_group.add_argument('--daemon', action='store_true')

    # TODO
    parser_raw_unsupported_group.add_argument('--config', metavar='FILE')

    # TODO
    parser_raw_unsupported_group.add_argument('-M', '--dparam',
                                              metavar='OVERRIDE')

    # TODO
    parser_raw_unsupported_group.add_argument('--no-detach',
                                              action='store_true')

    parser_opt = parsers_modes.add_parser('optimized',
                                          aliases=['opt', 'O', '1'],
                                          usage='%(prog)s [OPTION...] SRC... '
                                          '[DEST]',
                                          help="The arguments passed to the "
                                          "rsync commands are optimized "
                                          "according to known use cases; "
                                          "this means that some complex "
                                          "combinations of rsync arguments "
                                          "may not be supported.",
                                          parents=[parser_raw],
                                          add_help=False)

    parser_opt_optimized_group = parser_opt.add_argument_group(
                                'optimized arguments',
                                "Using these rsync arguments will trigger "
                                "special optimizing features.")

    # TODO
    parser_opt_optimized_group.add_argument('-c', '--checksum',
                                            action='store_true',
                                            help="Only used for the preview "
                                            "rsync command. It will not be "
                                            "used again for the syncing "
                                            "command.")

    # TODO
    parser_opt_optimized_group.add_argument('-a', '--archive',
                                            action='store_true',
                                            help="Passed verbatim to both the "
                                            "internal rsync commands.")

    parser_adv = parsers_modes.add_parser('advanced',
                                          aliases=['adv', 'A', '2'],
                                          # The unsupported options
                                          # shouldn't be shown in the usage
                                          # line
                                          usage='%(prog)s [OPTION...] SRC... '
                                          '[DEST]',
                                          help="All the given rsync arguments "
                                          "are also parsed by syncere in "
                                          "order to identify the source and "
                                          "destination locations, hence "
                                          "allowing syncere to enable some "
                                          "advanced features; only a subset "
                                          "of rsync arguments is supported "
                                          "by this mode, therefore some "
                                          "less common rsync use cases may "
                                          "not be supported.",
                                          parents=[parser_opt],
                                          add_help=False)

    parser_adv_advanced_group = parser_adv.add_argument_group(
                                'supported arguments',
                                "Besides those above, these are the only "
                                "rsync arguments supported by this mode.")

    # TODO
    parser_adv_advanced_group.add_argument('--info', metavar='FLAGS',
                                           help="Passed verbatim to the "
                                           "internal synchronizing rsync "
                                           "command. The preview command "
                                           "must instead force its own "
                                           "--info option in order to "
                                           "properly preview the "
                                           "files to be changed.")

    # TODO
    parser_adv_advanced_group.add_argument('--debug', metavar='FLAGS',
                                           help="Passed verbatim to both the "
                                           "internal rsync commands.")

    # TODO
    parser_adv_advanced_group.add_argument('--no-motd', action='store_true',
                                           help="Passed verbatim to both the "
                                           "internal rsync commands.")

    # TODO: Some ways to accept the rsync arguments:
    #  * use separate profile files to list the options
    #  * introduce syncere options with --syncere-*
    #  * use the special -- flag to separate the raw rsync options
    #    If using ==, -- must be implied, and vice versa
    #  * use a different prefix for syncere options, e.g. ==
    #  * adopt a white-list method, where only some options are explicitly
    #    supported
    #  * adopt a black-list method, where the known troublesome arguments
    #    are detected and a warning or error is issued if present
    # TODO: Remember to fail if rsyncargs is not empty in advanced mode
    syncereargs, rsyncargs = parser_root.parse_known_args()
    # FIXME
    print(syncereargs, rsyncargs)
    Syncere(syncereargs, rsyncargs).run()

    # FIXME: use where/if needed instead of sys.exit()
    parser_root.exit(0)


# TODO: Investigate the behavior with links, especially hard links, because
# excluding their copies/targets may generate synchronization issues
"""
-l, --links                 copy symlinks as symlinks
-L, --copy-links            transform symlink into referent file/dir
--copy-unsafe-links     only "unsafe" symlinks are transformed
--safe-links            ignore symlinks that point outside the tree
--munge-links           munge symlinks to make them safer
-k, --copy-dirlinks         transform symlink to dir into referent dir
-K, --keep-dirlinks         treat symlinked dir on receiver as dir
-H, --hard-links            preserve hard links
"""

# TODO: --archive inherits the problems of the options it activates
"""
-a, --archive               archive mode; equals -rlptgoD (no -H,-A,-X)
"""

# TODO: Test the effect of these arguments
"""
--no-OPTION             turn off an implied OPTION (e.g. --no-D)
--timeout=SECONDS       set I/O timeout in seconds
--contimeout=SECONDS    set daemon connection timeout in seconds
-s, --protect-args          no space-splitting; wildcard chars only
--outbuf=N|L|B          set out buffering to None, Line, or Block
-8, --8-bit-output          leave high-bit chars unescaped in output
-M, --remote-option=OPTION  send OPTION to the remote side only
--log-file=FILE         log what we're doing to the specified FILE
--log-file-format=FMT   log updates using the specified FMT
--list-only             list the files instead of copying them
"""

# TODO: These can't stay in the preview command; they are ok in the transfer
#       command
"""
--msgs2stderr           special output handling for debugging
-q, --quiet                 suppress non-error messages
"""

# TODO: In order to avoid recalculating the checksums again, the transfer
# command could omit the --checksum argument, compile a --files-from list
# instead of an --exclude-from list, and use --ignore-times to force updating
# the files whose size and timestamp are the same (the only difference is the
# checksum)
"""
-c, --checksum              skip based on checksum, not mod-time & size
"""

# TODO: Is this similar to --checksum?
"""
-y, --fuzzy                 find similar file for basis if no dest file
"""

# TODO: Can these arguments be specified multiple times?
"""
--exclude-from=FILE     read exclude patterns from FILE
--include-from=FILE     read include patterns from FILE
--files-from=FILE       read list of source-file names from FILE
"""

# TODO: This can create problems if the generated files use different
#       delimiters
"""
-0, --from0                 all *from/filter files are delimited by 0s
"""

# TODO: Inform that these are shared (but maybe parsing them would be too
#       aggressive except in advanced mode?)
"""
-v, --verbose               increase verbosity
--info=FLAGS            fine-grained informational verbosity
--stats                 give some file-transfer stats
-i, --itemize-changes       output a change-summary for all updates
--out-format=FORMAT     output updates using the specified FORMAT
-n, --dry-run               perform a trial run with no changes made
"""

# TODO: It doesn't make sense to support daemon mode
"""
--daemon                run as an rsync daemon
--config=FILE           specify alternate rsyncd.conf file
-M, --dparam=OVERRIDE       override global daemon config parameter
--no-detach             do not detach from the parent
"""

# TODO: These should be safe in both commands
"""
--debug=FLAGS           fine-grained debug verbosity
--no-motd               suppress daemon-mode MOTD (see caveat)
-r, --recursive             recurse into directories
-R, --relative              use relative path names
--no-implied-dirs       don't send implied dirs with --relative
-b, --backup                make backups (see --suffix & --backup-dir)
--backup-dir=DIR        make backups into hierarchy based in DIR
--suffix=SUFFIX         backup suffix (default ~ w/o --backup-dir)
-u, --update                skip files that are newer on the receiver
--inplace               update destination files in-place
--append                append data onto shorter files
--append-verify         --append w/old data in file checksum
-d, --dirs                  transfer directories without recursing
-p, --perms                 preserve permissions
-E, --executability         preserve executability
--chmod=CHMOD           affect file and/or directory permissions
-A, --acls                  preserve ACLs (implies -p)
-X, --xattrs                preserve extended attributes
-o, --owner                 preserve owner (super-user only)
-g, --group                 preserve group
--devices               preserve device files (super-user only)
--specials              preserve special files
-D                          same as --devices --specials
-t, --times                 preserve modification times
-O, --omit-dir-times        omit directories from --times
-J, --omit-link-times       omit symlinks from --times
--super                 receiver attempts super-user activities
--fake-super            store/recover privileged attrs using xattrs
-S, --sparse                handle sparse files efficiently
--preallocate           allocate dest files before writing
-W, --whole-file            copy files whole (w/o delta-xfer algorithm)
-x, --one-file-system       don't cross filesystem boundaries
-B, --block-size=SIZE       force a fixed checksum block-size
-e, --rsh=COMMAND           specify the remote shell to use
--rsync-path=PROGRAM    specify the rsync to run on remote machine
--existing              skip creating new files on receiver
--ignore-existing       skip updating files that exist on receiver
--remove-source-files   sender removes synchronized files (non-dir)
--del                   an alias for --delete-during
--delete                delete extraneous files from dest dirs
--delete-before         receiver deletes before xfer, not during
--delete-during         receiver deletes during the transfer
--delete-delay          find deletions during, delete after
--delete-after          receiver deletes after transfer, not during
--delete-excluded       also delete excluded files from dest dirs
--ignore-missing-args   ignore missing source args without error
--delete-missing-args   delete missing source args from destination
--ignore-errors         delete even if there are I/O errors
--force                 force deletion of dirs even if not empty
--max-delete=NUM        don't delete more than NUM files
--max-size=SIZE         don't transfer any file larger than SIZE
--min-size=SIZE         don't transfer any file smaller than SIZE
--partial               keep partially transferred files
--partial-dir=DIR       put a partially transferred file into DIR
--delay-updates         put all updated files into place at end
-m, --prune-empty-dirs      prune empty directory chains from file-list
--numeric-ids           don't map uid/gid values by user/group name
--usermap=STRING        custom username mapping
--groupmap=STRING       custom groupname mapping
--chown=USER:GROUP      simple username/groupname mapping
-I, --ignore-times          don't skip files that match size and time
--size-only             skip files that match in size
--modify-window=NUM     compare mod-times with reduced accuracy
-T, --temp-dir=DIR          create temporary files in directory DIR
--compare-dest=DIR      also compare received files relative to DIR
--copy-dest=DIR         ... and include copies of unchanged files
--link-dest=DIR         hardlink to files in DIR when unchanged
-z, --compress              compress file data during the transfer
--compress-level=NUM    explicitly set compression level
--skip-compress=LIST    skip compressing files with suffix in LIST
-C, --cvs-exclude           auto-ignore files in the same way CVS does
-f, --filter=RULE           add a file-filtering RULE
-F                          same as --filter='dir-merge /.rsync-filter'
--filter='- .rsync-filter'
--exclude=PATTERN       exclude files matching PATTERN
--include=PATTERN       don't exclude files matching PATTERN
--address=ADDRESS       bind address for outgoing socket to daemon
--port=PORT             specify double-colon alternate port number
--sockopts=OPTIONS      specify custom TCP options
--blocking-io           use blocking I/O for the remote shell
-h, --human-readable        output numbers in a human-readable format
--progress              show progress during transfer
-P                          same as --partial --progress
--password-file=FILE    read daemon-access password from FILE
--bwlimit=RATE          limit socket I/O bandwidth
--write-batch=FILE      write a batched update to FILE
--only-write-batch=FILE like --write-batch but w/o updating dest
--read-batch=FILE       read a batched update from FILE
--protocol=NUM          force an older protocol version to be used
--iconv=CONVERT_SPEC    request charset conversion of filenames
--checksum-seed=NUM     set block/file checksum seed (advanced)
-4, --ipv4                  prefer IPv4
-6, --ipv6                  prefer IPv6
--version               print version number
-h) --help                  show this help (see below for -h comment)
"""

main()

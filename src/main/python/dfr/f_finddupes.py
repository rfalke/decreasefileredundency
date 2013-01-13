#!/usr/bin/env python

import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))

import dfr.db
from dfr.bit_equal_finder import BitEqualFinder
from dfr.bit_truncated_finder import BitTruncatedFinder
from dfr.support import format_bytes, add_common_command_line_arguments


class InteractiveResolver:
    def __init__(self, dry_run):
        self.dry_run = dry_run

    def _delete(self, to_delete):
        assert len(to_delete) >= 1
        for path in to_delete:
            if self.dry_run:
                print "(dry-run) Would remove %s" % path
            else:
                os.remove(path)


class InteractiveBitEqualResolver(InteractiveResolver):
    def __init__(self, dry_run):
        InteractiveResolver.__init__(self, dry_run)
        self.default_preserve = None

    def _evaluate_input(self, input, pair):
        if input == "a":
            if pair.hardlinked:
                print "Error: Will not remove both hardlinked files."
                return None
            else:
                to_delete = [pair.path1, pair.path2]
        elif input == "s":
            return []
        elif input == "1!":
            to_delete = [pair.path2]
            self.default_preserve = 1
        elif input == "2!":
            to_delete = [pair.path1]
            self.default_preserve = 2
        else:
            try:
                choice = int(input)
            except ValueError:
                return None
            if choice not in [1, 2]:
                return None
            if choice == 1:
                to_delete = [pair.path2]
            elif choice == 2:
                to_delete = [pair.path1]
            else:
                assert 0
        return to_delete

    # pylint: disable=R0913
    def resolve(self, pair):
        progress = "[%d.%d/%d] " % (
            pair.ctxt_index+1, pair.ctxt_subindex+1, pair.ctxt_size)

        print "\nThe following files are equal and %s bytes large" % (
            format_bytes(pair.size))
        while True:
            print "  [1] %s" % pair.path1
            print "  [2] %s" % pair.path2
            msg = progress+"sPreserve what? Press 1, 2, "
            if not pair.hardlinked:
                msg += "'a' (to delete all), "
            msg += "'s' (to skip)."
            print msg

            if self.default_preserve:
                if self.default_preserve == 1:
                    to_delete = [pair.path2]
                elif self.default_preserve == 2:
                    to_delete = [pair.path1]
                else:
                    assert 0
            else:
                input = raw_input("> ")
                to_delete = self._evaluate_input(input, pair)
                if to_delete is None:
                    continue
                elif to_delete == []:
                    break

            self._delete(to_delete)
            break


class InteractiveBitTruncatedResolver(InteractiveResolver):
    def __init__(self, dry_run):
        InteractiveResolver.__init__(self, dry_run)

    def resolve(self, pair):
        progress = "[%d.%d/%d] " % (
            pair.ctxt_index+1, pair.ctxt_subindex+1, pair.ctxt_size)

        print "\n%sThe file '%s' is a shorter version of '%s'" % (
            progress, pair.small_path, pair.large_path)

        while True:
            print "Type 'd' to delete the shorter version. 's' to skip."

            input = raw_input("> ")
            if input == 'd':
                self._delete([pair.small_path])
                return
            elif input == 's':
                return
            else:
                continue


def main():
    parser = argparse.ArgumentParser(
        description='Find files with equal or similar content.')
    parser.add_argument('roots', metavar='DIR', nargs='*', default=["."],
                        help="a directory to scan for duplicate files " +
                        "(if not given '.' will be used)")
    add_common_command_line_arguments(parser)
    parser.add_argument('-c', '--csv', action="store_true",
                        help='print all findings as a CSV using instead ' +
                        'of resolve interactive')
    parser.add_argument('-n', '--dry-run', action="store_true", dest='dry_run',
                        help='do not delete any files')
    parser.add_argument('-t', '--truncated', action="store_true",
                        dest='truncated',
                        help='search for truncated files')

    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    if args.truncated:
        if args.csv:
            print "largesize;largepath;smallsize;smallpath"
        else:
            resolver = InteractiveBitTruncatedResolver(args.dry_run)
        finder = BitTruncatedFinder(repo, args.roots)
        for pair in finder.find():
            if args.csv:
                print "%d;%s;%s;%s" % (
                    pair.large_size, pair.large_path,
                    pair.small_size, pair.small_path)
            else:
                resolver.resolve(pair)
    else:
        if args.csv:
            print "size;hardlinked;path1;path2"
        else:
            resolver = InteractiveBitEqualResolver(args.dry_run)
        finder = BitEqualFinder(repo, args.roots)
        for pair in finder.find():
            if args.csv:
                print "%d;%s;%s;%s" % (
                    pair.size, pair.hardlinked, pair.path1, pair.path2)
            else:
                resolver.resolve(pair)

if __name__ == '__main__':
    main()


import argparse
import os
import locale

import dfr.db
from dfr.bit_equal_finder import BitEqualFinder


def format_bytes(bytes):
    return locale.format('%d', bytes, 1)


class InteractiveResolver:
    def __init__(self, dry_run):
        self.dry_run = dry_run
        self.default_preserve = None

    def _evaluate_input(self, input, hardlinked, path1, path2):
        if input == "a":
            if hardlinked:
                print "Error: Will not remove both hardlinked files."
                return None
            else:
                to_delete = [path1, path2]
        elif input == "s":
            return []
        elif input == "1!":
            to_delete = [path2]
            self.default_preserve = 1
        elif input == "2!":
            to_delete = [path1]
            self.default_preserve = 2
        else:
            try:
                choice = int(input)
            except ValueError:
                return None
            if choice not in [1, 2]:
                return None
            if choice == 1:
                to_delete = [path2]
            elif choice == 2:
                to_delete = [path1]
            else:
                assert 0
        return to_delete

    # pylint: disable=R0913
    def resolve(self, size, hardlinked, path1, path2, context):
        progress = "[%d.%d/%d] " % (
            context.index+1, context.subindex+1, context.size)

        print "\nThe following files are equal and %s bytes large" % (
            format_bytes(size))
        while True:
            print "  [1] %s" % path1
            print "  [2] %s" % path2
            msg = progress+"sPreserve what? Press 1, 2, "
            if not hardlinked:
                msg += "'a' (to delete all), "
            msg += "'s' (to skip)."
            print msg

            if self.default_preserve:
                if self.default_preserve == 1:
                    to_delete = [path2]
                elif self.default_preserve == 2:
                    to_delete = [path1]
                else:
                    assert 0
            else:
                input = raw_input("> ")
                to_delete = self._evaluate_input(
                    input, hardlinked, path1, path2)
                if to_delete is None:
                    continue
                elif to_delete == []:
                    break

            assert len(to_delete) >= 1
            for path in to_delete:
                if self.dry_run:
                    print "(dry-run) Would remove %s" % path
                else:
                    os.remove(path)
            break


def main():
    locale.setlocale(locale.LC_ALL, 'en_US')
    default_db_file = dfr.db.get_default_db_file()

    parser = argparse.ArgumentParser(
        description='Find files with equal or similar content.')
    parser.add_argument('roots', metavar='DIR', nargs='*', default=["."],
                        help="a directory to scan for duplicate files " +
                        "(if not given '.' will be used)")
    parser.add_argument('--db-file', metavar="FILE", dest='db', nargs=1,
                        default=[default_db_file],
                        help='the db file (default: '+default_db_file+')')
    parser.add_argument('-c', '--csv', action="store_true",
                        help='print all findings as a CSV using instead ' +
                        'of resolve interactive')
    parser.add_argument('-n', '--dry-run', action="store_true", dest='dry_run',
                        help='do not delete any files')

    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    if args.csv:
        print "size;hardlinked;path1;path2"
    else:
        resolver = InteractiveResolver(args.dry_run)
    finder = BitEqualFinder(repo)
    for size, hardlinked, path1, path2, context in finder.find(args.roots):
        if args.csv:
            print "%d;%s;%s;%s" % (size, hardlinked, path1, path2)
        else:
            resolver.resolve(size, hardlinked, path1, path2, context)

if __name__ == '__main__':
    main()

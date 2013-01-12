
import argparse
import dfr.db
from dfr.bit_indexer import BitIndexer
from dfr.support import add_common_command_line_arguments


def main():
    parser = argparse.ArgumentParser(
        description='Index directories recursive.')
    parser.add_argument('roots', metavar='DIR', nargs='*', default=["."],
                        help="a directory to index " +
                        "(if not given '.' will be used)")
    add_common_command_line_arguments(parser)

    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    indexer = BitIndexer(repo)
    indexer.run(args.roots)

if __name__ == '__main__':
    main()

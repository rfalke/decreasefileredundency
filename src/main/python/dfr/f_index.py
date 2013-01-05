
import argparse
import dfr.db
from dfr.bit_indexer import BitIndexer


def main():
    default_db_file = dfr.db.get_default_db_file()

    parser = argparse.ArgumentParser(
        description='Index directories recursive.')
    parser.add_argument('roots', metavar='DIR', nargs='*', default=["."],
                        help="a directory to index " +
                        "(if not given '.' will be used)")
    parser.add_argument('--db-file', metavar="FILE", dest='db', nargs=1,
                        default=[default_db_file],
                        help='the db file (default: '+default_db_file+')')

    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    indexer = BitIndexer(repo)
    indexer.run(args.roots)

if __name__ == '__main__':
    main()

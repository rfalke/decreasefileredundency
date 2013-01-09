
import argparse
import dfr.db
from dfr.image_indexer import ImageIndexer


def main():
    default_db_file = dfr.db.get_default_db_file()

    parser = argparse.ArgumentParser(
        description='Generate image signatures for files in database.')
    parser.add_argument('--db-file', metavar="FILE", dest='db', nargs=1,

                        default=[default_db_file],
                        help='the db file (default: '+default_db_file+')')

    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    indexer = ImageIndexer(repo)
    indexer.run()

if __name__ == '__main__':
    main()

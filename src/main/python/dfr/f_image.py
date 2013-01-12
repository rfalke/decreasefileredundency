
import argparse
import dfr.db
from dfr.image_indexer import ImageIndexer
from dfr.support import add_common_command_line_arguments


def main():
    parser = argparse.ArgumentParser(
        description='Generate image signatures for files in database.')
    add_common_command_line_arguments(parser)

    args = parser.parse_args()
    repo = dfr.db.Database(args.db[0])

    indexer = ImageIndexer(repo)
    indexer.run()

if __name__ == '__main__':
    main()

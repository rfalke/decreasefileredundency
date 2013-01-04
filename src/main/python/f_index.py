
import sys,os,argparse
import db,bit_indexer

default_db_file=db.get_default_db_file()

parser = argparse.ArgumentParser(description='Index directories recursive.')
parser.add_argument('roots', metavar='DIR', nargs='*', default=["."],
                   help="a directory to index (if not given '.' will be used)")
parser.add_argument('--db-file', metavar="FILE",dest='db', nargs=1,
                   default=[default_db_file],
                   help='the db file (default: '+default_db_file+')')

args = parser.parse_args()
repo=db.Database(args.db[0])

indexer=bit_indexer.BitIndexer(repo)
indexer.run(args.roots)

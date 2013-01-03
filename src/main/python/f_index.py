
import sys,os

import db,bit_indexer

repo=db.Database()

roots=sys.argv[1:]
if not roots:
    roots=["."]

indexer=bit_indexer.BitIndexer(repo)
indexer.run(roots)

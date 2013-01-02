
import sys,os

import support,db

repo=db.Database()

roots=sys.argv[1:]
if not roots:
    roots=["."]

for root in roots:
    for x in os.walk(root):
        support.index_one_directory(repo, *x)

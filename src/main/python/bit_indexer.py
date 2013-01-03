
import os,sys,hashlib
import bit_hashing

MIN_LENGTH=1024

def abspath(path):
    return os.path.realpath(os.path.abspath(path))

class BitIndexer:
    def __init__(self,db,verbose_progress=1):
        self.db=db
        self.verbose_progress=verbose_progress

    def should_index_file(self,dirpath, filename, size):
        if size<MIN_LENGTH: return False
        return True

    def run(self,roots):
        for root in roots:
            for x in os.walk(root):
                self.index_one_directory(*x)
        self.progress("\n")
    
    def get_or_insert_content(self, fullpath, size):
        first,full,other=bit_hashing.get_sha1sums(fullpath,size,MIN_LENGTH)
        other_hashs=" ".join(["%d:%s"%x for x in other.items()])
        return self.db.get_or_insert_content(first,full,size,other_hashs)
    
    def index_one_directory(self,dirpath, dirnames, filenames):
        self.progress("[")

        self.db.begin()

        dirid = self.db.get_or_insert_dir(abspath(dirpath))

        for filename in self.db.get_file_names_of_dir(dirid):
            if filename not in filenames:
                sys.stdout.write("d");sys.stdout.flush()
                self.db.remove_file(dirid,filename)

        for filename in filenames:
            fullpath=os.path.join(dirpath,filename)
            size=long(os.path.getsize(fullpath))

            if not self.should_index_file(dirpath, filename, size): continue
            dbfile = self.db.get_file(dirid,filename)
            if dbfile and dbfile.size==size:
                continue

            self.progress(".")
            contentid = self.get_or_insert_content(fullpath, size)
            self.db.insert_or_update_file(dirid,filename,contentid)

        self.db.commit()
        self.progress("]")

    def progress(self,msg):
        if self.verbose_progress:
            sys.stdout.write(msg);sys.stdout.flush()

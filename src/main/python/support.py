
import os,sys,hashlib,string

MIN_LENGTH=1024
MAX_CHUNK_SIZE=long(4*1024*1024)

def abspath(path):
    return os.path.realpath(os.path.abspath(path))

def should_index_file(dirpath, filename, size):
    if size<MIN_LENGTH: return False
    return True
   
def get_sha1sums(fullpath, size):
    file=open(fullpath,"r")
    h=hashlib.sha1()
    current_size=1024L
    bytes_read=0L
    result={}
    chunk_size=1024
    while 1:
        buffer=file.read(chunk_size)
        h.update(buffer)
        bytes_read += long(len(buffer))
        last_one = (len(buffer)!=chunk_size)
        if bytes_read==current_size or last_one:
            result[long(bytes_read)]=h.hexdigest()
            current_size=current_size*2L
            chunk_size=bytes_read
            if chunk_size>MAX_CHUNK_SIZE:
                chunk_size=MAX_CHUNK_SIZE
        if last_one:
            break
    file.close()
    first=result[1024]
    full=result[size]
    del result[1024]
    del result[size]
    return first,full,result

def get_or_insert_content(db, fullpath, size):
    first,full,other=get_sha1sums(fullpath,size)
    other_hashs=" ".join(["%d:%s"%x for x in other.items()])
    return db.get_or_insert_content(first,full,size,other_hashs)
    
def index_one_directory(db,dirpath, dirnames, filenames):
    sys.stdout.write("[");sys.stdout.flush()

    db.begin()

    dirid=db.get_or_insert_dir(abspath(dirpath))

    for filename in db.get_file_names_of_dir(dirid):
        if filename not in filenames:
            sys.stdout.write("d");sys.stdout.flush()
            db.remove_file(dirid,filename)
    
    for filename in filenames:
        fullpath=os.path.join(dirpath,filename)
        size=long(os.path.getsize(fullpath))
        
        if not should_index_file(dirpath, filename, size): continue
        dbfile=db.get_file(dirid,filename)
        if dbfile and dbfile.size==size:
            continue

        sys.stdout.write(".");sys.stdout.flush()
        contentid=get_or_insert_content(db,fullpath, size)
        db.insert_or_update_file(dirid,filename,contentid)

    db.commit()
    sys.stdout.write("]");sys.stdout.flush()

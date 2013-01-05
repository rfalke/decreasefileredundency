
import hashlib

MAX_CHUNK_SIZE_FOR_HASHING = long(4*1024*1024)


def get_sha1sums(fullpath, size, first_hash_size):
    assert size >= first_hash_size
    file = open(fullpath, "r")
    hashobj = hashlib.sha1()
    current_size = long(first_hash_size)
    bytes_read = 0L
    result = {}
    chunk_size = first_hash_size
    while 1:
        buffer = file.read(chunk_size)
        hashobj.update(buffer)
        bytes_read += long(len(buffer))
        last_one = (len(buffer) != chunk_size)
        if bytes_read == current_size or last_one:
            result[long(bytes_read)] = hashobj.hexdigest()
            current_size = current_size*2L
            chunk_size = bytes_read
            if chunk_size > MAX_CHUNK_SIZE_FOR_HASHING:
                chunk_size = MAX_CHUNK_SIZE_FOR_HASHING
        if last_one:
            break
    file.close()
    first = result[first_hash_size]
    full = result[size]
    del result[first_hash_size]
    if size != first_hash_size:
        del result[size]
    return first, full, result

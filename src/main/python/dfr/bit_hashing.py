
import hashlib


def get_sha1sums(fullpath, file_size, first_hash_size,
                 buffer_size=long(4*1024*1024)):
    assert file_size >= first_hash_size
    assert buffer_size >= first_hash_size
    file_size = long(file_size)
    first_hash_size = long(first_hash_size)
    buffer_size = long(buffer_size)

    file = open(fullpath, "r")
    hashobj = hashlib.sha1()
    buffer = file.read(buffer_size)
    assert len(buffer) in [file_size, buffer_size]

    current_size = first_hash_size
    offset = 0

    result = {}
    while file_size >= current_size:
        hashobj.update(buffer[offset:current_size])
        result[long(current_size)] = hashobj.hexdigest()

        offset = current_size
        current_size *= 2

    if file_size < buffer_size:
        hashobj.update(buffer[offset:])
        result[long(file_size)] = hashobj.hexdigest()
    elif file_size == buffer_size:
        # the hash for whole file is already there
        pass
    else:
        assert len(buffer) == buffer_size
        bytes_read = buffer_size
        current_size = 2*buffer_size
        while 1:
            buffer = file.read(buffer_size)
            hashobj.update(buffer)
            bytes_read += long(len(buffer))
            last_one = (len(buffer) != buffer_size)
            if bytes_read == current_size or last_one:
                result[long(bytes_read)] = hashobj.hexdigest()
                current_size = current_size*2L
            if last_one:
                break
    file.close()

    first = result[first_hash_size]
    full = result[file_size]
    del result[first_hash_size]
    if file_size != first_hash_size:
        del result[file_size]
    return first, full, result


def get_partial_sha1(fullpath, start_offset, bytes_to_hash,
                     buffer_size=long(4*1024*1024)):
    assert start_offset >= 0
    assert bytes_to_hash > 0

    file = open(fullpath, "r")
    file.seek(start_offset)
    hashobj = hashlib.sha1()
    bytes_left = bytes_to_hash
    while True:
        if bytes_left == 0:
            break
        length = buffer_size
        if length > bytes_left:
            length = bytes_left
        buffer = file.read(length)
        assert len(buffer) == length, [len(buffer), length]
        bytes_left -= length
        hashobj.update(buffer)
    file.close()
    return hashobj.hexdigest()

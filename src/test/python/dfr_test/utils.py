
import os

def write_binary(size, filename, offset=0):
    out = open(filename,"wb")
    for i in range(size):
        out.write(chr((i+offset) % 256))
    out.close()
    assert os.path.getsize(filename) == size



class Dir:
    def __init__(self, name, id=None):
        self.id = id
        self.name = name

    def __eq__(self, other):
        return (self.id == other.id
                and self.name == other.name)


class File:
    # pylint: disable=R0913
    def __init__(self, dirid, name, mtime, contentid, id=None):
        self.id = id
        self.dirid = dirid
        self.name = name
        self.mtime = mtime
        self.contentid = contentid

    def __eq__(self, other):
        return (self.id == other.id
                and self.dirid == other.dirid
                and self.name == other.name
                and self.mtime == other.mtime
                and self.contentid == other.contentid)


class Content:
    # pylint: disable=R0913
    def __init__(self, size, fullsha1, first1ksha1, partsha1s,
                 imageid, id=None):
        self.id = id
        self.size = size
        self.fullsha1 = fullsha1
        self.first1ksha1 = first1ksha1
        self.partsha1s = partsha1s
        self.imageid = imageid

    def get_part_hashs(self):
        res = {}
        for i in [x for x in self.partsha1s.split(" ") if x]:
            size, hash = i.split(":")
            res[long(size)] = hash
        return res

    def __eq__(self, other):
        return (self.id == other.id
                and self.fullsha1 == other.fullsha1
                and self.first1ksha1 == other.first1ksha1
                and self.partsha1s == other.partsha1s
                and self.imageid == other.imageid)


class Image:
    def __init__(self, sig1, sig2, id=None):
        self.id = id
        self.sig1 = sig1
        self.sig2 = sig2

    def __eq__(self, other):
        return (self.id == other.id
                and self.sig1 == other.sig1
                and self.sig2 == other.sig2)

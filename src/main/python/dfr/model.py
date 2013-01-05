

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
    def __init__(self, size, fullsha1, first1ksha1, partsha1s, id=None):
        self.id = id
        self.size = size
        self.fullsha1 = fullsha1
        self.first1ksha1 = first1ksha1
        self.partsha1s = partsha1s

    def __eq__(self, other):
        return (self.id == other.id
                and self.fullsha1 == other.fullsha1
                and self.first1ksha1 == other.first1ksha1
                and self.partsha1s == other.partsha1s)

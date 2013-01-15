

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
                 isimage, id=None):
        self.id = id
        self.size = size
        self.fullsha1 = fullsha1
        self.first1ksha1 = first1ksha1
        self.partsha1s = partsha1s
        self.isimage = isimage

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
                and self.isimage == other.isimage)


class ImageHash:
    def __init__(self, contentid, iht, hash, id=None):
        self.id = id
        self.contentid = contentid
        self.iht = iht
        self.hash = hash

    def __eq__(self, other):
        return (self.id == other.id
                and self.contentid == other.contentid
                and self.iht == other.iht
                and self.hash == other.hash)


class ImageCmp:
    # pylint: disable=R0913
    def __init__(self, contentid1, contentid2, iht, similarity, id=None):
        self.id = id
        self.contentid1 = contentid1
        self.contentid2 = contentid2
        self.iht = iht
        self.similarity = similarity

    def __eq__(self, other):
        return (self.id == other.id
                and self.contentid1 == other.contentid1
                and self.contentid2 == other.contentid2
                and self.iht == other.iht
                and self.similarity == other.similarity)


class ImageFeedback:
    def __init__(self, contentid1, contentid2, aresimilar, id=None):
        self.id = id
        self.contentid1 = contentid1
        self.contentid2 = contentid2
        self.aresimilar = aresimilar

    def __eq__(self, other):
        return (self.id == other.id
                and self.contentid1 == other.contentid1
                and self.contentid2 == other.contentid2
                and self.aresimilar == other.aresimilar)


TILE_CHUNK_SIZE = 1000


class Dir(object):
    def __init__(self, name, id=None):
        self.id = id
        self.name = name

    def __eq__(self, other):
        return (self.id == other.id
                and self.name == other.name)


class File(object):
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


class Content(object):
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


class ImageHash(object):
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


def encode_pairs(pairs, first1, first2):
    def encode_one(pair):
        contentid1, contentid2, similarity = pair
        assert 0 < similarity <= 1

        rel1 = contentid1-first1
        rel2 = contentid2-first2

        if similarity == 1.0:
            error = ".0"
        else:
            error = 1-similarity
            error = "%f" % error
            assert error.startswith("0.")
            error = error[1:7]

        return "%d,%d%s" % (rel1, rel2, error)
    return "|".join([encode_one(x) for x in pairs])


def decode_pairs(input, first1, first2):
    def decode_one(str):
        ids, error = str.split(".")
        error = float("0."+error)
        id1, id2 = ids.split(",")
        return (first1+int(id1),
                first2+int(id2),
                1-error)
    if input:
        return [decode_one(x) for x in input.split("|")]
    else:
        return []


class ImageCmp(object):
    # pylint: disable=R0913
    def __init__(self,
                 contentid1_first, contentid1_last,
                 contentid2_first, contentid2_last,
                 iht, similarity_threshold, pairs, id=None):
        self.id = id
        self.contentid1_first = contentid1_first
        self.contentid1_last = contentid1_last
        self.contentid2_first = contentid2_first
        self.contentid2_last = contentid2_last
        self.iht = iht
        self.similarity_threshold = similarity_threshold
        self.pairs = pairs

    def get_decoded_pairs(self):
        return decode_pairs(self.pairs, self.contentid1_first,
                            self.contentid2_first)

    def __eq__(self, other):
        return (self.id == other.id
                and self.contentid1_first == other.contentid1_first
                and self.contentid2_first == other.contentid2_first
                and self.iht == other.iht)


class ImageFeedback(object):
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


class Tile(object):
    def __init__(self, first1, last1, first2, last2):
        assert first1 <= first2
        self.first1 = first1
        self.last1 = last1
        self.first2 = first2
        self.last2 = last2
        self.pairs = []

    def add(self, similarity, contentid1, contentid2):
        assert self.first1 <= contentid1 <= self.last1
        assert self.first2 <= contentid2 <= self.last2
        assert 0 < similarity <= 1
        self.pairs.append((contentid1, contentid2, similarity))

    def get_encoded_pairs(self):
        return encode_pairs(self.pairs, self.first1, self.first2)

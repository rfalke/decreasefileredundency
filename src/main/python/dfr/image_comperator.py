
import sys
from dfr.model import ImageCmp, Tile, TILE_CHUNK_SIZE
from dfr.progress import Progress


def prepare_sig1(hash):
    return [int(x, 16) for x in hash.split(" ")]


def compare_sig1(hash1, hash2):
    if len(hash1) != len(hash2):
        return 0
    error = 0
    for i in range(len(hash1)):
        error += abs(hash1[i] - hash2[i])
    similarity = 1-error / float(2**17)
    return similarity


def prepare_hex_sig(hash):
    return int(hash, 16)


def compare_sig_by_comparing_256_bits(hash1, hash2):
    xor = hash1 ^ hash2
    distance = bin(xor).count("1")
    similarity = 1-distance/256.0
    assert 0 <= similarity <= 1, similarity
    return similarity


def compare_sig_by_comparing_64_bits(hash1, hash2):
    xor = hash1 ^ hash2
    distance = bin(xor).count("1")
    similarity = 1-distance/64.0
    assert 0 <= similarity <= 1, similarity
    return similarity


def get_tiles(contents):
    last_id = 0
    if contents:
        last_id = contents[-1].id
    first_ids = range(0, last_id, TILE_CHUNK_SIZE)
    res = []

    def get_last(first, index):
        if index == len(first_ids)-1:
            return last_id
        else:
            return first+TILE_CHUNK_SIZE-1

    for index1 in range(len(first_ids)):
        first1 = first_ids[index1]
        last1 = get_last(first1, index1)
        for index2 in range(index1, len(first_ids)):
            first2 = first_ids[index2]
            last2 = get_last(first2, index2)
            res.append(Tile(first1, last1, first2, last2))
    return res


class ImageComperator(object):
    def __init__(self, db, sig_type, verbose_progress=1):
        self.db = db
        self.verbose_progress = verbose_progress
        assert sig_type in [1, 2, 3, 4, 5]
        self.iht = sig_type
        if sig_type == 1:
            self.prepare = prepare_sig1
            self.compare = compare_sig1
        elif sig_type == 2:
            self.prepare = prepare_hex_sig
            self.compare = compare_sig_by_comparing_256_bits
        elif sig_type == 3:
            self.prepare = prepare_hex_sig
            self.compare = compare_sig_by_comparing_64_bits
        elif sig_type == 4:
            self.prepare = prepare_hex_sig
            self.compare = compare_sig_by_comparing_64_bits
        elif sig_type == 5:
            self.prepare = prepare_hex_sig
            self.compare = compare_sig_by_comparing_64_bits

    def _find_contents(self):
        contents = self.db.content.find(isimage=1)
        for content in contents:
            content.prepared_hash = None
            hashs = self.db.imagehash.find(contentid=content.id, iht=self.iht)
            if hashs:
                assert len(hashs) == 1
                if hashs[0].hash:
                    content.prepared_hash = self.prepare(hashs[0].hash)
        contents = [x for x in contents if x.prepared_hash is not None]
        return contents

    def get_open_tiles(self, contents, min_similarity):
        res = []
        all_tiles = get_tiles(contents)
        for tile in all_tiles:
            known = self.db.imagecmp.find(contentid1_first=tile.first1,
                                          contentid2_first=tile.first2,
                                          iht=self.iht)
            if not known:
                res.append(tile)
            else:
                assert len(known) == 1
                known = known[0]
                if known.similarity_threshold > min_similarity:
                    self.db.imagecmp.delete(known)
                    res.append(tile)
                elif (known.contentid1_last != tile.last1 or
                      known.contentid2_last != tile.last2):
                    self.db.imagecmp.delete(known)
                    res.append(tile)
        return res

    def save_tile(self, tile, min_similarity):
        self.db.imagecmp.save(
            ImageCmp(tile.first1, tile.last1, tile.first2,
                     tile.last2, self.iht, min_similarity,
                     tile.get_encoded_pairs()))
        self.db.commit()

    def calculate_tile(self, tile, min_similarity, contents_by_id):
        contents1 = [contents_by_id.get(x, None) for x in
                     range(tile.first1, tile.last1+1)]
        contents2 = [contents_by_id.get(x, None) for x in
                     range(tile.first2, tile.last2+1)]
        contents1 = [x for x in contents1 if x]
        contents2 = [x for x in contents2 if x]

        for cont1 in contents1:
            for cont2 in contents2:
                if cont1.id >= cont2.id:
                    continue
                sim = self.compare(cont1.prepared_hash,
                                   cont2.prepared_hash)
                if sim >= min_similarity:
                    tile.add(sim, cont1.id, cont2.id)
        self.save_tile(tile, min_similarity)

    def calculate_tiles(self, tiles, contents, min_similarity):
        contents_by_id = {}
        for i in contents:
            contents_by_id[i.id] = i

        prog = Progress(len(tiles), "Comparing images",
                        do_output=self.verbose_progress > 0)
        for tile in tiles:
            self.calculate_tile(tile, min_similarity, contents_by_id)
            prog.work()
        prog.finish()

    def ensure_that_all_tiles_are_calculated(self, min_similarity):
        contents = self._find_contents()
        contents.sort(lambda x, y: cmp(x.id, y.id))

        tiles = self.get_open_tiles(contents, min_similarity)
        if tiles:
            self.calculate_tiles(tiles, contents, min_similarity)
        else:
            self.progress("INFO: Have compared all image signatures.\n")

    def progress(self, msg, level=1):
        if level <= self.verbose_progress:
            sys.stderr.write(msg)
            sys.stderr.flush()

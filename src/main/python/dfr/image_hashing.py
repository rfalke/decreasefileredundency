
import Image
import tempfile
import os


def shell_quote(str):
    return "'%s'" % str.replace("'", "'\\''")


def get_image_signature1(filename):
    """
    based on the color histogram
    """
    image = Image.open(filename)
    histo = image.histogram()
    bands = -1
    if len(histo) in [3*256, 4*256]:
        bands = 3
    elif len(histo) == 256:
        bands = 1

    assert bands > 0, ("Can't get histogram for %s; histogram size is %d" %
                       (filename, len(histo)))

    subparts = 16
    width = 256/subparts
    value = []

    for band in range(bands):
        cstart = 256*band
        cend = 256*(band+1)

        band_total = float(sum(histo[cstart:cend]))

        raw_values = [-1]*256
        for j in range(cstart, cend):
            raw_values[j-cstart] = float(histo[j])/band_total

        values_for_band = []
        for j in range(subparts):
            values_for_band.append(sum(raw_values[j*width:(j+1)*width]))
        value += values_for_band

    assert -1 not in value
    return value


def get_image_signatures2(filenames):
    infile = tempfile.mkstemp()[1]
    out = open(infile, "w")
    for i in range(len(filenames)):
        out.write("%d %s\n" % (i, filenames[i]))
    out.close()

    outfile = tempfile.mkstemp()[1]
    os.system('src/main/perl/get_sig2.pl <%s >%s 2>/dev/null' % (
        shell_quote(infile), shell_quote(outfile)))

    hashs = []
    for line in open(outfile).readlines():
        id, hash = line.strip().split(" ", 1)
        id = int(id)
        assert len(hashs) == id
        if hash == "FAILED":
            hashs.append(None)
        else:
            assert len(hash) == 64
            hashs.append(hash)
    assert len(hashs) == len(filenames)
    return hashs

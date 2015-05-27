from PIL import Image
from PIL import ImageStat
import tempfile
import os
import ctypes

try:
    PHASH_LIB = ctypes.CDLL('libpHash.so.0', use_errno=True)
except OSError:
    PHASH_LIB = None


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


CAUSE_UNEQUAL_LINES = []


def get_image_signatures2(filenames):
    filedescr, inname = tempfile.mkstemp()
    os.close(filedescr)
    try:
        out = open(inname, "w")
        for i in range(len(filenames)):
            out.write("%d %s\n" % (i, filenames[i]))
        out.close()

        filedescr, outname = tempfile.mkstemp()
        os.close(filedescr)
        try:
            os.system('src/main/perl/get_sig2.pl <%s >%s 2>/dev/null' % (
                shell_quote(inname), shell_quote(outname)))
            hashs = []
            with open(outname) as infile:
                for line in infile.readlines():
                    id, hash = line.strip().split(" ", 1)
                    id = int(id)
                    assert len(hashs) == id
                    if hash == "FAILED":
                        hashs.append(None)
                    else:
                        assert len(hash) == 16
                        hashs.append(hash)
            # Guess that the perl script does not work because of missing deps
            if len(hashs) == 0:
                return None
            if len(hashs) != len(filenames) or CAUSE_UNEQUAL_LINES:
                raise KeyboardInterrupt()
            return hashs
        finally:
            os.remove(outname)
    finally:
        os.remove(inname)


def get_image_signature3(filename):
    """
    from http://folk.uio.no/davidjo/DifferenceHash.py

A program to calculate a hash of an image based on visual characteristics.
Author: David J. Oftedal.

Thanks to Dr. Neal Krawetz:
http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html
for the algorithm which formed the inspiration for this algorithm.
    """
    the_image = Image.open(filename)

    # Convert the image to 8-bit grayscale.
    the_image = the_image.convert("L")  # 8-bit grayscale

    # Squeeze it down to an 8x8 image.
    the_image = the_image.resize((8, 8), Image.ANTIALIAS)

    # Go through the image pixel by pixel.
    # Return 1-bits when a pixel is equal to or brighter than the previous
    # pixel, and 0-bits when it's below.

    # Use the 64th pixel as the 0th pixel.
    previous_pixel = the_image.getpixel((0, 7))

    difference_hash = 0
    for row in xrange(0, 8, 2):

        # Go left to right on odd rows.
        for col in xrange(8):
            difference_hash <<= 1
            pixel = the_image.getpixel((col, row))
            difference_hash |= 1 * (pixel >= previous_pixel)
            previous_pixel = pixel

        row += 1

        # Go right to left on even rows.
        for col in xrange(7, -1, -1):
            difference_hash <<= 1
            pixel = the_image.getpixel((col, row))
            difference_hash |= 1 * (pixel >= previous_pixel)
            previous_pixel = pixel

    return difference_hash


def get_image_signature4(filename):
    """
    from http://folk.uio.no/davidjo/AverageHash.py

A program to calculate a hash of an image based on visual characteristics.
Author: David J. Oftedal.

Thanks to Dr. Neal Krawetz:
http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html
for the algorithm which formed the inspiration for this algorithm.
    """
    the_image = Image.open(filename)

    # Convert the image to 8-bit grayscale.
    the_image = the_image.convert("L")  # 8-bit grayscale

    # Squeeze it down to an 8x8 image.
    the_image = the_image.resize((8, 8), Image.ANTIALIAS)

    # Calculate the average value.
    average_value = ImageStat.Stat(the_image).mean[0]

    # Go through the image pixel by pixel.
    # Return 1-bits when the tone is equal to or above the average,
    # and 0-bits when it's below the average.
    average_hash = 0
    for row in xrange(8):
        for col in xrange(8):
            average_hash <<= 1
            value = the_image.getpixel((col, row))
            average_hash |= 1 * (value >= average_value)

    return average_hash


def get_image_signature5(filename):
    """
From https://github.com/mk-fg/image-deduplication-tool

Uses pHash.
    """

    if PHASH_LIB is None:
        return None
    phash = ctypes.c_uint64()
    if PHASH_LIB.ph_dct_imagehash(filename, ctypes.pointer(phash)):
        return None
    return phash.value

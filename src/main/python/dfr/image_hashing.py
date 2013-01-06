
import Image


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

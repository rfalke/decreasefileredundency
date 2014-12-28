import unittest

from dfr.image_hashing import get_image_signature1, get_image_signatures2, \
    get_image_signature3, get_image_signature4, get_image_signature5, CAUSE_UNEQUAL_LINES


class Test(unittest.TestCase):

    def test_signature1(self):
        def get_sig(filename):
            return [int(x*100) for x in get_image_signature1("src/test/images/"+filename)]

        self.assertEqual(get_sig("all_white_rgb.png"), [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100])
        self.assertEqual(get_sig("all_black_rgb.png"), [
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(get_sig("all_red.png"), [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100,
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(get_sig("all_green.png"), [
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100,
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(get_sig("all_blue.png"), [
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100])
        self.assertEqual(get_sig("red_green_blue.png"), [
            66, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 33,
            66, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 33,
            66, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 33])

        self.assertEqual(get_sig("all_white_gray.png"), [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100])
        self.assertEqual(get_sig("all_black_gray.png"), [
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(get_sig("white_2_grays_and_black.png"), [
            25, 0, 0, 0, 0, 0, 25, 0, 0, 0, 0, 0, 0, 25, 0, 25])

        self.assertEqual(get_sig("python-logo-master-v3-TM.png"), [
            0, 0, 0, 3, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 89,
            0, 0, 0, 0, 0, 0, 6, 2, 0, 0, 0, 0, 0, 2, 0, 86,
            0, 0, 0, 0, 1, 0, 5, 0, 0, 0, 1, 0, 0, 0, 0, 86])

    def test_signature2(self):
        self.assertEqual(get_image_signatures2(
            ["src/test/images/all_black_rgb.png",
             "does not exists",
             "Makefile",
             "src/test/images/all_white_rgb.png",
             "src/test/images/pattern1.png"]),
            ['ffffffffffffffff',
             None,
             None,
             '0000000000000000',
             'f8f8f8ffff1f1f1f'])

    def test_signature2_for_coverage(self):
        CAUSE_UNEQUAL_LINES.append(1)
        try:
            get_image_signatures2(["src/test/images/all_black_rgb.png"])
            self.fail()
        except KeyboardInterrupt:
            pass

    def test_signature3(self):
        def assert_sig3(filename, expected):
            sig = get_image_signature3(filename)
            self.assertEqual("%016x" % sig, expected)
        assert_sig3("src/test/images/big/Organigramm_deut_2_Seewiesen-1_png.png", "0f042da70d87cfa7")
        assert_sig3("src/test/images/big/free-your-mind-Seite2.bmp", "37a733b533b737b7")
        assert_sig3("src/test/images/pattern1.png", "5d227f22a27f225d")
        assert_sig3("src/test/images/big/bird_bird_bird_png_format_by_chimonk-d37tayt.png", "622a4d0eab9b95d9")
        assert_sig3("src/test/images/big/sample_03.jpeg", "779ba5b1334b1993")
        assert_sig3("src/test/images/big/NENG1614.bmp", "799d2d52b8a5a4bb")
        assert_sig3("src/test/images/pattern2.png", "7fff7fffffff7fff")
        assert_sig3("src/test/images/white_2_grays_and_black.png", "80ff80ff80ff80ff")
        assert_sig3("src/test/images/big/Sunflower_Metalhead64_edited.png", "87070f0787878f8f")
        assert_sig3("src/test/images/big/nice-map-big.jpeg", "88eda7a64d637cec")
        assert_sig3("src/test/images/big/globe_west_2048.jpeg", "b1f8e0fcf26e78b9")
        assert_sig3("src/test/images/big/Nice-Bee.jpeg", "cd3ac3371dab6360")
        assert_sig3("src/test/images/big/Intercom_PCB_mit_Best.Druck.gif", "da68e4deda68e4de")
        assert_sig3("src/test/images/python-logo-master-v3-TM.png", "eb49b795afe1bbff")
        assert_sig3("src/test/images/red_green_blue.png", "f0f8f0f8f0f8f0f8")
        assert_sig3("src/test/images/pattern3.png", "ff7fff7f7f7fff7f")
        assert_sig3("src/test/images/all_black_gray.png", "ffffffffffffffff")
        assert_sig3("src/test/images/all_black_rgb.png", "ffffffffffffffff")
        assert_sig3("src/test/images/all_blue.png", "ffffffffffffffff")
        assert_sig3("src/test/images/all_green.png", "ffffffffffffffff")
        assert_sig3("src/test/images/all_red.png", "ffffffffffffffff")
        assert_sig3("src/test/images/all_white_gray.png", "ffffffffffffffff")
        assert_sig3("src/test/images/all_white_rgb.png", "ffffffffffffffff")

    def test_signature4(self):
        def assert_sig4(filename, expected):
            sig = get_image_signature4(filename)
            self.assertEqual("%016x" % sig, expected)
        assert_sig4("src/test/images/pattern2.png", "00000000ffffffff")
        assert_sig4("src/test/images/big/sample_03.jpeg", "000185bdfbc38d8b")
        assert_sig4("src/test/images/big/globe_west_2048.jpeg", "00387c7c787e3c00")
        assert_sig4("src/test/images/big/Intercom_PCB_mit_Best.Druck.gif", "007c7c00007c7c60")
        assert_sig4("src/test/images/pattern1.png", "0f0f0f0ff0f0f0f0")
        assert_sig4("src/test/images/big/NENG1614.bmp", "38382f1e9cbff4fc")
        assert_sig4("src/test/images/red_green_blue.png", "3838383838383838")
        assert_sig4("src/test/images/big/Organigramm_deut_2_Seewiesen-1_png.png", "8727008080e3e7ef")
        assert_sig4("src/test/images/big/free-your-mind-Seite2.bmp", "97c1b381818d81ff")
        assert_sig4("src/test/images/big/bird_bird_bird_png_format_by_chimonk-d37tayt.png", "e3446760a8f9f0f2")
        assert_sig4("src/test/images/big/Nice-Bee.jpeg", "eff8f0c080d7f93c")
        assert_sig4("src/test/images/white_2_grays_and_black.png", "f0f0f0f0f0f0f0f0")
        assert_sig4("src/test/images/big/nice-map-big.jpeg", "fef7f7ef0f0f0004")
        assert_sig4("src/test/images/python-logo-master-v3-TM.png", "ff9f818181ffffff")
        assert_sig4("src/test/images/big/Sunflower_Metalhead64_edited.png", "ffc783818183c3ff")
        assert_sig4("src/test/images/pattern3.png", "ffffffff00000000")
        assert_sig4("src/test/images/all_black_gray.png", "ffffffffffffffff")
        assert_sig4("src/test/images/all_black_rgb.png", "ffffffffffffffff")
        assert_sig4("src/test/images/all_blue.png", "ffffffffffffffff")
        assert_sig4("src/test/images/all_green.png", "ffffffffffffffff")
        assert_sig4("src/test/images/all_red.png", "ffffffffffffffff")
        assert_sig4("src/test/images/all_white_gray.png", "ffffffffffffffff")
        assert_sig4("src/test/images/all_white_rgb.png", "ffffffffffffffff")

    def test_signature5(self):
        def assert_sig5(filename, expected):
            sig = get_image_signature5(filename)
            self.assertEqual("%016x" % sig, expected)

        assert_sig5("src/test/images/big/nice-map-big.jpeg", "3929ca47ab8c956b")
        self.assertEqual(get_image_signature5("src/test/images/big/Intercom_PCB_mit_Best.Druck.gif"), None)
        self.assertEqual(get_image_signature5("Makefile"), None)
        self.assertEqual(get_image_signature5("does not exist"), None)

if __name__ == '__main__':
    unittest.main()

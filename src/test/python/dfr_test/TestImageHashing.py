
import unittest

from dfr.image_hashing import get_image_signature1, get_image_signatures2


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
            ['ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
             None,
             None,
             '0000000000000000000000000000000000000000000000000000000000000000',
             'ff80ff80ff80ff80ff80ff80ff80ffffffff01ff01ff01ff01ff01ff01ff01ff'])

if __name__ == '__main__':
    unittest.main()

import bit_hashing
import os,unittest,random
from tempdir import TempDir

class Test(unittest.TestCase):

    def test_empty_file(self):
        with TempDir() as d:
            tmpfn = os.path.join(d.name, 'input')
            self.write_binary(0, tmpfn)
            self.assertRaises(AssertionError, bit_hashing.get_sha1sums, tmpfn,os.path.getsize(tmpfn),1024)

    def test_1023_file(self):
        with TempDir() as d:
            tmpfn = os.path.join(d.name, 'input')
            self.write_binary(1023, tmpfn)
            self.assertRaises(AssertionError, bit_hashing.get_sha1sums, tmpfn,os.path.getsize(tmpfn),1024)

    def test_1024_file(self):
        with TempDir() as d:
            tmpfn = os.path.join(d.name, 'input')
            self.write_binary(1024, tmpfn)
            hashs=bit_hashing.get_sha1sums(tmpfn,os.path.getsize(tmpfn),1024)
            self.assertEqual(hashs, ('5b00669c480d5cffbdfa8bdba99561160f2d1b77', '5b00669c480d5cffbdfa8bdba99561160f2d1b77', {}))

    def test_1025_bytes_file(self):
        with TempDir() as d:
            tmpfn = os.path.join(d.name, 'input')
            self.write_binary(1025, tmpfn)
            hashs=bit_hashing.get_sha1sums(tmpfn,os.path.getsize(tmpfn),1024)
            self.assertEqual(hashs, ('5b00669c480d5cffbdfa8bdba99561160f2d1b77', '409c9978384c2832af4a98bafe453dfdaa8e8054', {}))

    def test_2049_bytes_file(self):
        with TempDir() as d:
            tmpfn = os.path.join(d.name, 'input')
            self.write_binary(2049, tmpfn)
            hashs=bit_hashing.get_sha1sums(tmpfn,os.path.getsize(tmpfn),1024)
            self.assertEqual(hashs, ('5b00669c480d5cffbdfa8bdba99561160f2d1b77', '170751534f1a95fd80a7a25787ecad2b60368e0a',
                                     {2048L: 'f10ccfde60c17db26e7d85d35665c7661dbbeb2c'}))

    def write_binary(self,size,filename):
        f=open(filename,"wb")
        for i in range(size):
            f.write(chr(i % 256))
        f.close()
        assert os.path.getsize(filename)==size
        

if __name__ == '__main__':
    unittest.main()

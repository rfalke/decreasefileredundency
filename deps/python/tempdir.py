import tempfile
import shutil

class TempDir(object):
    """ class for temporary directories
creates a (named) directory which is deleted after use.
All files created within the directory are destroyed
Might not work on windows when the files are still opened
"""
    def __init__(self, suffix="", prefix="tmp", basedir=None):
        self.name = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=basedir)

    def __del__(self):
        if "name" in self.__dict__:
            self.__exit__(None, None, None)

    def __enter__(self):
        return self

    def __exit__(self, *errstuff):
        return self.dissolve()

    def dissolve(self):
        """remove all files and directories created within the tempdir"""
        if self.name:
            shutil.rmtree(self.name)
        self.name = ""

    def __str__(self):
        if self.name:
            return "temporary directory at: %s" % (self.name,)
        else:
            return "dissolved temporary directory"



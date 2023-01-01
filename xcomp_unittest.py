import unittest
import xcomp
from io import StringIO
from unittest.mock import patch


class Arguments:

    def __init__(
        self,
        path1: str,
        path2: str,
        cache_file: list[str] | None = None,
        recursive: bool | None = None,
        verbose: bool | None = None
    ):
        self.path1 = path1
        self.path2 = path2
        self.cache_file = cache_file
        self.recursive = recursive
        self.verbose = verbose


class Tests(unittest.TestCase):

    def test_paths_dont_exist(self):
        args = Arguments("absent_file1", "absent_file2")
        with self.assertRaises(SystemExit):
            xcomp.main(args)

    def test_path1_does_not_exist(self):
        args = Arguments("absent_file1", "./fixtures/directory1/file1")
        with self.assertRaises(SystemExit):
            xcomp.main(args)

    def test_path2_does_not_exist(self):
        args = Arguments("./fixtures/directory1/file1", "absent_file2")
        with self.assertRaises(SystemExit):
            xcomp.main(args)

    def test_hexdigest(self):
        self.assertEqual(
            xcomp.xxh3('./fixtures/directory1/file1'), "8bb820c8bfd319e9"
        )

    def test_redundant_single_file(self):
        args = Arguments(
            'fixtures/directory1/file1',
            'fixtures/directory2/file1'
        )
        with patch('sys.stdout', new=StringIO()) as xcomp_out:
            result = (
                "=8bb820c8bfd319e9 ['/home/rodrigo/Documents/code/python/"
                "xcomp/fixtures/directory1/file1', '/home/rodrigo/Documents/"
                "code/python/xcomp/fixtures/directory2/file1']\n"
                "=input files are redundant\n"
            )
            xcomp.main(args)
            self.assertEqual(xcomp_out.getvalue(), result)


if __name__ == '__main__':
    unittest.main()

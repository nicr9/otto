import unittest
import StringIO
import sys

from otto.utils import *

class TestUtil(unittest.TestCase):
    def setUp(self):
        # Monkey patch STDOUT
        self.stdout = StringIO.StringIO()
        self._real_stdout = sys.stdout
        sys.stdout = self.stdout

    def tearDown(self):
        sys.stdout = self._real_stdout

    def test_bail_no_message(self):
        expected = "\x1b[1m\nExiting...\x1b[0m\n"
        with self.assertRaises(SystemExit):
            bail()

        self.assertEqual(expected, self.stdout.getvalue())

    def test_bail_with_message(self):
        expected = "\x1b[1m\nExiting: The cake is a lie\x1b[0m\n"
        with self.assertRaises(SystemExit):
            bail("The cake is a lie")

        self.assertEqual(expected, self.stdout.getvalue())


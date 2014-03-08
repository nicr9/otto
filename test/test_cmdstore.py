import unittest

from os.path import dirname, join
from tempfile import NamedTemporaryFile as TF

from otto.config import CmdStore
from otto.cmds import BASE_CMDS

TEST_DIR = dirname(__file__)
DEFAULT_MAP = map = {
        'base': BASE_CMDS.keys(),
        }

PACK_NAME = 'test'
PACK_DIR = join(TEST_DIR, '.otto/test')
PACK_MAP = {
        PACK_NAME: [
            'test1',
            'test2',
            ],
        }

class TestCmdStore(unittest.TestCase):
    def setUp(self):
        self.target = CmdStore()
        self.target.init(BASE_CMDS)

    def tearDown(self):
        del self.target

    def check_store(self, map):
        self.assertTrue(self.target._ready)
        self.assertEqual(self.target.pack_keys, set(map.keys()))
        for pack, cmds in map.iteritems():
            self.assertEqual(self.target.pack_cmds[pack].keys(), cmds)

    def test_init(self):
        self.check_store(DEFAULT_MAP)

    def test_loadpack(self):
        self.target.loadpack(PACK_NAME, PACK_DIR)

        map = DEFAULT_MAP.copy()
        map.update(PACK_MAP)
        self.check_store(map)

    def test_lookup(self):
        self.target.loadpack(PACK_NAME, PACK_DIR)
    
        self.assertEqual(self.target.lookup('test1'), ('test', 'test1'))
        self.assertEqual(self.target.lookup('test2'), ('test', 'test2'))
        self.assertEqual(self.target.lookup('test:test1'), ('test', 'test1'))
        self.assertEqual(self.target.lookup('test:test2'), ('test', 'test2'))

        with self.assertRaises(SystemExit):
            self.target.lookup('test3')

if __name__ == "__main__":
    unittest.main()

import unittest

from os.path import dirname, join, isfile
from tempfile import NamedTemporaryFile as TF

from otto.config import CmdStore
from otto.cmds import BASE_CMDS
from otto.utils import isOttoCmd

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
    @classmethod
    def setUpClass(cls):
        from otto.utils import shell, ChangePath, info
        info("Setting up CmdStore tests...")
        with ChangePath('otto/test/'):
            shell('otto dr')

    @classmethod
    def tearDownClass(cls):
        from otto.utils import ConfigFile, info
        info("Cleaning up after CmdStore tests...")
        with ConfigFile('otto/test/.otto/config.json') as config:
            config['packs']['test'] = ''

    def setUp(self):
        self.target = CmdStore()
        self.target.init_base(BASE_CMDS)

    def tearDown(self):
        del self.target

    def check_store(self, map):
        self.assertEqual(self.target.pack_keys, set(map.keys()))
        for pack, cmds in map.iteritems():
            self.assertEqual(self.target.cmds_by_pack[pack].keys(), cmds)

    def test_init(self):
        self.check_store(DEFAULT_MAP)

    def test_add_cmd(self):
        with TF() as _file:
            self.target._add_cmd('a', 'b', _file.name)
            self.assertTrue('a' in self.target.pack_keys)
            self.assertTrue('b' in self.target.cmds_by_pack['a'])
            self.assertEqual(self.target.cmds_by_pack['a']['b'], _file.name)

    def test_load_pack(self):
        self.target.load_pack(PACK_NAME, PACK_DIR)

        map = DEFAULT_MAP.copy()
        map.update(PACK_MAP)
        self.check_store(map)

    def test_load_cmd(self):
        # Make sure _load_cmd will always do nothing to a base cmd
        for cmd_name, cmd_ref in BASE_CMDS.iteritems():
            result = self.target._load_cmd('base', cmd_name, cmd_ref)
            self.assertTrue(isOttoCmd(result))

        # Make sure all refs for installed packs are paths...
        self.target.load_pack(PACK_NAME, PACK_DIR)
        test_pack = self.target.cmds_by_pack[PACK_NAME]
        for cmd_name, cmd_ref in test_pack.iteritems():
            self.assertTrue(isfile(cmd_ref))

            # ... and that they return from _load_cmd as an OttoCmd
            result = self.target._load_cmd(PACK_NAME, cmd_name, cmd_ref)
            self.assertTrue(isOttoCmd(result))

    def test_lookup(self):
        self.target.load_pack(PACK_NAME, PACK_DIR)
    
        self.assertEqual(self.target.lookup('test1'), ('test', 'test1'))
        self.assertEqual(self.target.lookup('test2'), ('test', 'test2'))
        self.assertEqual(self.target.lookup('test:test1'), ('test', 'test1'))
        self.assertEqual(self.target.lookup('test:test2'), ('test', 'test2'))

        with self.assertRaises(SystemExit):
            self.target.lookup('test3')


from lament import *
from otto.cmdstore import CmdStore

class CmdsConfig(LamentConfig):
    @config('cmds', dict)
    def cmds(self, config, obj):
        config.update(obj)

class OttoConfig(LamentConfig):
    @config('packs', CmdStore)
    def packs(self, config, obj):
        for key, val in obj.iteritems():
            config.loadpack(key, val)
        return config

    @export('packs')
    def ex_packs(self, config):
        return config.export()

    @config('remember', dict)
    def remember(self, config, obj):
        config.update(obj)
        return config

    @config('tone', str)
    def tone(self, config, obj):
        return obj

from modloader.modclass import Mod, loadable_mod
from link import run_linkfile

@loadable_mod
class AWSWMod(Mod):
    @staticmethod
    def mod_info():
        return ("Linkfile Example Mod", "v0.0", "4onen", False)

    @staticmethod
    def mod_load():
        run_linkfile('example.link')
        run_linkfile('adine_cg.link')
        run_linkfile('loremipsum.link')

    @staticmethod
    def mod_complete():
        pass
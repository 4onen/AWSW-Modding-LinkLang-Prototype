from modloader import modast, modinfo
from modloader.modclass import Mod, loadable_mod
from modloader.modgame import base as ml

from link import run_linkfile

@loadable_mod
class AWSWMod(Mod):
    @staticmethod
    def mod_info():
        return ("Linkfile Example Mod", "v0.0", "4onen", False)

    @staticmethod
    def mod_load():
        run_linkfile('example.link')

    @staticmethod
    def mod_complete():
        pass
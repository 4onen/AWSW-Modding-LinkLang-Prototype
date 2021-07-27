from modloader.modclass import Mod, loadable_mod

@loadable_mod
class AWSWMod(Mod):
    @staticmethod
    def mod_info():
        return ("Linkfile Example Mod", "v0.0", "4onen", False)

    @staticmethod
    def mod_load():
        pass

    @staticmethod
    def mod_complete():
        pass
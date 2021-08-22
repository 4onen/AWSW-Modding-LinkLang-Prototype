import gc
from modloader.modclass import Mod, loadable_mod
from modloader import modast

@loadable_mod
class AWSWMod(Mod):
    @staticmethod
    def mod_info():
        return ("Linkmod", "v1.0", "4onen", False)

    @staticmethod
    def mod_load():
        pass

    @staticmethod
    def mod_complete():
        # Fixing EvilChaosKnight's bad ASTHook use.
        # Do not, I repeat, DO NOT, hook to the main menus like he does.
        mainmenu = modast.find_label("mainmenu")
        bad_hooks = (node for node in gc.get_objects() if isinstance(node, modast.ASTHook) and node.next is mainmenu)
        for hook in bad_hooks:
            hook.unhook()
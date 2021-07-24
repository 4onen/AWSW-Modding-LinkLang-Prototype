# AWSW Modding LinkLang

*LinkLang* is a crazy idea I had last night for making it easier to link *Angels with Scaly Wings* mods into the base game. At the moment, the process is really unapproachable because people are just told to "figure it out from code examples."

Well, I'm not changing that, but I'm making the code much easier to understand! Here's the simplest possible mod with *LinkLang*:

*short_example.link*
```
find say "I thought they sent you away after everything that's going on."
call short_example_mod_target
```

*short_example.rpy*
```
label short_example_mod_target:
    c "It takes more than that to get rid of me!"
    return
```

*\_\_init\_\_.py*
```py
from modloader.modclass import Mod, loadable_mod
from link import run_linkfile

@loadable_mod
class AWSWMod(Mod):
    @staticmethod
    def mod_info():
        return ("Linkfile Short Example Mod", "v0.0", "4onen", False)

    @staticmethod
    def mod_load():
        run_linkfile('short_example.link')

    @staticmethod
    def mod_complete():
        pass
```

That's it! But really, that's just the tip of the iceberg. I'll write a larger language reference in a day or two when I have time (I shouldn't have spent the time I did today!) but for now you can look at the testing mod for a fuller picture.

Word of warning: Do _not_ use this as it currently stands. I literally just wrote this. It has one test case. If you do choose to use it, no warranty express or implied. Just don't touch it quite yet please.
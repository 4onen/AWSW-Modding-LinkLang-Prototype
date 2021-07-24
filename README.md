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

Language reference:

+ `find ...` - Commands that search the entire Ren'Py AST for a given node.
    + Optional Arguments:
        + `as <storeto>` save the node to the variable name `storeto` in addition to setting the current node. (Useful for saving a node to do an operation on later, for example calling from a node but returning later.)
    + Subcommands:
        + `find label <label>` - Finds the given label.
        + `find jump <label>` - Finds a node that jumps to the given label. (No ordering guarantees!)
        + `find menu <option>` - Finds a menu by one of its options. (Make sure it's a unique one!)
        + `find show <image> <attributes> <like> <normal> <b>` - Finds a point when an image is shown with a `show` statement. (Good for hooking the appearance of unique character graphics!)
        + `find hide <image> <attributes> <like> <flirty> <old>` - Finds a point when an image is hidden. (See above. Remember, match the attributes used in the `hide` exactly, if any or none!) 
        + `find say <option>` - Finds any instance of a character or the narrator saying something. (Again, no ordering guarantees if it's not unique!)
        + `find python <statement>` - Finds an instance of a python statement in the Ren'Py code of the game. Any statement that is more complex than mere letters must be wrapped in quotation marks (" or ').
+ `search ...` - Commands that search forward from the current node.
    + Optional arguments:
        + `as <storeto>` save the node to the variable name `storeto` in addition to setting the current node. (Useful for saving a node to do an operation on later, for example calling from a node but returning later.)
        + `from <variable>` start searching from a node that is not the current node, saved in a local variable.
        + `for <number>` sets how many nodes forward the search will attempt to look before raising an error. (Default: 200)
    + Subcommands: `say`,`if`,`menu`,`show`,`hide`,`scene`,`label`
        + These are the same as in `find ...`, but start from the current node and step forward with `node.next`. This means, instead of searching the whole Ren'Py AST, it will only search the current scene! The downside is these `search ...` commands will step _over_ if statements and menus. To look inside them, see `branch`.
+ `call <label>` - Links the current node to call a given label, as if by inserting a `call` statement at that spot.
    + Optional arguments:
        + `from <variable>` link the call from a node that is not the current node.
        + `return <variable>` when `return` is called inside the called label, will return to the node stored in *variable* rather than to the next node.
+ `jump <label>` - Links the current node to jump to a given label, as if by inserting a `jump` statement at that spot.
    + Optional arguments:
        + `from <variable>` link the jump from a node that is not the current node.
+ `branch <option>` - Descend into a branch of an If statement or Menu. Sets the current node to the first node inside that branch.
    + If the current node is a `renpy.ast.If`, will compare the condition text _exactly_ (excluding whitespace at the beginning.)
    + If the current node is a `renpy.ast.Menu`, will compare the text _exactly_ against the menu options.
    + Optional arguments:
        + `as <storeto>` save the node to the variable name *storeto* in addition to setting as the current node.
+ `change <option> to <newoption>` - Change an option's label or condition.
    + If the current node is a `renpy.ast.If`, will compare the condition text _exactly_ and, upon finding a match, replace the condition with the text in *newoption*.
    + If the current node is a `renpy.ast.Menu`, will compare the choice text _exactly_ and, upon finding a match, repalce the choice text with the text in *newoption*.
+ ... 3 more commands to be documented...

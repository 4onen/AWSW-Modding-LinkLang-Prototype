# No more intuition, Bryce.
find label brycefirst
search if
change "persistent.brycegoodending == True" to inaccessible

# No auto-save, Seb.
find label c4cont2
search if
search if
branch "mcfirst == True":
    search say "Should I? It's hard to think about something fun when I'm wrapped up in this investigation."
    search if "persistent.sebastianfail == False"
    change "persistent.sebastianfail == False" to inaccessible

# Depression is a deep cycle, Remy.
find label c4library
search if
change "persistent.remygoodending == True" to inaccessible
find label chapter5
search if "persistent.remygoodending == False"
change "persistent.remygoodending == False" to True
find label chapter4
search if
change "persistent.remygoodending == False" to True

# Watch your step, Lorem.
find label c4witness
search if "persistent.loremgoodending"
change "persistent.loremgoodending" to "persistent.loremgoodending and loremstatus != \"bad\""

find label chapter4
search if "persistent.loremgoodending == False"
change "persistent.loremgoodending == False" to True
branch True:
    change "loremstatus == \"none\"" to "loremstatus == \"none\" and persistent.loremgoodending == False"

# Break a wing, Adine.
find label chapter4
search if "persistent.adinegoodending == False"
change "persistent.adinegoodending == False" to True
branch True:
    change "adine2unplayed == True" to "adine2unplayed == True and persistent.adinegoodending == False"
find label chapter5
search if "persistent.adinegoodending == False"
change "persistent.adinegoodending == False" to "persistent.adinegoodending == False or adinestatus == \"bad\""
branch "persistent.adinegoodending == False or adinestatus == \"bad\"":
    branch "adine4unplayed == True":
        change "remygoodending == False" to "remygoodending == False or adinestatus == \"bad\""


# You work too much, Anna.
find label chapter3
search say "Well, what is it?"
search if
change "persistent.annagoodending == True" to "persistent.annagoodending == True and annastatus != \"bad\""

# You're not a good enough person, [player_name].
find label chapter5
callto impermanence_end_fix if any((remydead, annadead, loremdead, brycedead, adinedead))
search if "persistent.trueending"
change "persistent.trueending" to inaccessible
search scene o4
callto impermanence_end_fix if any((remydead, annadead, loremdead, brycedead, adinedead))

label impermanence_end_fix:
    $ trueselectable = False
    return
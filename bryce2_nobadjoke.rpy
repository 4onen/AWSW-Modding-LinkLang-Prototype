find label bryce2
search scene pad
search if "nodrinks == False"
change "nodrinks == False" to "nodrinks == False and brycestatus != \"good\""
add else branch link_example_bryce2_jokechoice
search say "Don't mind the chaos, this is just a temporary arrangement."
link link_example_bryce2_dontmindarrangement

label link_example_bryce2_jokechoice:
    if nodrinks == False:
        menu:
            "[[Make a joke about last time.]":
                return
            "[[Apologize again for last time.]":
                c "I just wanted to say again, I'm sorry for my part in letting the other night get as far as it did."
                Br "I thought we agreed not to mention that."
                c "Oops, right."
            "[[Step in.]":
                pass
    m "I stepped inside Bryce's apartment."
    $ renpy.pop_call()

label link_example_bryce2_dontmindarrangement:
    pass

search say "So, what do you usually do for fun in your world?"
search menu
add "Not drink." branch link_example_bryce2_antidrink if nodrinks == True
label link_example_bryce2_antidrink:
    python:
        renpy.pause(0.5)
        bryce2mood -= 1
    Br stern "You're walking on thin ice with that one."
    c "I'm sorry, I just don't see drinking all the time as--"
    Br "There's no need to bring that up right now."
    c "Okay. How about you? What do you do for fun that isn't drinking?"
    show bryce stern with dissolve
    m "Bryce seemed at least a little relieved I left him an out to change the subject."
search say "Different things. A little bit of this, a little bit of that... You know how it is."
link link_example_bryce2_antidrink_aftermenu
label link_example_bryce2_antidrink_aftermenu:
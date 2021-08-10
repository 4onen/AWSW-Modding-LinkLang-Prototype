init:
    find label seccont
    # search scene chap1
    # search show cgseb
    search say "Welcome to our establishment. My name's Adine, and I'll be your waitress today. What can I bring you two?" for 1000
    callto label link_example_show_cg_adine

label link_example_show_cg_adine:
    scene black with dissolve
    $ renpy.pause (0.3)
    show cgadine at Pan((0, 120), (0, 0), 7.0) with dissolvemed
    $ renpy.pause(5.0)
    scene cafe
    show reza normal at Position(xpos = 0.7)
    show adine normal b flip at left
    with dissolvemed
    Ad "Are you going to keep staring?"
    c "Sorry, this is all just very new to me."
    return
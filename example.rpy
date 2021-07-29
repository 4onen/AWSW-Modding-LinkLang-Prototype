init:
    # Adine1 adjustments
    find label adine1
    search say "(Well, that was quick.)" # Test comment
    callto link_example_adine1_expected_longer

    search if
    branch "chapter3unplayed == False":
        search say "I thought they sent you away after everything that's going on."
        jumpto link_example_adine1_alt_greeting
    branch else:
        search menu
        add "Sure is." branch link_example_adine1_alt_greeting
        branch "I thought we were over this, but at least you don't reduce me to my species anymore.":
            search show
            callto link_example_adine1_notserious
            search show
            jumpto link_example_adine1_alt_greeting

    # Hook a link for rude players to end up back with more choice.
    search menu
    branch "Well, thanks for the food.":
        search menu
        branch "This isn't a homeless shelter.":
            link link_example_adine1_alt_greeting_rude_labelback

    next
    link link_example_adine1_alt_greeting_labelback

    search if
    change "persistent.adine1skip == True" to inaccessible

    search say "Feel right at home. I better eat this before it gets cold." as eatbeforecold
    search say "I sat down at the table and started eating my food while Adine decided to take a seat opposite of myself."
    next
    callto link_example_adine1_alt_sitting from eatbeforecold return here

label link_example_adine1_expected_longer:
    c "(I expected it to take longer to get here.)"
    c "(Not sure why, when some dragons can fly.)"
    return

label link_example_adine1_notserious:
    m "Though my tone was deadpan serious, she seemed to take it as a joke."
    return

label link_example_adine1_alt_greeting:
    Ad annoyed b "Here's your food. Now I have got to get out of this rain a few minutes."
    Ad "I'm coming in."
    menu:
        "Uh. Okay.":
            Ad normal b "Thanks."
            jump link_example_adine1_alt_greeting_labelback
        "I'm not sure...":
            jump link_example_adine1_alt_greeting_rude_labelback

label link_example_adine1_alt_greeting_labelback:
    pass # This is made to go to the right point by the link file

label link_example_adine1_alt_greeting_rude_labelback:
    pass # This is made to go to the right point by the link file

label link_example_adine1_alt_sitting:
    play sound "fx/chair.wav"
    m "I sat down at the table and started eating my food."
    m "After a moment, Adine decided to take a seat opposite me."
    return
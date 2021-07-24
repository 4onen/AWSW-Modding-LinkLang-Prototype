

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
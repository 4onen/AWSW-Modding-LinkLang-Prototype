init:
    find hide "meetingipsum"
    search if
    branch else:
        search say "You don't mind if I take a seat, right?"
        callto link_example_loremipsum_knoweachother

    search say "I'm sorry, [player_name]. This is my roommate and long-time best friend, Ipsum."
    callto link_example_loremipsum_dontknoweachother

label link_example_loremipsum_knoweachother:
    c "Wait, Lorem, Ipsum, you know each other?"
    Ip happy "Of course. Lorem is my roommate."
    Lo relieved flip "He means he's {i}my{/i} roommate."
    Ip normal "It's all a matter of perspective."

    label link_example_loremipsum_dolor:
    c "Do you two know a dragon named Dolor?"
    show lorem think flip with dissolve
    Ip think "No, why do you ask?"
    c "Lorem... Ipsum... Dolor sit amet..."
    Lo shy flip "What are you talking about? That chanting sounds creepy."
    Ip "It is interesting indeed."
    return

label link_example_loremipsum_dontknoweachother:
    if c4witnessavailable == True:
        c "Wait, Lorem? Ipsum?"
        Ip happy "Yes, of course. We are, after all, roommates."
    return
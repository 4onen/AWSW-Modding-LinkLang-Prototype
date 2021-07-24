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
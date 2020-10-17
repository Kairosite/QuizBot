from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import deque
import random

insults = {
    "muppet",
    "mango",
    "dip",
    "fool",
    "prat",
    "wazzock",
    "numpty",
    "goon",
    "dork",
    "dolt",
    "pudding-head",
    "goof",
    "spud",
    "nit",
    "twit",
    "pillock",
    "mug",
    "dingbat",
    "twonk",
    "balloon",
    "clot"
}

prefixes = {
    "complete",
    "utter",
    "total",
    "bleeding",
    "absolute",
    "spectacular",
    "damned"
}


def get_insult():
    selection = deque(prefixes.copy())
    random.shuffle(selection)
    prefix = ""
    while selection and (random.randrange(1, 21) == 20):
        prefix += selection.pop() + " "

    insult = random.choice(tuple(insults))
    return prefix + insult

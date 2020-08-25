from munch import Munch

params = {
    "discord": {
        "token": "FromDiscord"  # get token
    }
}

config = Munch.fromDict(params)

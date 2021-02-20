from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from qb_database import CachedGame
from collections import OrderedDict


class GameCache():
    __instance = None

    # Yield a singleton
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, max_size=16):
        if (self.__initialized):
            return
        else:
            self.max_size = max_size
            self.cache = OrderedDict()
            self.__initialized

    def get_game(self, channel_id):
        if channel_id in self.cache:
            self.cache.move_to_end(channel_id)
            return self.cache[channel_id]
        else:
            self.cache[channel_id] = CachedGame(channel_id)
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
        return self.cache[channel_id]

    def writeback(self):
        for cached_game in self.cache.values():
            cached_game._writeback_()

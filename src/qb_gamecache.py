from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from qb_database import CachedGame
from collections import OrderedDict, namedtuple
from time import monotonic

GameEntry = namedtuple("GameEntry", ["game", "last_accessed"])


class GameCache():
    __instance = None

    # Yield a singleton
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, max_size=128, time_out=300):
        if (self.__initialized):
            return
        else:
            self.max_size = max_size
            self.time_out = time_out
            self.cache = OrderedDict()
            self.__initialized = True

    def get_game(self, channel_id):
        if channel_id in self.cache:
            self.cache.move_to_end(channel_id)
            self.cache[channel_id].last_accessed = monotonic()
        else:
            self.cache[channel_id] = GameEntry(
                CachedGame(channel_id),
                monotonic()
            )
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
        return self.cache[channel_id].game

    def timeout(self):
        cut_off = monotonic() - self.time_out
        while self.cache:
            left_most = self.cache.popitem(last=False)
            if left_most.last_accessed() > cut_off:
                channel_id = left_most.game.channel_id
                self.cache[channel_id] = left_most
                self.cache.move_to_end(channel_id, last=False)
                break

    def writeback(self):
        for cached_game in self.cache.values():
            cached_game._writeback_()

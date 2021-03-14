from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from qb_gamecache import GameCache
from discord.ext.commands import Cog, group, Greedy
from discord.ext.tasks import loop
from discord import Member


class QuizBotInterface(Cog):

    def __init__(self):
        self.game_cache = GameCache()
        self.writeback_task.start()
        self.timeout_task.start()

    def cog_unload(self):
        self.writeback_task.cancel()
        self.timeout_task.cancel()

    @group(
        name="start"
    )
    async def start(self, ctx, players: Greedy[Member]):
        # TODO
        pass

    @start.game(
        name="game"
    )
    async def start_game(self, ctx, players: Greedy[Member]):
        await self.start(ctx, *players)

    @loop(minutes=5)
    async def writeback_task(self):
        self.game_cache.writeback()

    @loop(minutes=1)
    async def timeout_task(self):
        self.game_cache.timeout()

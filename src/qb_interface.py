from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from qb_database import QuizBotDatabaseException
from qb_gamecache import GameCache
from discord.ext.commands import Cog, group, command, Greedy
from discord.ext.tasks import loop
from discord import Member
import inspect
from typing import Optional


class QuizBotInterface(Cog):

    def __init__(self):
        self.game_cache = GameCache()
        self.writeback_task.start()
        self.timeout_task.start()

    def cog_unload(self):
        self.writeback_task.cancel()
        self.timeout_task.cancel()

    def game_only(self, func):
        async def wrapper(ctx, *args, **kwargs):
            try:
                game = self.game_cache.get_game(ctx.channel.id)
                await func(game, ctx, *args, **kwargs)
            except QuizBotDatabaseException:
                await ctx.send("This command requires a game to work.")

        wrapper.__name__ = func.__name__
        sig = inspect.signature(func)
        wrapper.__signature__ = sig.replace(
            parameters=tuple(sig.parameters.values())[2:]
        )
        return wrapper

    @group(
        name="start",
        case_insensitive=True,
        invoke_without_command=True,
        pass_context=True
    )
    async def start(self, ctx, players: Greedy[Member]):
        # TODO
        pass

    @start.game(
        name="game"
    )
    async def start_game(self, ctx, players: Greedy[Member]):
        await self.start(ctx, *players)

    @group(
        name="add",
        case_insensitive=True,
        invoke_without_command=True,
        pass_context=True
    )
    @game_only
    async def add_root(
            self,
            game,
            ctx,
            players: Greedy[Member],
            team_name: Optional[str]
    ):
        if team_name:
            if captain_id := game.get_captain_id(team_name):
                for player in players:
                    game.add_player(player.id)
                    game.set_player_team(player.id, captain_id)
                if len(players) > 1:
                    await ctx.send(
                        f"All players successfully added to {team_name}."
                    )
                else:
                    await ctx.send(
                        f"{player[0].display_name} successfully"
                        f" added to {team_name}."
                    )
            else:
                await ctx.send(
                    "I can't find a team with that name, "
                    "consider checking the spelling."
                )
        else:
            perfect = True
            success = False
            for player in players:
                if not game.add_player(player.id):
                    await ctx.send(
                        f"{player.display_name} is already in the game."
                    )
                    perfect = False
                else:
                    success = True
            if perfect and len(players) > 1:
                await ctx.send("All players added successfully.")
            elif perfect:
                await ctx.send("Player added successfully.")
            elif success:
                await ctx.send("All other players added successfully.")
            else:
                await ctx.send(
                    "Every player listed was already in the game, "
                    "you may be looking for a different command."
                )

    @command(
        name="add_player",
        usage=["user-mention"]
    )
    @game_only
    async def add_player(self, game, ctx, player: Member):
        if game.add_player(player.id):
            ctx.message.add_reaction("✅")
        else:
            ctx.send(player.mention + " is already in the game.")

    @loop(minutes=5)
    async def writeback_task(self):
        self.game_cache.writeback()

    @loop(minutes=1)
    async def timeout_task(self):
        self.game_cache.timeout()

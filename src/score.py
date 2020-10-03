from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from discord.ext import commands
from collections import defaultdict
from operator import itemgetter


class Scores(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.scores = defaultdict(lambda: 0)

    @commands.command(
        name="update",
        aliases=["upt"]
    )
    async def update_score(self, ctx, score: int):
        self.scores[ctx.author] += score
        return

    @commands.command(
        name="get",
        aliases=["g"]
    )
    async def get_score(self, ctx):
        await ctx.send(self.pretty_format_scores())
        return

    @commands.command(
        name="reset",
        aliases=["r"]
    )
    async def reset_score(self, ctx):
        await ctx.send(self.pretty_format_scores())
        self.scores.clear()
        return

    def pretty_format_scores(self) -> str:
        formatted_string = "```\n"
        entries = self.scores.items()
        entries = sorted(entries, key=itemgetter(1), reverse=True)
        for user, score in entries:
            score_entry = f"{score:3} | {user.display_name} \n"
            formatted_string += score_entry

        return formatted_string + "```"

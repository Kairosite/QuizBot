from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from discord.ext import commands
from collections import defaultdict
from operator import itemgetter
from responses import get_insult


class Scores(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.scores = defaultdict(lambda: 0)

    @commands.command(
        name="update",
        aliases=["upt", "u"]
    )
    @commands.guild_only()
    async def update_score(self, ctx, score: int):
        self.scores[ctx.author] += score
        await ctx.send(
            f"```\n {self.scores[ctx.author]:3}" +
            f" | {ctx.author.display_name} \n```"
        )
        return

    @update_score.error
    async def update_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                ctx.author.mention +
                " you have to actually give a score." +
                f"{get_insult().capitalize()}."
            )
        elif isinstance(error, commands.UserInputError):
            await ctx.send(
                ctx.author.mention +
                f" is a {get_insult()}, scores must be whole numbers."
            )
        return

    @commands.command(
        name="get",
        aliases=["g"]
    )
    @commands.guild_only()
    async def get_score(self, ctx):
        if self.scores:
            await ctx.send(self.pretty_format_scores())
        else:
            await ctx.send(
                ctx.author.mention +
                f", there are no scores yet, you {get_insult()}."
            )
        return

    @commands.command(
        name="reset",
        aliases=["r"]
    )
    @commands.guild_only()
    async def reset_score(self, ctx):
        if self.scores:
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

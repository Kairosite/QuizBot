from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from discord.ext import commands
from collections import defaultdict
from operator import itemgetter
from responses import get_insult
import discord


class Scores(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.scores = defaultdict(lambda: 0)

    @commands.command(
        name="update",
        aliases=["upt", "u"]
    )
    @commands.guild_only()
    async def update_score(self, ctx, score: int,
                           member: discord.Member = None):
        if member:
            if "games master" not in map(lambda x: x.name, ctx.author.roles):
                raise commands.MissingRole("games master")
            target = member
        else:
            target = ctx.author

        self.scores[target] += score
        await ctx.send(
            f"```\n {self.scores[target]:3}" +
            f" | {target.display_name} \n```"
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
        elif isinstance(error, commands.MissingRole):
            await ctx.send(
                ctx.author.mention +
                " you have no power here."
            )
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(
                ctx.author.mention +
                f" is a {get_insult()}, thats not a user."
            )
        elif isinstance(error, commands.BadArgument):
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
    @commands.has_role("games master")
    async def reset_score(self, ctx):
        if self.scores:
            await ctx.send(self.pretty_format_scores())
        self.scores.clear()
        return

    @reset_score.error
    async def reset_error(self, ctx, error):
        await ctx.send(
            ctx.author.mention +
            " you have no power here."
        )
        return

    def pretty_format_scores(self) -> str:
        formatted_string = "```\n"
        entries = self.scores.items()
        entries = sorted(entries, key=itemgetter(1), reverse=True)
        for user, score in entries:
            score_entry = f"{score:3} | {user.display_name} \n"
            formatted_string += score_entry

        return formatted_string + "```"

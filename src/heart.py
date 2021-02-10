from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from discord.ext import commands
from score import Scores

cogs = [Scores]


QuizBot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    case_insensitive=True
)


@QuizBot.command(name="Oi!")
async def marco_polo(ctx):
    await ctx.send("What?")


if __name__ == "__main__":
    for cog in cogs:
        QuizBot.add_cog(cog(QuizBot))

    with open("/__env__/bot.key") as key:
        token = key.read()

    QuizBot.run(token, bot=True, reconnect=True)

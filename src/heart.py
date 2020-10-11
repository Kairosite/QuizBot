from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from discord.ext import commands
from config import config
from score import Scores

QuizBot = commands.Bot(command_prefix=commands.when_mentioned_or("!"))


@QuizBot.command(name="Oi!")
async def marco_polo(ctx):
    await ctx.send("What?")

QuizBot.add_cog(Scores(QuizBot))

QuizBot.run(config.discord.token, bot=True, reconnect=True)

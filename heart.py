#!/usr/bin/env python

import discord
from config import config

client = discord.Client()
scores = dict()


def pretty_format_scores() -> str:
    pass


@client.event
async def on_ready():
    print('Online as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith("!update"):
        pass

    if message.content.lower() == "!get":
        await message.channel.send(
            pretty_format_scores()
        )
        return

    if message.content.lower() == "!reset":
        await message.channel.send(
            pretty_format_scores()
        )
        scores.clear()
        return


client.run(config.discord.token)

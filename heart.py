#!/usr/bin/env python

import discord
from collections import defaultdict
from config import config

client = discord.Client()
scores = defaultdict(lambda: 0)


def pretty_format_scores() -> str:
    formatted_string = "```\n"
    entries = scores.items()
    entries = sorted(entries, key=itemgetter(1), reverse=True)
    for user, score in entries:
        score_entry = f"{score:3} | {user.display_name} \n"
        formatted_string += score_entry

    return formatted_string + "```"


@client.event
async def on_ready():
    print('Online as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith("!update"):
        try:
            split_message = message.content.split()
            score = int(split_message[1])
        except ValueError:
            await message.channel.send(
                message.author.mention +
                " fucked up, scores must be whole numbers."
            )
        except IndexError:
            await message.channel.send(
                message.author.mention +
                ", you have to actually give a score. Muppet."
            )
        else:
            scores[message.author] += score

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

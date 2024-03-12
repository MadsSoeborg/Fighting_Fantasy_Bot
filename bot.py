import discord
import json
from discord.ext import commands

intents = discord.Intents.default()
intents.reactions = True
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load story from JSON file
with open("data/pages.json", "r") as file:
    story = json.load(file)

current_location = "start"


@bot.command(name="start_adventure")
async def start_adventure(ctx):
    global current_location
    current_location = "start"  # Reset to start
    await present_location(ctx)


async def present_location(ctx):
    location = story[current_location]
    message = await ctx.send(location["text"])
    for choice in location["choices"]:
        await message.add_reaction("🫡")


@bot.event
async def on_reaction_add(reaction, user):
    global current_location
    if user == bot.user or reaction.message.author != bot.user:
        return  # Ignore bot's own reactions and reactions to other messages
    choice_made = "left" if reaction.emoji == "🫡" else "right"
    if choice_made in story[current_location]["choices"]:
        current_location = story[current_location]["choices"][choice_made]
        await reaction.message.channel.send(story[current_location]["text"])
        # Check if further choices to present
        if story[current_location]["choices"]:
            await present_location(reaction.message.channel)


bot.run("MTIxNjc5MTU4NTMyMTM5MDE0MQ.Gj9kLY.scdWcdiFI-PM-yvAOGekVs6Zft9qndokc6PUhA")

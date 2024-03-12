import discord
import json
import asyncio
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
    await ctx.send("Welcome to the City of Thieves! To choose an option, type the number of the option you want to choose in the chat.")
    current_location = "1"  # Reset to start
    await present_location(ctx)


async def present_location(ctx):
    global current_location
    location = story[current_location]
    choices_text = '\n'.join([f"{num}. {option}" for num, option in enumerate(location["choices"].values(), start=1)])
    await ctx.send(f"{location['text']}\n\nChoose one of the following:\n{choices_text}")

    def check(m):
        return (
            m.author == ctx.author and
            m.channel == ctx.channel and
            m.content.isdigit() and
            1 <= int(m.content) <= len(location["choices"])
        )

    try:
        message = await bot.wait_for("message", check=check, timeout=300.0)
    except asyncio.TimeoutError:
        await ctx.send("You took too long to decide... Start over with !start_adventure")
        return
    else:
        choice_index = int(message.content) - 1
        # Fetch choice key based on index
        choice_key = list(location["choices"].keys())[choice_index]
        current_location = location["choices"][choice_key]
        await ctx.send(story[current_location]["text"])
        if story[current_location]["choices"]:
            await present_location(ctx)



bot.run("MTIxNjc5MTU4NTMyMTM5MDE0MQ.Gj9kLY.scdWcdiFI-PM-yvAOGekVs6Zft9qndokc6PUhA")

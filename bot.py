import discord
import json
import asyncio
import os
from models.character import Character
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

characters = {}


def load_characters():
    try:
        if os.path.exists("data/characters.json"):
            with open("data/characters.json", "r") as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    return {}
        else:
            return {}
    except IOError as e:
        print(f"An error occurred while loading characters: {e}")


def save_characters(characters):
    with open("data/characters.json", "w") as file:
        json.dump(characters, file, indent=4)


characters = load_characters()


@bot.command(name="create")
async def create_character(ctx):
    user_id = str(ctx.author.id)  # Convert to str for JSON keys
    if user_id in characters:
        await ctx.send("You already have a character.")
        return

    # Create a new character
    character = Character(name=ctx.author.display_name)
    # Convert to dict for JSON
    character_data = {
        "name": character.name,
        "skill": character.skill,
        "stamina": character.stamina,
        "luck": character.luck,
        "inventory": character.inventory,
    }
    characters[user_id] = character_data

    # Save the updated characters to a file
    save_characters(characters)

    # Notify the player of their new character's stats
    await ctx.send(f"Character created! Here are your stats:\n{str(character)}")


@bot.command(name="play")
async def start_adventure(ctx):
    user_id = str(ctx.author.id)  # Convert to str for JSON keys
    if user_id not in characters:
        await ctx.send("You do not have a character. Create one with !create")
        return

    global current_location
    await ctx.send(
        "Welcome to the City of Thieves! To choose an option, type the number of the option you want to choose in the chat."
    )

    current_location = "1"  # Starting point
    await present_location(ctx)


async def present_location(ctx):
    global current_location
    location = story[current_location]
    choices_text = "\n".join(
        [
            f"{num}. {option}"
            for num, option in enumerate(location["choices"].values(), start=1)
        ]
    )
    await ctx.send(f"{location['text']}\n\nChoose an option:\n{choices_text}")

    def check(m):
        return (
            m.author == ctx.author
            and m.channel == ctx.channel
            and m.content.isdigit()
            and 1 <= int(m.content) <= len(location["choices"])
        )

    try:
        message = await bot.wait_for("message", check=check, timeout=300.0)
    except asyncio.TimeoutError:
        await ctx.send(
            "You took too long to decide... Start over with !start_adventure"
        )
        return
    else:
        choice_index = int(message.content) - 1
        # Fetch choice key based on index
        choice_key = list(location["choices"].keys())[choice_index]
        current_location = location["choices"][choice_key]
        # await ctx.send(story[current_location]["text"])
        await present_location(ctx)


bot.run("MTIxNjc5MTU4NTMyMTM5MDE0MQ.Gj9kLY.scdWcdiFI-PM-yvAOGekVs6Zft9qndokc6PUhA")

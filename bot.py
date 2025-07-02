import discord
import os
import json
from discord.ext import commands
from dotenv import load_dotenv

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Global Data Loading ---
try:
    with open("data/pages.json", "r", encoding="utf-8") as f:
        bot.story_data = json.load(f)
    with open("data/enemies.json", "r", encoding="utf-8") as f:
        bot.enemy_data = json.load(f)
    print("Story and enemy data loaded successfully.")
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"FATAL: Error loading data files: {e}")
    exit()

# Dictionary to hold active game states
bot.active_games = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.load_extension("cogs.game")
    print("Game Cog loaded.")

# --- Main Execution ---
if __name__ == "__main__":
    load_dotenv()
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    if not discord_token:
        print("FATAL: DISCORD_BOT_TOKEN not found in .env file.")
        exit()
    bot.run(discord_token)
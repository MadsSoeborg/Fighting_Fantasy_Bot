import discord
import os
import json
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv 

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
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
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    print(f"--- Attempting to load .env from explicit path: {dotenv_path} ---")
    # Have to override otherwise it will load the wrong token
    load_dotenv(dotenv_path=dotenv_path, override=True) 
    discord_token = os.getenv("DISCORD_BOT_TOKEN")

    if not discord_token:
        print("FATAL: Token could not be loaded even with explicit path. Check file permissions.")
        exit()
        
    bot.run(discord_token)
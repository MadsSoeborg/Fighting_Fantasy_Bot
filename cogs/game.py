import discord
import json
import asyncio
import os
from discord.ext import commands
from models.character import Character
from .game_state import GameState

class GameCog(commands.Cog, name="Fighting Fantasy"):
    def __init__(self, bot):
        self.bot = bot

    # --- Helper Functions for Data Persistence ---
    def _load_all_chars(self):
        if not os.path.exists("data/characters.json"): return {}
        with open("data/characters.json", "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}

    def _save_all_chars(self, chars_dict):
        with open("data/characters.json", "w", encoding="utf-8") as f:
            json.dump(chars_dict, f, indent=4)

    def load_character(self, user_id):
        user_id = str(user_id)
        all_chars = self._load_all_chars()
        if user_id in all_chars:
            return Character.from_dict(all_chars[user_id])
        return None

    def save_character(self, character):
        all_chars = self._load_all_chars()
        all_chars[str(character.user_id)] = character.to_dict()
        self._save_all_chars(all_chars)

    # --- Character Management Commands ---
    @commands.command(name="create")
    async def create_character(self, ctx):
        """Creates a new character for your adventure."""
        if self.load_character(ctx.author.id):
            await ctx.send("You already have a character. Use `!delete` to start over.")
            return
        character = Character(name=ctx.author.display_name, user_id=ctx.author.id)
        self.save_character(character)
        await ctx.send(f"Character created! Welcome, adventurer **{character.name}**!")
        await ctx.send(embed=self.create_char_embed(character))

    @commands.command(name="stats")
    async def show_stats(self, ctx):
        """Displays your character sheet."""
        character = self.load_character(ctx.author.id)
        if not character:
            await ctx.send("No character found. Use `!create` to make one.")
            return
        await ctx.send(embed=self.create_char_embed(character))

    def create_char_embed(self, character: Character):
        """Creates a nice embed for the character sheet."""
        embed = discord.Embed(title=f"{character.name}'s Adventure Sheet", color=discord.Color.dark_gold())
        embed.add_field(name="Stats", value=f"**SKILL**: {character.skill}/{character.max_skill}\n**STAMINA**: {character.stamina}/{character.max_stamina}\n**LUCK**: {character.luck}/{character.max_luck}", inline=True)
        embed.add_field(name="Resources", value=f"**Gold**: {character.gold}\n**Provisions**: {character.provisions}", inline=True)
        inventory_str = ', '.join(character.inventory) if character.inventory else "Empty"
        embed.add_field(name="Inventory", value=inventory_str, inline=False)
        embed.set_footer(text=f"Current Location: Page {character.current_location}")
        return embed

    @commands.command(name="delete")
    async def delete_character(self, ctx):
        """Deletes your current character. This is permanent!"""
        user_id = str(ctx.author.id)
        if user_id in self.bot.active_games:
            await ctx.send("You can't delete your character while playing. Use `!quit` first.")
            return

        all_chars = self._load_all_chars()
        if user_id in all_chars:
            del all_chars[user_id]
            self._save_all_chars(all_chars)
            await ctx.send("Your character has been permanently deleted.")
        else:
            await ctx.send("You don't have a character to delete.")

    # --- Game Loop and Handlers ---
    @commands.command(name="play")
    async def play_game(self, ctx):
        """Starts or resumes your adventure in the City of Thieves."""
        user_id = str(ctx.author.id)
        if user_id in self.bot.active_games:
            await ctx.send("You are already playing!")
            return

        character = self.load_character(user_id)
        if not character:
            await ctx.send("You need a character. Use `!create` to make one.")
            return

        game = GameState(character)
        self.bot.active_games[user_id] = game
        await ctx.send(f"Welcome back to the City of Thieves, **{character.name}**! Resuming your adventure...")

        while user_id in self.bot.active_games:
            page_id = game.character.current_location
            page_data = self.bot.story_data.get(page_id)

            if not page_data:
                await ctx.send(f"Error: Story page `{page_id}` not found. Ending game.")
                del self.bot.active_games[user_id]
                break
            
            # The Great Dispatcher
            page_type = page_data.get("type", "choice")
            handler = getattr(self, f"handle_{page_type}", self.handle_unknown)
            await handler(ctx, game, page_data)

            # Check for death after every action
            if game.character.is_dead():
                await ctx.send(f"Your STAMINA has fallen to 0! You have died.")
                await self.handle_game_over(ctx, game, {"text": "Your adventure has come to a tragic end."})
            
            # Save progress unless the game ended
            if user_id in self.bot.active_games:
                self.save_character(game.character)
            await asyncio.sleep(1)  # Short pause to let user read

    async def handle_choice(self, ctx, game, page_data):
        """Handles a standard choice page."""
        choices = page_data["choices"]
        options_text = "\n".join([f"**{i}**. {text}" for i, text in enumerate(choices.keys(), 1)])
        prompt = f"```\nPage {game.character.current_location}\n```\n{page_data['text']}\n\n{options_text}"
        
        await ctx.send(prompt)

        def check(m):
            return m.author.id == int(game.character.user_id) and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= len(choices)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=300.0)
            choice_index = int(msg.content) - 1
            game.character.current_location = list(choices.values())[choice_index]
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Your adventure is paused. Use `!play` to resume.")
            del self.bot.active_games[game.character.user_id]

    async def handle_effect(self, ctx, game, page_data):
        """Handles applying stat/item changes and moving on."""
        await ctx.send(f"```\nPage {game.character.current_location}\n```\n{page_data['text']}")
        effect_summary = game.character.apply_effects(page_data["effects"])
        await ctx.send(f"**Effect**: {effect_summary}")
        game.character.current_location = page_data["next"]
        await asyncio.sleep(2) # Pause to let user read

    async def handle_luck_test(self, ctx, game, page_data):
        """Handles a Test Your Luck page."""
        await ctx.send(f"```\nPage {game.character.current_location}\n```\n{page_data['text']}")
        await ctx.send(f"You must **Test Your Luck**! (Current LUCK: {game.character.luck})")
        
        is_lucky = game.character.test_luck()
        await asyncio.sleep(1)

        if is_lucky:
            await ctx.send(f"You are **LUCKY**! (LUCK is now {game.character.luck})")
            game.character.current_location = page_data["outcomes"]["lucky"]
        else:
            await ctx.send(f"You are **UNLUCKY**! (LUCK is now {game.character.luck})")
            game.character.current_location = page_data["outcomes"]["unlucky"]
        await asyncio.sleep(2)
        
    async def handle_skill_test(self, ctx, game, page_data):
        """Handles a Test Your Skill page."""
        await ctx.send(f"```\nPage {game.character.current_location}\n```\n{page_data['text']}")
        await ctx.send(f"You must **Test Your Skill**! (Current SKILL: {game.character.skill})")

        is_successful = game.character.test_skill()
        await asyncio.sleep(1)

        if is_successful:
            await ctx.send("**Success!**")
            game.character.current_location = page_data["outcomes"]["success"]
        else:
            await ctx.send("**Failure!**")
            game.character.current_location = page_data["outcomes"]["failure"]
        await asyncio.sleep(2)

    async def handle_condition_item(self, ctx, game, page_data):
        """Checks if the character has an item and routes them."""
        # This page type is silent, it just routes the player
        if game.character.has_item(page_data["check"]["item"]):
            game.character.current_location = page_data["outcomes"]["success"]
        else:
            game.character.current_location = page_data["outcomes"]["failure"]

    async def handle_combat(self, ctx, game, page_data):
        """Handles a combat encounter."""
        await ctx.send(f"```\nPage {game.character.current_location}\n```\n{page_data['text']}")
        await ctx.send("⚔️ **COMBAT BEGINS!** ⚔️")
        
        enemies = [self.bot.enemy_data[eid].copy() for eid in page_data["enemies"]]
        game.combat_rounds = 0

        for enemy in enemies:
            if game.character.is_dead(): break
            await ctx.send(f"You now face **{enemy['name']}** (SKILL: {enemy['skill']}, STAMINA: {enemy['stamina']})!")
            
            # Single enemy combat loop
            while not game.character.is_dead() and enemy['stamina'] > 0:
                game.combat_rounds += 1
                player_attack = game.character.roll_dice(2) + game.character.skill
                enemy_attack = game.character.roll_dice(2) + enemy['skill']
                
                await asyncio.sleep(1.5)
                summary = f"**Round {game.combat_rounds}**: Your Attack Strength (`{player_attack}`) vs. {enemy['name']}'s (`{enemy_attack}`)"
                
                if player_attack > enemy_attack:
                    enemy['stamina'] -= 2
                    await ctx.send(f"{summary}\n> You hit the {enemy['name']}! (Enemy STAMINA: {enemy['stamina']})")
                elif enemy_attack > player_attack:
                    game.character.take_damage(2)
                    await ctx.send(f"{summary}\n> The {enemy['name']} hits you! (Your STAMINA: {game.character.stamina})")
                else:
                    await ctx.send(f"{summary}\n> A draw! Your weapons clang together.")
            
            if not game.character.is_dead():
                 await ctx.send(f"You have defeated the {enemy['name']}!")

        # After all combat is resolved
        if game.character.is_dead():
            game.character.current_location = page_data["outcomes"]["lose"]
        else:
            # Handle complex outcomes like round limits
            if "max_rounds" in page_data.get("rules", {}):
                if game.combat_rounds <= page_data["rules"]["max_rounds"]:
                    game.character.current_location = page_data["outcomes"]["win_fast"]
                else:
                    game.character.current_location = page_data["outcomes"]["win_slow"]
            else: # Standard win
                game.character.current_location = page_data["outcomes"]["win"]
    
    async def handle_auto(self, ctx, game, page_data):
        """Handles a page that just displays text and moves on."""
        await ctx.send(f"```\nPage {game.character.current_location}\n```\n{page_data['text']}")
        game.character.current_location = page_data["next"]
        await asyncio.sleep(3) # Give user time to read

    async def handle_game_over(self, ctx, game, page_data):
        await ctx.send(f"```{game.character.current_location}```\n{page_data['text']}")
        await ctx.send("💀 **GAME OVER** 💀\nYour character has met a grisly end. Use `!delete` and `!create` to start a new adventure.")
        if game.character.user_id in self.bot.active_games:
            del self.bot.active_games[game.character.user_id]
            
    async def handle_victory(self, ctx, game, page_data):
        await ctx.send(f"```{game.character.current_location}```\n{page_data['text']}")
        await ctx.send("🏆 **CONGRATULATIONS!** 🏆\nYou have completed your quest!")
        if game.character.user_id in self.bot.active_games:
            del self.bot.active_games[game.character.user_id]

    async def handle_unknown(self, ctx, game, page_data):
        page_type = page_data.get("type", "choice")
        await ctx.send(f"Error: Handler for page type `{page_type}` not implemented. Ending game.")
        if game.character.user_id in self.bot.active_games:
            del self.bot.active_games[game.character.user_id]

    async def handle_transaction(self, ctx, game, page_data):
        """Handles a page with choices that may cost gold"""
        choices = page_data["choices"]
        options_text_list = []
        for i, (text, data) in enumerate(choices.items(), 1):
            cost = data.get("cost", 0)
            if cost > 0:
                options_text_list.append(f"**{i}**. {text} (Cost: {cost} Gold)")
            else:
                options_text_list.append(f"**{i}**. {text}")
        
        options_text = "\n".join(options_text_list)
        prompt = f"```\nPage {game.character.current_location}\n```\n{page_data['text']}\n\n{options_text}"

        await ctx.send(prompt)

        def check(m):
            return m.author.id == int(game.character.user_id) and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= len(choices)
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=300.0)
            choice_index = int(msg.content) - 1

            # Get the selected choice and its data
            chosen_option_data = list(choices.values())[choice_index]
            cost = chosen_option_data.get("cost", 0)

            # Check if the character can afford the cost
            if game.character.gold < cost:
                await ctx.send(f"You don't have enough gold for that! You need {cost} Gold, but you only have {game.character.gold}.")
                # Loop back to the same page
                return
            if cost > 0:
                game.character.gold -= cost
                await ctx.send(f"You pay {cost} Gold. (Remaining: {game.character.gold} Gold)")
            
            if "effect" in chosen_option_data:
                effect_summary = game.character.apply_effects(chosen_option_data["effect"])
                await ctx.send(f"**Effect**: {effect_summary}")
            
            game.character.current_location = chosen_option_data["next"]
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Your adventure is paused. Use `!play` to resume.")
            del self.bot.active_games[game.character.user_id]

    @commands.command(name="quit")
    async def quit_game(self, ctx):
        """Quits the current game, saving your progress."""
        user_id = str(ctx.author.id)
        if user_id in self.bot.active_games:
            del self.bot.active_games[user_id]
            await ctx.send("You have quit the game. Your progress is saved. Use `!play` to return!")
        else:
            await ctx.send("You are not currently in a game.")


    @commands.command(name="info", aliases=["help"])
    async def show_info(self, ctx):
        """Displays a help message with instructions on how to play."""
        
        embed = discord.Embed(
            title="⚔️ How to Play Fighting Fantasy Bot ⚔️",
            description="Welcome, adventurer! Here's how to navigate the world and complete your quest.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="1. Create Your Character",
            value="Every great adventure starts with a hero. Use `!create` to roll your character's stats. You can only have one character at a time.",
            inline=False
        )
        
        embed.add_field(
            name="2. Start Your Adventure",
            value="Use `!play` to begin your journey or to resume from where you last stopped. Your progress is saved automatically!",
            inline=False
        )

        embed.add_field(
            name="3. Making Choices",
            value="When the story presents you with a numbered list of options, simply type the number of your choice in the chat (e.g., `1`, `2`, etc.) and press Enter.",
            inline=False
        )

        embed.add_field(
            name="4. Automatic Actions",
            value="Combat, `Test Your Luck`, and `Test Your Skill` checks are all handled automatically by the bot. Just sit back and watch the events unfold!",
            inline=False
        )

        embed.add_field(
            name="Essential Commands",
            value=(
                "`!create` - Creates your adventurer.\n"
                "`!play` - Starts or resumes the game.\n"
                "`!stats` - Shows your current character sheet (stats, inventory, etc.).\n"
                "`!quit` - Safely exits the game, saving your progress.\n"
                "`!delete` - **Permanently** deletes your character to start over.\n"
                "`!info` or `!help` - Shows this help message."
            ),
            inline=False
        )

        embed.set_footer(text="Good luck in the City of Thieves!")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GameCog(bot))
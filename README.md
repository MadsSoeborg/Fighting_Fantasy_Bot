# Fighting Fantasy Discord Bot

This is a Discord bot designed to let users play through the classic Fighting Fantasy gamebooks by Steve Jackson and Ian Livingstone. The bot manages character creation, stats, inventory, and story progression, bringing the single-player role-playing experience to a Discord server.

This implementation is based on **Book 5: City of Thieves**.

## Features

- **Interactive Story:** Play through the complete "City of Thieves" adventure by making choices.
- **Character Management:** Create and manage your own unique adventurer with classic FF stats (SKILL, STAMINA, LUCK).
- **Persistent State:** Your character's stats, inventory, and progress are automatically saved, so you can `!quit` and resume your adventure later with `!play`.
- **Automated Mechanics:** The bot handles all dice rolls for combat, skill tests, and luck tests, letting you focus on the story.
- **Data-Driven:** The entire adventure is powered by structured JSON files, making it easy to modify, fix, or even adapt for other Fighting Fantasy books.

## How to Play

Interacting with the bot is simple. Once it's in your server, use the following commands in any channel the bot can see.

### Essential Commands

- `!create`

  - Creates your adventurer with randomly rolled stats. This is the first step for any new player. You can only have one character at a time.

- `!play`

  - Starts your adventure or resumes from where you last stopped. The bot will present you with the current story page and your choices.

- `!stats`

  - Displays your current character sheet, including your SKILL, STAMINA, LUCK, Gold, Provisions, and Inventory.

- `!info` or `!help`

  - Shows a detailed help message explaining all the commands and how to interact with the game.

- `!quit`

  - Safely ends your current game session. Your progress is saved, and you can use `!play` to come back at any time.

- `!delete`
  - **Permanently deletes** your current character. Use this if you want to start a completely new game with a new character roll. This action cannot be undone.

### Making Choices

When the bot presents you with a story segment and a numbered list of choices, simply **type the number of your desired choice** into the chat and press Enter.

> **Example:**
>
> **Bot:**
>
> ```
> Page 1
> ```
>
> At the gate you are confronted by a tall guard... 'State the nature of your business...'
>
> **1**. Tell him you wish to be taken to Nicodemus.
> **2**. Tell him you wish to sell some stolen booty.
> **3**. Attack him quickly with your sword.
>
> **You type:** > `2`

The bot will then process your choice and present the next part of the story.

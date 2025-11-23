# Fighting Fantasy: City of Thieves (CLI Edition)

A text-based RPG engine that brings the classic *Fighting Fantasy* gamebook experience to your terminal. This project digitizes Steve Jackson and Ian Livingstone's **Book 5: City of Thieves**, managing all the dice rolling, inventory tracking, and combat mechanics so you can focus on surviving Port Blacksand.

## Features

*   **Interactive Fiction:** Play through the complete text adventure. Your choices determine whether you survive or perish.
*   **Automated Rules:** The engine handles all 2d6 dice rolls for Combat, *Test Your Luck*, and Skill checks instantly.
*   **RPG Mechanics:** Automatically tracks your **SKILL**, **STAMINA**, **LUCK**, Gold, and Inventory.
*   **Save System:** Your progress is auto-saved after every page. You can quit at any time and resume exactly where you left off.
*   **Retro Visuals:** Features colored text output and ASCII art headers.
*   **Data-Driven:** The entire story is powered by JSON files, making it easy to mod or fix.

## Installation & Setup

You need **Python 3** installed on your computer.

1.  **Clone or Download** this repository.
2.  Open your terminal (Command Prompt, PowerShell, or Terminal).
3.  Navigate to the game folder:
    ```bash
    cd madssoeborg-fighting_fantasy_bot
    ```
4.  Install the required libraries (Colorama for colors, Pyfiglet for ASCII art):
    ```bash
    pip install -r requirements.txt
    ```
5.  **Run the Game:**
    ```bash
    python main.py
    ```

## How to Play

Once the game is running, you will see the Main Menu.

### Main Menu
*   **1. New Game:** Create a fresh character. (Warning: Overwrites existing save).
*   **2. Continue:** Resume your adventure from the last page visited.
*   **3. View Stats:** Check your character sheet.
*   **4. Delete:** Wipe your save file.

### In-Game Controls
When reading the story, you interact by typing commands into the terminal prompt `>`.

*   **Make a Choice:** Type the **Number** of the option you want to take (e.g., `1`, `2`).
*   **`s`** - **Show Stats:** Displays your current Health, Gold, Items, and Skills.
*   **`e`** - **Eat Provision:** Consumes 1 Provision to heal 4 STAMINA points (cannot exceed initial Stamina).
*   **`q`** - **Quit:** Saves and returns to the main menu/exits.

### Combat & Events
*   **Combat:** Press `Enter` to advance rounds. The game handles attack rolls automatically.
*   **Luck:** During combat or story events, you may be asked to *Test Your Luck*. Type `y` to burn a Luck point for a chance at a better outcome (e.g., dealing double damage).

## Cheat Code
Struggling to survive?
*   When creating a new character, name yourself `Ian Livingstone` to activate **God Mode** (Max stats + 50 Gold).

## Credits
*   Based on the gamebook *City of Thieves* by Ian Livingstone.

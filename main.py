import json
import os
import sys
from engine.game import GameEngine
from engine.utils import clear_screen, print_header, print_error

def load_data():
    try:
        base_path = os.path.dirname(__file__)
        
        with open(os.path.join(base_path, "data/pages.json"), "r", encoding="utf-8") as f:
            story = json.load(f)
        with open(os.path.join(base_path, "data/enemies.json"), "r", encoding="utf-8") as f:
            enemies = json.load(f)
        return story, enemies
    except FileNotFoundError as e:
        print_error(f"FATAL: Could not load data files. {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print_error(f"FATAL: JSON format error. {e}")
        sys.exit(1)

def main_menu():
    story_data, enemy_data = load_data()
    engine = GameEngine(story_data, enemy_data)

    while True:
        clear_screen()
        print_header("FIGHTING FANTASY: CITY OF THIEVES")
        print("1. New Game / Create Character")
        print("2. Continue Adventure")
        print("3. View Character Stats")
        print("4. Delete Character")
        print("5. Quit")
        
        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            clear_screen()
            if engine.create_character_flow():
                engine.play()
        elif choice == "2":
            engine.play()
        elif choice == "3":
            clear_screen()
            engine.show_stats()
        elif choice == "4":
            confirm = input("Are you sure you want to delete your character? (y/n): ")
            if confirm.lower() == 'y':
                if engine.delete_character():
                    print("Character deleted.")
                else:
                    print("No character to delete.")
                input("Press Enter...")
        elif choice == "5":
            print("Goodbye!")
            sys.exit()
        else:
            pass

if __name__ == "__main__":
    os.system('') 
    main_menu()
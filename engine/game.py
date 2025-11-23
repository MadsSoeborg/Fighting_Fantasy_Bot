import json
import time
import os
from models.character import Character
from engine.utils import clear_screen, print_header, print_bold, print_error, print_success, print_warning

class GameEngine:
    def __init__(self, story_data, enemy_data):
        self.story_data = story_data
        self.enemy_data = enemy_data
        self.character = None
        self.user_id = "local_player" # Single player, fixed ID
        self.running = False

    # --- Persistence ---
    def _load_all_chars(self):
        if not os.path.exists("data/characters.json"): return {}
        with open("data/characters.json", "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}

    def _save_all_chars(self, chars_dict):
        with open("data/characters.json", "w", encoding="utf-8") as f:
            json.dump(chars_dict, f, indent=4)

    def load_character(self):
        all_chars = self._load_all_chars()
        if self.user_id in all_chars:
            return Character.from_dict(all_chars[self.user_id])
        return None

    def save_character(self):
        if not self.character: return
        all_chars = self._load_all_chars()
        all_chars[self.user_id] = self.character.to_dict()
        self._save_all_chars(all_chars)

    def delete_character(self):
        all_chars = self._load_all_chars()
        if self.user_id in all_chars:
            del all_chars[self.user_id]
            self._save_all_chars(all_chars)
            return True
        return False

    # --- Core Game Logic ---
    def create_character_flow(self):
        print_header("Character Creation")
        if self.load_character():
            print_warning("You already have a character. Delete it first to start over.")
            return

        name = input("Enter your adventurer's name: ").strip()
        if not name: name = "Adventurer"
        
        self.character = Character(name=name, user_id=self.user_id)
        self.save_character()
        print_success(f"Welcome, {self.character.name}!")
        print(self.character)
        input("\nPress Enter to continue...")

    def show_stats(self):
        char = self.load_character()
        if char:
            print("\n" + str(char) + "\n")
        else:
            print_error("No character found.")
        input("Press Enter to continue...")

    def play(self):
        self.character = self.load_character()
        if not self.character:
            print_error("No character found. Create one first!")
            input("Press Enter...")
            return

        self.running = True
        print_header(f"City of Thieves - {self.character.name}")
        time.sleep(1)

        while self.running:
            clear_screen()
            page_id = self.character.current_location
            page_data = self.story_data.get(page_id)

            if not page_data:
                print_error(f"Error: Page {page_id} not found.")
                self.running = False
                break

            # Dispatcher
            page_type = page_data.get("type", "choice")
            handler_name = f"handle_{page_type}"
            
            if hasattr(self, handler_name):
                getattr(self, handler_name)(page_data)
            else:
                self.handle_unknown(page_data)

            # Check Death
            if self.character.is_dead():
                print_error("\nYour STAMINA has reached 0.")
                self.handle_game_over({"text": "You have died."})
            
            # Save unless game over
            if self.running:
                self.save_character()

    # --- Page Handlers ---

    def display_page_text(self, page_data):
        print_header(f"Page {self.character.current_location}")
        print(f"\n{page_data['text']}\n")

    def handle_choice(self, page_data):
        self.display_page_text(page_data)
        choices = page_data["choices"]
        
        # Display options
        options = list(choices.keys())
        for i, text in enumerate(options, 1):
            print(f"{i}. {text}")

        # Input Loop
        while True:
            try:
                choice_input = input(f"\nMake your choice (1-{len(options)}) or 'q' to quit: ").lower()
                if choice_input == 'q':
                    self.running = False
                    return
                
                idx = int(choice_input) - 1
                if 0 <= idx < len(options):
                    selected_text = options[idx]
                    self.character.current_location = choices[selected_text]
                    return
                else:
                    print_error("Invalid number.")
            except ValueError:
                print_error("Please enter a number.")

    def handle_transaction(self, page_data):
        self.display_page_text(page_data)
        choices = page_data["choices"]
        options = list(choices.items()) # List of tuples (text, data)

        for i, (text, data) in enumerate(options, 1):
            cost = data.get("cost", 0)
            cost_str = f" (Cost: {cost} Gold)" if cost > 0 else ""
            print(f"{i}. {text}{cost_str}")

        while True:
            try:
                choice_input = input(f"\nSelect option (1-{len(options)}) or 'q' to quit: ").lower()
                if choice_input == 'q':
                    self.running = False
                    return

                idx = int(choice_input) - 1
                if 0 <= idx < len(options):
                    _, choice_data = options[idx]
                    cost = choice_data.get("cost", 0)

                    if self.character.gold < cost:
                        print_warning(f"Not enough gold! You have {self.character.gold}, need {cost}.")
                        continue
                    
                    if cost > 0:
                        self.character.gold -= cost
                        print(f"Paid {cost} Gold.")

                    if "effect" in choice_data:
                        summary = self.character.apply_effects(choice_data["effect"])
                        print_success(f"Effect: {summary}")
                        time.sleep(1.5)

                    self.character.current_location = choice_data["next"]
                    return
                else:
                    print_error("Invalid number.")
            except ValueError:
                print_error("Please enter a number.")

    def handle_effect(self, page_data):
        self.display_page_text(page_data)
        summary = self.character.apply_effects(page_data["effects"])
        print_success(f"Effect: {summary}")
        self.character.current_location = page_data["next"]
        input("\nPress Enter to continue...")

    def handle_luck_test(self, page_data):
        self.display_page_text(page_data)
        print_bold(f"Testing Luck... (Current: {self.character.luck})")
        input("Press Enter to roll dice...")
        
        is_lucky = self.character.test_luck()
        time.sleep(0.5)
        
        if is_lucky:
            print_success("You are LUCKY!")
            self.character.current_location = page_data["outcomes"]["lucky"]
        else:
            print_error("You are UNLUCKY!")
            self.character.current_location = page_data["outcomes"]["unlucky"]
        
        time.sleep(1.5)

    def handle_skill_test(self, page_data):
        self.display_page_text(page_data)
        print_bold(f"Testing Skill... (Current: {self.character.skill})")
        input("Press Enter to roll dice...")

        is_success = self.character.test_skill()
        time.sleep(0.5)

        if is_success:
            print_success("Success!")
            self.character.current_location = page_data["outcomes"]["success"]
        else:
            print_error("Failure!")
            self.character.current_location = page_data["outcomes"]["failure"]
        time.sleep(1.5)

    def handle_condition_item(self, page_data):
        # Hidden check
        if self.character.has_item(page_data["check"]["item"]):
            self.character.current_location = page_data["outcomes"]["success"]
        else:
            self.character.current_location = page_data["outcomes"]["failure"]

    def handle_combat(self, page_data):
        self.display_page_text(page_data)
        print_warning("⚔️  COMBAT BEGINS! ⚔️")
        
        enemies = [self.enemy_data[eid].copy() for eid in page_data["enemies"]]
        combat_rounds = 0

        for enemy in enemies:
            if self.character.is_dead(): break
            print_bold(f"\nEnemy: {enemy['name']} (SKILL: {enemy['skill']}, STAMINA: {enemy['stamina']})")
            input("Press Enter to fight...")

            while not self.character.is_dead() and enemy['stamina'] > 0:
                combat_rounds += 1
                print(f"\n--- Round {combat_rounds} ---")
                
                player_roll = self.character.roll_dice(2)
                player_attack = player_roll + self.character.skill
                
                enemy_roll = self.character.roll_dice(2)
                enemy_attack = enemy_roll + enemy['skill']

                time.sleep(0.5)
                print(f"You rolled {player_roll} (+{self.character.skill} Skill) = {player_attack}")
                print(f"{enemy['name']} rolled {enemy_roll} (+{enemy['skill']} Skill) = {enemy_attack}")
                time.sleep(0.5)

                if player_attack > enemy_attack:
                    enemy['stamina'] -= 2
                    print_success(f"You hit! {enemy['name']} Stamina: {enemy['stamina']}")
                elif enemy_attack > player_attack:
                    self.character.take_damage(2)
                    print_error(f"You were hit! Your Stamina: {self.character.stamina}")
                else:
                    print("Draw!")
                
                if not self.character.is_dead() and enemy['stamina'] > 0:
                    time.sleep(0.8) # Pause between rounds

            if not self.character.is_dead():
                print_success(f"You defeated {enemy['name']}!")
                time.sleep(1)

        # Outcome
        if self.character.is_dead():
            self.character.current_location = page_data["outcomes"]["lose"]
        else:
            rules = page_data.get("rules", {})
            if "max_rounds" in rules:
                if combat_rounds <= rules["max_rounds"]:
                    self.character.current_location = page_data["outcomes"]["win_fast"]
                else:
                    self.character.current_location = page_data["outcomes"]["win_slow"]
            else:
                self.character.current_location = page_data["outcomes"]["win"]
        
        input("\nPress Enter to continue...")

    def handle_auto(self, page_data):
        self.display_page_text(page_data)
        self.character.current_location = page_data["next"]
        input("Press Enter to continue...")

    def handle_game_over(self, page_data):
        clear_screen()
        print_error("\n" + page_data.get('text', ''))
        print_header("💀 GAME OVER 💀")
        self.delete_character()
        self.running = False
        input("Press Enter to return to main menu...")

    def handle_victory(self, page_data):
        clear_screen()
        print_success("\n" + page_data.get('text', ''))
        print_header("🏆 CONGRATULATIONS 🏆")
        print("You have completed the adventure!")
        self.delete_character()
        self.running = False
        input("Press Enter...")

    def handle_unknown(self, page_data):
        print_error(f"Unknown page type: {page_data.get('type')}")
        self.running = False
import json
import time
import os
import random

from colorama import Fore, Style
from models.character import Character
from engine.utils import (
    clear_screen, print_header, print_bold, print_error, 
    print_success, print_warning, print_wrapped, print_info
)

class GameEngine:
    def __init__(self, story_data, enemy_data):
        self.story_data = story_data
        self.enemy_data = enemy_data
        self.character = None
        self.user_id = "local_player"
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
        clear_screen()
        print_header("NEW ADVENTURE")
        
        if self.load_character():
            print_warning("A character already exists!")
            confirm = input("Overwrite this save? (y/n): ").lower()
            if confirm != 'y':
                return False

        name = input("\nEnter your adventurer's name: ").strip()
        if not name: name = "Adventurer"
        
        self.character = Character(name=name, user_id=self.user_id)
        
        # CHEAT MODE / GOD MODE
        if name.lower() == "ian livingstone":
            print_success("GOD MODE ACTIVATED")
            self.character.skill = 12
            self.character.stamina = 24
            self.character.luck = 12
            self.character.max_skill = 12
            self.character.max_stamina = 24
            self.character.max_luck = 12
            self.character.gold = 50

        self.save_character()
        
        print_success(f"\nCharacter Created! Welcome, {self.character.name}.")
        print(self.character)
        input("\nPress Enter to begin your adventure...")
        return True

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
        
        while self.running:
            clear_screen()
            page_id = self.character.current_location
            page_data = self.story_data.get(page_id)

            if not page_data:
                print_error(f"FATAL ERROR: Page {page_id} not found in story data.")
                self.running = False
                break

            # --- Dispatcher ---
            page_type = page_data.get("type", "choice")
            handler_name = f"handle_{page_type}"
            
            if hasattr(self, handler_name):
                getattr(self, handler_name)(page_data)
            else:
                self.handle_unknown(page_data)

            # --- Post-Action Checks ---
            if self.character.is_dead():
                print_error("\nYour STAMINA has reached 0.")
                self.handle_game_over({"text": "You have died."})
            
            if self.running:
                self.save_character()

    # --- UI Helpers ---
    def display_page_text(self, page_data):
        print_header(f"Page {self.character.current_location}")
        if "text" in page_data and page_data["text"]:
            print_wrapped(page_data['text'])
            print("-" * 60)

    def get_input_cmd(self):
        print(f"\n{Fore.LIGHTBLACK_EX}[Commands: # to choose, 's' for stats, 'e' to eat provision, 'q' to quit]{Style.RESET_ALL}")
        return input("> ").strip().lower()

    # --- Specific Handlers ---

    def handle_choice(self, page_data):
        self.display_page_text(page_data)
        choices = page_data["choices"]
        options = list(choices.keys())
        
        for i, text in enumerate(options, 1):
            print(f"{i}. {text}")

        while True:
            cmd = self.get_input_cmd()
            if cmd == 'q': self.running = False; return
            if cmd == 's': print(self.character); continue
            if cmd == 'e': print_bold(self.character.eat_provision()); continue

            try:
                idx = int(cmd) - 1
                if 0 <= idx < len(options):
                    self.character.current_location = choices[options[idx]]
                    return
            except ValueError:
                pass
            print_error("Invalid choice.")

    def handle_auto(self, page_data):
        self.display_page_text(page_data)
        input(f"\n{Fore.GREEN}Press Enter to continue...{Style.RESET_ALL}")
        self.character.current_location = page_data["next"]

    def handle_transaction(self, page_data):
        """Simple buying decisions (one time choice)."""
        self.display_page_text(page_data)
        choices = page_data["choices"]
        options = list(choices.items())

        for i, (text, data) in enumerate(options, 1):
            cost = data.get("cost", 0)
            cost_str = f"{Fore.YELLOW}({cost} Gold){Style.RESET_ALL}" if cost > 0 else ""
            print(f"{i}. {text} {cost_str}")

        while True:
            cmd = self.get_input_cmd()
            if cmd == 'q': self.running = False; return
            if cmd == 's': print(self.character); continue

            try:
                idx = int(cmd) - 1
                if 0 <= idx < len(options):
                    _, data = options[idx]
                    cost = data.get("cost", 0)
                    
                    if self.character.gold < cost:
                        print_warning(f"Not enough gold! You have {self.character.gold}.")
                        continue
                    
                    if cost > 0:
                        self.character.gold -= cost
                        print_info(f"You pay {cost} Gold.")

                    if "effect" in data:
                        summary = self.character.apply_effects(data["effect"])
                        print_success(f"Gained: {summary}")
                        time.sleep(1)

                    self.character.current_location = data["next"]
                    return
            except ValueError:
                pass

    def handle_shop(self, page_data):
        """Buying single items from a list."""
        self.handle_shop_multi(page_data) # Re-use logic

    def handle_shop_multi(self, page_data):
        """Buying multiple items from a list."""
        self.display_page_text(page_data)
        items = page_data["items"] # Dict of "Item Name": Cost
        
        while True:
            print_bold(f"\nYour Gold: {self.character.gold}")
            item_list = list(items.items())
            
            for i, (name, cost) in enumerate(item_list, 1):
                print(f"{i}. {name} - {Fore.YELLOW}{cost} Gold{Style.RESET_ALL}")
            print(f"{len(item_list)+1}. Leave Shop")

            try:
                choice = input("\nBuy which item? > ").strip()
                if choice == str(len(item_list) + 1):
                    break # Leave
                
                idx = int(choice) - 1
                if 0 <= idx < len(item_list):
                    name, cost = item_list[idx]
                    if self.character.gold >= cost:
                        self.character.gold -= cost
                        self.character.add_item(name)
                        print_success(f"Bought {name}!")
                    else:
                        print_warning("Not enough gold!")
                else:
                    print_error("Invalid number.")
            except ValueError:
                print_error("Invalid input.")

        if "next" in page_data:
            self.character.current_location = page_data["next"]

    def handle_pawn_shop(self, page_data):
        """Selling items."""
        self.display_page_text(page_data)
        sellable_items = page_data["items"] # Dict "Item": Value

        while True:
            print_bold(f"\nYour Inventory: {', '.join(self.character.inventory)}")
            print_bold(f"Your Gold: {self.character.gold}")
            
            # Filter what user actually has
            user_has = [item for item in sellable_items if self.character.has_item(item)]
            
            if not user_has:
                print_warning("You have nothing else to sell here.")
                input("Press Enter to leave...")
                break

            for i, item in enumerate(user_has, 1):
                val = sellable_items[item]
                print(f"{i}. Sell {item} for {Fore.YELLOW}{val} Gold{Style.RESET_ALL}")
            print(f"{len(user_has)+1}. Leave")

            try:
                choice = input("\nSell what? > ").strip()
                if choice == str(len(user_has) + 1):
                    break
                
                idx = int(choice) - 1
                if 0 <= idx < len(user_has):
                    item_name = user_has[idx]
                    val = sellable_items[item_name]
                    self.character.remove_item(item_name)
                    self.character.gold += val
                    print_success(f"Sold {item_name} for {val} Gold.")
                else:
                    print_error("Invalid number.")
            except ValueError:
                print_error("Invalid input.")

        self.character.current_location = page_data["next"]

    def handle_effect(self, page_data):
        self.display_page_text(page_data)
        if "effects" in page_data:
            summary = self.character.apply_effects(page_data["effects"])
            print_success(f"Update: {summary}")
        
        input("\nPress Enter...")
        self.character.current_location = page_data["next"]

    def handle_random_effect(self, page_data):
        """Handles 1d6 rolls that result in stat changes."""
        self.display_page_text(page_data)
        input("Press Enter to roll die...")
        roll = random.randint(1, 6)
        print_info(f"You rolled a {roll}!")
        
        # Process the template string (e.g., "-{roll}*3")
        effects = page_data["effect_template"].copy()
        for key, val in effects.items():
            if isinstance(val, str) and "{roll}" in val:
                # Safe eval of math expression
                expr = val.format(roll=roll)
                effects[key] = eval(expr) 
        
        summary = self.character.apply_effects(effects)
        print_success(f"Result: {summary}")
        input("Press Enter...")
        self.character.current_location = page_data["next"]

    def handle_luck_test(self, page_data):
        self.display_page_text(page_data)
        print_info(f"Your Luck: {self.character.luck}")
        input("Press Enter to Test Your Luck...")
        
        if self.character.test_luck():
            print_success("LUCKY! ✨")
            self.character.current_location = page_data["outcomes"]["lucky"]
        else:
            print_error("UNLUCKY! 💀")
            self.character.current_location = page_data["outcomes"]["unlucky"]
        time.sleep(1)

    def handle_luck_test_double(self, page_data):
        """Handles Page 128: Two darts, two separate luck tests."""
        self.display_page_text(page_data)
        
        # --- First Test ---
        print_bold(f"\n--- Dart 1 (Current Luck: {self.character.luck}) ---")
        input("Press Enter to dodge...")
        
        result_1 = "lucky" if self.character.test_luck() else "unlucky"
        
        if result_1 == "lucky":
            print_success("You dodged the first dart!")
        else:
            print_error("The first dart hit you!")
        
        time.sleep(1)

        # --- Second Test ---
        # Note: Your luck is now 1 point lower automatically
        print_bold(f"\n--- Dart 2 (Current Luck: {self.character.luck}) ---")
        input("Press Enter to dodge...")
        
        result_2 = "lucky" if self.character.test_luck() else "unlucky"
        
        if result_2 == "lucky":
            print_success("You dodged the second dart!")
        else:
            print_error("The second dart hit you!")
            
        time.sleep(1)

        # --- Determine Outcome ---
        outcome_key = f"{result_1}_{result_2}"
        
        self.character.current_location = page_data["outcomes"][outcome_key]

    def handle_skill_test(self, page_data):
        self.display_page_text(page_data)
        print_info(f"Your Skill: {self.character.skill}")
        input("Press Enter to Test Your Skill...")
        
        if self.character.test_skill():
            print_success("SUCCESS!")
            self.character.current_location = page_data["outcomes"]["success"]
        else:
            print_error("FAILURE!")
            self.character.current_location = page_data["outcomes"]["failure"]
        time.sleep(1)

    def handle_random_test(self, page_data):
        """Roll a die, check against a table (Page 223)."""
        self.display_page_text(page_data)
        input("Press Enter to roll...")
        roll = str(random.randint(1, 6))
        print_info(f"You rolled a {roll}.")
        
        outcomes = page_data["outcomes"]
        # Check specific numbers first, then ranges
        if roll in outcomes:
            res = outcomes[roll]
        elif "2-6" in outcomes and int(roll) >= 2:
            res = outcomes["2-6"]
        else:
            res = list(outcomes.values())[0] # Fallback

        if res == "GAME_OVER":
            self.handle_game_over({"text": "Bad luck. The pill was poison."})
        else:
            self.character.current_location = res

    def handle_condition_item(self, page_data):
        """Silent check for an item."""
        if self.character.has_item(page_data["check"]["item"]):
            self.character.current_location = page_data["outcomes"]["success"]
        else:
            self.character.current_location = page_data["outcomes"]["failure"]

    def handle_condition_multi(self, page_data):
        """Checks multiple conditions (Page 108/156)."""
        checks = page_data["checks"]
        passed = True
        
        # We need to simulate the 'silence' of this check usually, 
        # but for multi-checks specifically at the end of the game, it's good to know.
        for check in checks:
            if check["type"] == "item":
                if not self.character.has_item(check["value"]):
                    passed = False
                    break
        
        if passed:
            self.character.current_location = page_data["outcomes"]["success"]
        else:
            self.character.current_location = page_data["outcomes"]["failure"]

    def handle_condition_gold(self, page_data):
        if self.character.gold >= page_data["check"]["amount"]:
            self.character.current_location = page_data["outcomes"]["success"]
        else:
            self.character.current_location = page_data["outcomes"]["failure"]

    def handle_condition_item_any(self, page_data):
        """
        Handles Page 187: Checks if the player has AT LEAST ONE of the listed items.
        (OR Logic: Item A OR Item B OR Item C).
        """
        checks = page_data["checks"]
        found_item = False
        
        # Check inventory for any of the required items
        for check in checks:
            item_name = check["item"]
            
            # Use strict matching or partial matching depending on your preference.
            # Here we rely on character.has_item() which does case-insensitive check.
            if self.character.has_item(item_name):
                found_item = True
                break # We found one, that's enough
        
        if found_item:
            self.character.current_location = page_data["outcomes"]["success"]
        else:
            self.character.current_location = page_data["outcomes"]["failure"]

    def handle_random_encounter(self, page_data):
        """Page 201: Roll 1d6, fight random enemy."""
        self.display_page_text(page_data)
        input("Press Enter to see what appears...")
        roll = str(random.randint(1, 6))
        enemy_id = page_data["encounters"][roll]
        
        # Create a temporary combat page structure on the fly
        combat_data = {
            "text": f"A creature appears! It is a {self.enemy_data[enemy_id]['name']}!",
            "enemies": [enemy_id],
            "outcomes": page_data["outcomes"]
        }
        self.handle_combat(combat_data)

    def handle_dice_game(self, page_data):
        """Handles Page 206 (High Roll) and 378 (Hot Potato)."""
        self.display_page_text(page_data)
        rules = page_data.get("rules", {})
        game_type = rules.get("game_type", "high_roll")
        
        if game_type == "high_roll":
            # Page 206 logic
            stake = rules.get("stake", 2)
            max_plays = rules.get("max_plays", 4)
            plays = 0
            
            while plays < max_plays and self.character.gold >= stake:
                print_info(f"Gold: {self.character.gold}. Stake: {stake}")
                choice = input("Play a round? (y/n): ").lower()
                if choice != 'y': break
                
                plays += 1
                my_roll = random.randint(1, 6) + random.randint(1, 6)
                dwarf_roll = random.randint(1, 6) + random.randint(1, 6)
                
                print(f"You rolled: {my_roll} | Dwarf rolled: {dwarf_roll}")
                if my_roll > dwarf_roll:
                    print_success(f"You win {stake*4} gold!") # JSON implies winning 8 total?
                    self.character.gold += 8 
                elif dwarf_roll > my_roll:
                    print_error("You lost.")
                    self.character.gold -= stake
                else:
                    print("Draw.")
            
            self.character.current_location = page_data["next"]

        elif game_type == "hot_potato":
            # Page 378 logic: Roll alternately until 1 is thrown.
            wager = rules.get("wager", 5)
            while True:
                input("Press Enter to roll...")
                roll = random.randint(1, 6)
                print(f"You rolled: {roll}")
                if roll == 1:
                    print_error("You rolled a 1! You lose.")
                    self.character.gold -= wager
                    break
                
                time.sleep(0.5)
                opp_roll = random.randint(1, 6)
                print(f"Opponent rolled: {opp_roll}")
                if opp_roll == 1:
                    print_success("Opponent rolled a 1! You win.")
                    self.character.gold += wager
                    break
            
            self.character.current_location = page_data["next"]

    def handle_special_heal(self, page_data):
        """
        Handles Page 126: Heals based on how many times the player was hit previously,
        then applies mandatory stat/item changes.
        """
        self.display_page_text(page_data)
        
        heal_unit = page_data.get("heal_per_arrow", 2)

        # 1. Ask user for context from the previous encounter
        print_info("The old man looks at your wounds...")
        while True:
            try:
                # We must ask the user because the engine doesn't remember the specific result of the previous page's random damage roll.
                arrows = int(input("How many arrows hit you on the previous page? (Enter 0 if none): "))
                if arrows < 0:
                    print_error("Invalid number.")
                    continue
                break
            except ValueError:
                print_error("Please enter a number.")

        # 2. Apply Healing
        if arrows > 0:
            total_heal = arrows * heal_unit
            old_stamina = self.character.stamina
            self.character.heal(total_heal)
            actual_healed = self.character.stamina - old_stamina
            print_success(f"He removed {arrows} arrows. You regained {actual_healed} STAMINA.")
        else:
            print_info("You have no arrow wounds to heal.")

        time.sleep(1)

        # 3. Apply Mandatory Effects (Trade Swords, Lose Skill)
        if "effects" in page_data:
            summary = self.character.apply_effects(page_data["effects"])
            print_warning(f"Exchange: {summary}")

        input("\nPress Enter to continue...")
        self.character.current_location = page_data["next"]

    def handle_combat(self, page_data):
        if "text" in page_data: 
            self.display_page_text(page_data)
        
        print_warning("⚔️  COMBAT BEGINS  ⚔️")
        
        # Load enemies
        enemies = []
        if "enemies" in page_data:
            for eid in page_data["enemies"]:
                 enemies.append(self.enemy_data[eid].copy())
        
        rules = page_data.get("rules", {})
        combat_rounds = 0
        escaped = False

        for enemy in enemies:
            if self.character.is_dead() or escaped: break
            
            print_bold(f"\nEnemy: {enemy['name']} (SKILL: {enemy['skill']}, STAMINA: {enemy['stamina']})")
            input("Press Enter to engage...")

            while not self.character.is_dead() and enemy['stamina'] > 0:
                combat_rounds += 1
                
                # Check escape rules
                if "escape_after_rounds" in rules:
                    if combat_rounds > rules["escape_after_rounds"]["rounds"]:
                        print_info("You manage to escape!")
                        self.character.current_location = rules["escape_after_rounds"]["page"]
                        escaped = True
                        break

                # Rolls
                p_roll = random.randint(1,6) + random.randint(1,6)
                p_attack = p_roll + self.character.skill
                
                e_roll = random.randint(1,6) + random.randint(1,6)
                e_attack = e_roll + enemy['skill']

                print(f"Round {combat_rounds}: You {p_attack} ({p_roll}) vs Enemy {e_attack} ({e_roll})")
                time.sleep(0.3)

                damage = 2
                
                if p_attack > e_attack:
                    print_success("HIT!")
                    if self.character.luck > 0:
                        want_luck = input("Test Luck for double damage? (y/n): ").lower()
                        if want_luck == 'y':
                            if self.character.test_luck():
                                print_success("LUCKY! 4 Damage!")
                                damage = 4
                            else:
                                print_error("Unlucky. 1 Damage.")
                                damage = 1
                    
                    enemy['stamina'] -= damage
                    print(f"{enemy['name']} HP: {enemy['stamina']}")

                elif e_attack > p_attack:
                    print_error("OUCH!")
                    if self.character.luck > 0:
                        want_luck = input("Test Luck to reduce damage? (y/n): ").lower()
                        if want_luck == 'y':
                            if self.character.test_luck():
                                print_success("LUCKY! 1 Damage taken.")
                                damage = 1
                            else:
                                print_error("Unlucky. 3 Damage taken.")
                                damage = 3
                    
                    self.character.take_damage(damage)
                    print(f"Your HP: {self.character.stamina}")

                else:
                    print("Clash! No damage.")

        # Determine outcome
        if self.character.is_dead():
            self.character.current_location = page_data["outcomes"]["lose"]
        
        elif not escaped:
            # Check for special win conditions
            if "max_rounds" in rules:
                if combat_rounds <= rules["max_rounds"]:
                    print_success("You defeated him quickly!")
                    self.character.current_location = page_data["outcomes"]["win_fast"]
                else:
                    print_warning("The fight took too long...")
                    self.character.current_location = page_data["outcomes"]["win_slow"]
            
            # Standard win
            else:
                self.character.current_location = page_data["outcomes"]["win"]

    def handle_multi_combat(self, page_data):
        """
        Handles fighting multiple enemies simultaneously (e.g., as a pair).
        - You select a target to attack.
        - You compare your AS against the target (deal/take damage).
        - You compare your AS against the other(s) (only take damage).
        """
        if "text" in page_data:
            self.display_page_text(page_data)
        
        print_warning("⚔️  SIMULTANEOUS COMBAT!  ⚔️")
        print_info("You must defend against all enemies, but you can only hurt one per round.")

        # Load enemies
        enemies = []
        if "enemies" in page_data:
            for eid in page_data["enemies"]:
                 enemies.append(self.enemy_data[eid].copy())
        
        combat_round = 0

        # Loop while Player is alive AND at least one enemy is alive
        while not self.character.is_dead() and any(e['stamina'] > 0 for e in enemies):
            combat_round += 1
            print_bold(f"\n--- Round {combat_round} ---")
            
            # 1. List active enemies
            active_enemies = [e for e in enemies if e['stamina'] > 0]
            
            # 2. Player chooses target
            target = None
            if len(active_enemies) > 1:
                print("Choose your target:")
                for i, e in enumerate(active_enemies, 1):
                    print(f"{i}. {e['name']} (SK: {e['skill']}, ST: {e['stamina']})")
                
                while not target:
                    try:
                        choice = int(input("> ")) - 1
                        if 0 <= choice < len(active_enemies):
                            target = active_enemies[choice]
                    except ValueError:
                        pass
            else:
                target = active_enemies[0] # Only one left

            print_info(f"Targeting: {target['name']}")
            time.sleep(0.5)

            # 3. Roll Player Attack Strength
            p_roll = random.randint(1, 6) + random.randint(1, 6)
            p_attack = p_roll + self.character.skill
            print(f"You rolled {p_roll} + {self.character.skill} Skill = {Fore.CYAN}{p_attack} AS{Style.RESET_ALL}")

            # 4. Process Every Enemy
            for enemy in active_enemies:
                e_roll = random.randint(1, 6) + random.randint(1, 6)
                e_attack = e_roll + enemy['skill']
                
                print(f"{enemy['name']} rolled {e_roll} + {enemy['skill']} Skill = {Fore.RED}{e_attack} AS{Style.RESET_ALL}")
                time.sleep(0.5)

                damage = 2

                # Case A: Targeted enemy
                if enemy == target:
                    if p_attack > e_attack:
                        print_success(f"--> You HIT {enemy['name']}!")
                        # Luck Logic (Damage Dealt)
                        if self.character.luck > 0:
                            w = input("Test Luck for double damage? (y/n): ").lower()
                            if w == 'y':
                                if self.character.test_luck():
                                    print_success("LUCKY! 4 Damage!")
                                    damage = 4
                                else:
                                    print_error("Unlucky. 1 Damage.")
                                    damage = 1
                        enemy['stamina'] -= damage
                    
                    elif e_attack > p_attack:
                        print_error(f"<-- {enemy['name']} HITS YOU!")
                        # Luck Logic (Damage Taken)
                        if self.character.luck > 0:
                            w = input("Test Luck to reduce damage? (y/n): ").lower()
                            if w == 'y':
                                if self.character.test_luck():
                                    print_success("LUCKY! 1 Damage taken.")
                                    damage = 1
                                else:
                                    print_error("Unlucky. 3 Damage taken.")
                                    damage = 3
                        self.character.take_damage(damage)
                    else:
                        print_info("-- Clash! No damage.")

                # Case B: Extra enemy
                else:
                    if e_attack > p_attack:
                        print_error(f"<-- {enemy['name']} HITS YOU (Flanked)!")
                         # Luck Logic (Damage Taken)
                        if self.character.luck > 0:
                            w = input("Test Luck to reduce damage? (y/n): ").lower()
                            if w == 'y':
                                if self.character.test_luck():
                                    print_success("LUCKY! 1 Damage taken.")
                                    damage = 1
                                else:
                                    print_error("Unlucky. 3 Damage taken.")
                                    damage = 3
                        self.character.take_damage(damage)
                    else:
                        print_info(f"-- You parried {enemy['name']}.")
                
                # Check player death immediately
                if self.character.is_dead():
                    break
            
            # End of round summary
            print(f"Your Stamina: {self.character.stamina}")
            time.sleep(1)

        # Outcome
        if self.character.is_dead():
            self.character.current_location = page_data["outcomes"]["lose"]
        else:
            print_success("\nYou have defeated the pair!")
            self.character.current_location = page_data["outcomes"]["win"]
        
        input("\nPress Enter...")

    def handle_game_over(self, page_data):
        clear_screen()
        print_header("GAME OVER")
        print_wrapped(page_data.get('text', ''))
        self.delete_character()
        self.running = False
        input("\nPress Enter to return to menu...")

    def handle_victory(self, page_data):
        clear_screen()
        print_header("VICTORY!")
        print_wrapped(page_data.get('text', ''))
        print_success("You have conquered the City of Thieves!")
        self.delete_character()
        self.running = False
        input("\nPress Enter to return to menu...")

    def handle_unknown(self, page_data):
        print_error(f"Unknown Page Type: {page_data.get('type')}")
        self.running = False
        input("Press Enter...")
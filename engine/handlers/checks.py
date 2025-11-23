import time
import random
from .base import BaseHandler
from engine.utils import print_bold, print_error, print_success, print_info, print_warning

class CheckHandler(BaseHandler):

    def handle_effect(self, page_data):
        self.display(page_data)
        if "effects" in page_data:
            summary = self.game.character.apply_effects(page_data["effects"])
            print_success(f"Update: {summary}")
        
        input("\nPress Enter...")
        self.game.character.current_location = page_data["next"]

    def handle_random_effect(self, page_data):
        self.display(page_data)
        input("Press Enter to roll die...")
        roll = random.randint(1, 6)
        print_info(f"You rolled a {roll}!")
        
        effects = page_data["effect_template"].copy()
        for key, val in effects.items():
            if isinstance(val, str) and "{roll}" in val:
                expr = val.format(roll=roll)
                effects[key] = eval(expr) 
        
        summary = self.game.character.apply_effects(effects)
        print_success(f"Result: {summary}")
        input("Press Enter...")
        self.game.character.current_location = page_data["next"]

    def handle_luck_test(self, page_data):
        self.display(page_data)
        print_info(f"Your Luck: {self.game.character.luck}")
        input("Press Enter to Test Your Luck...")
        
        if self.game.character.test_luck():
            print_success("LUCKY! ✨")
            self.game.character.current_location = page_data["outcomes"]["lucky"]
        else:
            print_error("UNLUCKY! 💀")
            self.game.character.current_location = page_data["outcomes"]["unlucky"]
        time.sleep(1)

    def handle_luck_test_double(self, page_data):
        self.display(page_data)
        print_bold(f"\n--- First Test (Luck: {self.game.character.luck}) ---")
        input("Press Enter...")
        res1 = "lucky" if self.game.character.test_luck() else "unlucky"
        print(res1.upper())
        
        time.sleep(1)
        print_bold(f"\n--- Second Test (Luck: {self.game.character.luck}) ---")
        input("Press Enter...")
        res2 = "lucky" if self.game.character.test_luck() else "unlucky"
        print(res2.upper())

        outcome_key = f"{res1}_{res2}"
        self.game.character.current_location = page_data["outcomes"][outcome_key]

    def handle_skill_test(self, page_data):
        self.display(page_data)
        print_info(f"Your Skill: {self.game.character.skill}")
        input("Press Enter to Test Your Skill...")
        
        if self.game.character.test_skill():
            print_success("SUCCESS!")
            self.game.character.current_location = page_data["outcomes"]["success"]
        else:
            print_error("FAILURE!")
            self.game.character.current_location = page_data["outcomes"]["failure"]
        time.sleep(1)

    def handle_random_test(self, page_data):
        self.display(page_data)
        input("Press Enter to roll...")
        roll = str(random.randint(1, 6))
        print_info(f"You rolled a {roll}.")
        
        outcomes = page_data["outcomes"]
        if roll in outcomes:
            res = outcomes[roll]
        elif "2-6" in outcomes and int(roll) >= 2:
            res = outcomes["2-6"]
        else:
            res = list(outcomes.values())[0]

        if res == "GAME_OVER":
            self.game.handlers['story'].handle_game_over({"text": "Bad luck."})
        else:
            self.game.character.current_location = res

    def handle_condition_item(self, page_data):
        if self.game.character.has_item(page_data["check"]["item"]):
            self.game.character.current_location = page_data["outcomes"]["success"]
        else:
            self.game.character.current_location = page_data["outcomes"]["failure"]

    def handle_condition_item_any(self, page_data):
        checks = page_data["checks"]
        found_item = False
        for check in checks:
            if self.game.character.has_item(check["item"]):
                found_item = True
                break
        if found_item:
            self.game.character.current_location = page_data["outcomes"]["success"]
        else:
            self.game.character.current_location = page_data["outcomes"]["failure"]

    def handle_condition_multi(self, page_data):
        checks = page_data["checks"]
        passed = True
        for check in checks:
            if check["type"] == "item":
                if not self.game.character.has_item(check["value"]):
                    passed = False
                    break
        if passed:
            self.game.character.current_location = page_data["outcomes"]["success"]
        else:
            self.game.character.current_location = page_data["outcomes"]["failure"]

    def handle_condition_gold(self, page_data):
        if self.game.character.gold >= page_data["check"]["amount"]:
            self.game.character.current_location = page_data["outcomes"]["success"]
        else:
            self.game.character.current_location = page_data["outcomes"]["failure"]

    def handle_condition_combat(self, page_data):
        """Checks who we fought recently (Page 138)."""
        target_enemy = page_data["check"].get("last_enemy_fought", "").lower()
        # Game engine needs to track this during combat
        last_fought = getattr(self.game, "last_enemy_fought", "").lower()
        
        # Flexible matching
        if target_enemy in last_fought:
            self.game.character.current_location = page_data["outcomes"]["success"]
        else:
            self.game.character.current_location = page_data["outcomes"]["failure"]

    def handle_random_encounter(self, page_data):
        self.display(page_data)
        input("Press Enter to see what appears...")
        roll = str(random.randint(1, 6))
        enemy_id = page_data["encounters"][roll]
        
        combat_data = {
            "text": f"A creature appears! It is a {self.game.enemy_data[enemy_id]['name']}!",
            "enemies": [enemy_id],
            "outcomes": page_data["outcomes"]
        }
        self.game.handlers['combat'].handle_combat(combat_data)

    def handle_special_heal(self, page_data):
        self.display(page_data)
        heal_unit = page_data.get("heal_per_arrow", 2)
        print_info("The old man looks at your wounds...")
        while True:
            try:
                arrows = int(input("How many arrows hit you? (0 if none): "))
                if arrows < 0: continue
                break
            except ValueError: pass

        if arrows > 0:
            total = arrows * heal_unit
            self.game.character.heal(total)
            print_success(f"Regained {total} STAMINA.")
        
        if "effects" in page_data:
            summary = self.game.character.apply_effects(page_data["effects"])
            print_warning(f"Exchange: {summary}")

        input("\nPress Enter...")
        self.game.character.current_location = page_data["next"]
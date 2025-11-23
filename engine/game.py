import sys
from colorama import Fore, Style
from models.character import Character
from engine.storage import SaveManager
from engine.utils import clear_screen, print_header, print_error, print_success, print_warning, print_wrapped, print_bold

# Import handlers
from engine.handlers import CombatHandler, StoryHandler, CommerceHandler, CheckHandler

class GameEngine:
    def __init__(self, story_data, enemy_data):
        self.story_data = story_data
        self.enemy_data = enemy_data
        self.user_id = "local_player"
        self.character = None
        self.running = False
        self.last_enemy_fought = "" # Runtime state for conditions
        
        # 1. Init Storage
        self.save_manager = SaveManager()

        # 2. Init Handlers
        self.handlers = {
            'story': StoryHandler(self),
            'combat': CombatHandler(self),
            'commerce': CommerceHandler(self),
            'check': CheckHandler(self)
        }

    # --- Persistence Wrappers ---
    def save_character(self):
        if self.character: self.save_manager.save_character(self.character)

    def load_character(self):
        return self.save_manager.load_character(self.user_id)

    def delete_character(self):
        return self.save_manager.delete_character(self.user_id)

    # --- Global Input ---
    def get_input_cmd(self):
        print(f"\n{Fore.LIGHTBLACK_EX}[Commands: # to choose, 's' for stats, 'e' to eat, 'q' to quit]{Style.RESET_ALL}")
        return input("> ").strip().lower()

    def handle_global_commands(self, cmd):
        if cmd == 'q': 
            self.running = False
            return True
        if cmd == 's': 
            print(self.character)
            return True
        if cmd == 'e': 
            print_bold(self.character.eat_provision())
            return True
        return False

    def display_page_text(self, page_data):
        print_header(f"Page {self.character.current_location}")
        if "text" in page_data and page_data["text"]:
            print_wrapped(page_data['text'])
            print("-" * 60)

    # --- The Dispatcher ---
    def dispatch(self, page_data):
        ptype = page_data.get("type", "choice")
        
        mapping = {
            # Story
            "choice":           self.handlers['story'].handle_choice,
            "auto":             self.handlers['story'].handle_auto,
            "game_over":        self.handlers['story'].handle_game_over,
            "victory":          self.handlers['story'].handle_victory,
            
            # Combat
            "combat":           self.handlers['combat'].handle_combat,
            "multi_combat":     self.handlers['combat'].handle_multi_combat,
            
            # Commerce
            "transaction":      self.handlers['commerce'].handle_transaction,
            "shop":             self.handlers['commerce'].handle_shop,
            "shop_multi":       self.handlers['commerce'].handle_shop_multi,
            "pawn_shop":        self.handlers['commerce'].handle_pawn_shop,
            "dice_game":        self.handlers['commerce'].handle_dice_game,
            
            # Checks/Conditions
            "luck_test":        self.handlers['check'].handle_luck_test,
            "luck_test_double": self.handlers['check'].handle_luck_test_double,
            "skill_test":       self.handlers['check'].handle_skill_test,
            "random_test":      self.handlers['check'].handle_random_test,
            "effect":           self.handlers['check'].handle_effect,
            "random_effect":    self.handlers['check'].handle_random_effect,
            "condition_item":   self.handlers['check'].handle_condition_item,
            "condition_multi":  self.handlers['check'].handle_condition_multi,
            "condition_item_any": self.handlers['check'].handle_condition_item_any,
            "condition_gold":   self.handlers['check'].handle_condition_gold,
            "condition_combat": self.handlers['check'].handle_condition_combat,
            "random_encounter": self.handlers['check'].handle_random_encounter,
            "special_heal":     self.handlers['check'].handle_special_heal,
        }

        if ptype in mapping:
            mapping[ptype](page_data)
        else:
            print_error(f"Unknown Page Type: {ptype}")
            self.running = False
            input("Press Enter...")

    # --- Main Loop ---
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
                print_error(f"FATAL: Page {page_id} missing.")
                self.running = False
                break

            self.dispatch(page_data)

            if self.character.is_dead():
                print_error("\nYour STAMINA has reached 0.")
                self.handlers['story'].handle_game_over({"text": "You have died."})
            
            if self.running:
                self.save_character()

    def create_character_flow(self):
        clear_screen()
        print_header("NEW ADVENTURE")
        if self.load_character():
            print_warning("Character exists. Overwrite? (y/n)")
            if input("> ").lower() != 'y': return False

        name = input("\nName: ").strip() or "Adventurer"
        self.character = Character(name=name, user_id=self.user_id)
        
        if name.lower() == "ian livingstone":
            print_success("GOD MODE")
            self.character.skill = 12
            self.character.stamina = 24
            self.character.luck = 12
            self.character.max_skill = 12
            self.character.max_stamina = 24
            self.character.max_luck = 12
            self.character.gold = 50

        self.save_character()
        print(self.character)
        input("\nPress Enter...")
        return True
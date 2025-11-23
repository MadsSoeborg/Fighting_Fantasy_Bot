import time
import random
from colorama import Fore, Style
from .base import BaseHandler
from engine.utils import print_bold, print_error, print_success, print_warning, print_info

class CommerceHandler(BaseHandler):

    def handle_transaction(self, page_data):
        self.display(page_data)
        choices = page_data["choices"]
        options = list(choices.items())

        for i, (text, data) in enumerate(options, 1):
            cost = data.get("cost", 0)
            cost_str = f"{Fore.YELLOW}({cost} Gold){Style.RESET_ALL}" if cost > 0 else ""
            print(f"{i}. {text} {cost_str}")

        while True:
            cmd = self.game.get_input_cmd()
            if self.game.handle_global_commands(cmd): continue

            try:
                idx = int(cmd) - 1
                if 0 <= idx < len(options):
                    _, data = options[idx]
                    cost = data.get("cost", 0)
                    
                    if self.game.character.gold < cost:
                        print_warning(f"Not enough gold! You have {self.game.character.gold}.")
                        continue
                    
                    if cost > 0:
                        self.game.character.gold -= cost
                        print_info(f"You pay {cost} Gold.")

                    if "effect" in data:
                        summary = self.game.character.apply_effects(data["effect"])
                        print_success(f"Gained: {summary}")
                        time.sleep(1)

                    self.game.character.current_location = data["next"]
                    return
            except ValueError:
                pass

    def handle_shop(self, page_data):
        """Simple wrapper for shop_multi."""
        self.handle_shop_multi(page_data)

    def handle_shop_multi(self, page_data):
        self.display(page_data)
        items = page_data["items"] # Dict of "Item Name": Cost
        
        while True:
            print_bold(f"\nYour Gold: {self.game.character.gold}")
            item_list = list(items.items())
            
            for i, (name, cost) in enumerate(item_list, 1):
                print(f"{i}. {name} - {Fore.YELLOW}{cost} Gold{Style.RESET_ALL}")
            print(f"{len(item_list)+1}. Leave Shop")

            try:
                choice = input("\nBuy which item? > ").strip()
                if choice == str(len(item_list) + 1):
                    break
                
                idx = int(choice) - 1
                if 0 <= idx < len(item_list):
                    name, cost = item_list[idx]
                    if self.game.character.gold >= cost:
                        self.game.character.gold -= cost
                        self.game.character.add_item(name)
                        print_success(f"Bought {name}!")
                    else:
                        print_warning("Not enough gold!")
                else:
                    print_error("Invalid number.")
            except ValueError:
                print_error("Invalid input.")

        if "next" in page_data:
            self.game.character.current_location = page_data["next"]

    def handle_pawn_shop(self, page_data):
        self.display(page_data)
        sellable_items = page_data["items"] # Dict "Item": Value

        while True:
            print_bold(f"\nYour Inventory: {', '.join(self.game.character.inventory)}")
            print_bold(f"Your Gold: {self.game.character.gold}")
            
            user_has = [item for item in sellable_items if self.game.character.has_item(item)]
            
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
                    self.game.character.remove_item(item_name)
                    self.game.character.gold += val
                    print_success(f"Sold {item_name} for {val} Gold.")
                else:
                    print_error("Invalid number.")
            except ValueError:
                print_error("Invalid input.")

        self.game.character.current_location = page_data["next"]

    def handle_dice_game(self, page_data):
        self.display(page_data)
        rules = page_data.get("rules", {})
        game_type = rules.get("game_type", "high_roll")
        
        if game_type == "high_roll":
            stake = rules.get("stake", 2)
            max_plays = rules.get("max_plays", 4)
            plays = 0
            
            while plays < max_plays and self.game.character.gold >= stake:
                print_info(f"Gold: {self.game.character.gold}. Stake: {stake}")
                choice = input("Play a round? (y/n): ").lower()
                if choice != 'y': break
                
                plays += 1
                my_roll = random.randint(1, 6) + random.randint(1, 6)
                dwarf_roll = random.randint(1, 6) + random.randint(1, 6)
                
                print(f"You rolled: {my_roll} | Dwarf rolled: {dwarf_roll}")
                if my_roll > dwarf_roll:
                    print_success(f"You win {stake*4} gold!")
                    self.game.character.gold += (stake * 4)
                elif dwarf_roll > my_roll:
                    print_error("You lost.")
                    self.game.character.gold -= stake
                else:
                    print("Draw.")
            
            self.game.character.current_location = page_data["next"]

        elif game_type == "hot_potato":
            wager = rules.get("wager", 5)
            while True:
                input("Press Enter to roll...")
                roll = random.randint(1, 6)
                print(f"You rolled: {roll}")
                if roll == 1:
                    print_error("You rolled a 1! You lose.")
                    self.game.character.gold -= wager
                    break
                
                time.sleep(0.5)
                opp_roll = random.randint(1, 6)
                print(f"Opponent rolled: {opp_roll}")
                if opp_roll == 1:
                    print_success("Opponent rolled a 1! You win.")
                    self.game.character.gold += wager
                    break
            
            self.game.character.current_location = page_data["next"]
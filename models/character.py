import random
from colorama import Fore, Style

class Character:
    def __init__(self, name, user_id="local_player"):
        self.name = name
        self.user_id = str(user_id)
        self.skill = self.roll_dice(1) + 6
        self.stamina = self.roll_dice(2) + 12
        self.luck = self.roll_dice(1) + 6
        self.max_skill = self.skill
        self.max_stamina = self.stamina
        self.max_luck = self.luck
        self.inventory = ["Sword", "Leather Armour", "Backpack"]
        self.gold = self.roll_dice(1) + 8
        self.provisions = 10
        self.current_location = "1"

    @staticmethod
    def roll_dice(number_of_dice):
        return sum(random.randint(1, 6) for _ in range(number_of_dice))

    def take_damage(self, amount):
        self.stamina = max(0, self.stamina - amount)

    def heal(self, amount):
        self.stamina = min(self.max_stamina, self.stamina + amount)

    def is_dead(self):
        return self.stamina <= 0

    def test_skill(self):
        return self.roll_dice(2) <= self.skill

    def test_luck(self):
        if self.luck <= 0: return False
        is_lucky = self.roll_dice(2) <= self.luck
        self.luck = max(0, self.luck - 1)
        return is_lucky

    def has_item(self, item_name):
        return item_name.lower() in (item.lower() for item in self.inventory)
        
    def add_item(self, item_name):
        if not self.has_item(item_name):
            self.inventory.append(item_name)

    def remove_item(self, item_name):
        item_to_remove = next((item for item in self.inventory if item.lower() == item_name.lower()), None)
        if item_to_remove:
            self.inventory.remove(item_to_remove)

    def eat_provision(self):
        if self.provisions > 0:
            if self.stamina >= self.max_stamina:
                return "Your stamina is already full."
            
            self.provisions -= 1
            self.heal(4) # 1 provision = 4 stamina
            return f"You ate a meal. Stamina is now {self.stamina}/{self.max_stamina}. Provisions left: {self.provisions}"
        else:
            return "You have no provisions left!"

    def apply_effects(self, effects):
        summary = []
        
        # --- STAMINA ---
        if "stamina" in effects and effects["stamina"] != 0:
            # Prevent going above Max, but also prevent going below 0
            new_val = self.stamina + effects["stamina"]
            self.stamina = max(0, min(self.max_stamina, new_val))
            
            sign = '+' if effects['stamina'] > 0 else ''
            summary.append(f"{sign}{effects['stamina']} STAMINA")

        # --- SKILL ---
        if "skill" in effects and effects["skill"] != 0:
            new_val = self.skill + effects["skill"]
            self.skill = max(0, min(self.max_skill, new_val))
            
            sign = '+' if effects['skill'] > 0 else ''
            summary.append(f"{sign}{effects['skill']} SKILL")

        # --- LUCK ---
        if "luck" in effects and effects["luck"] != 0:
            new_val = self.luck + effects["luck"]
            # Luck can be restored, but never higher than Initial (Max) Luck
            self.luck = max(0, min(self.max_luck, new_val))
            
            sign = '+' if effects['luck'] > 0 else ''
            summary.append(f"{sign}{effects['luck']} LUCK")

        # --- GOLD ---
        if "gold" in effects:
            # Special case for "lose all gold" or "set to 0"
            if isinstance(effects["gold"], str) and effects["gold"] == "set_to_0":
                val_change = self.gold * -1
                self.gold = 0
                summary.append("Lost all Gold")
            elif isinstance(effects["gold"], int) and effects["gold"] != 0:
                self.gold = max(0, self.gold + effects["gold"])
                sign = '+' if effects['gold'] > 0 else ''
                summary.append(f"{sign}{effects['gold']} Gold")

        # --- ITEMS ---
        if "add_items" in effects:
            for item in effects["add_items"]:
                self.add_item(item)
                summary.append(f"Gained: {item}")
        
        if "remove_items" in effects:
            for item in effects["remove_items"]:
                self.remove_item(item)
                summary.append(f"Lost: {item}")
        
        # Special logic for random item loss
        if "lose_random_items" in effects:
            count = effects["lose_random_items"]
            lost = []
            for _ in range(count):
                if self.inventory:
                    item = random.choice(self.inventory)
                    self.inventory.remove(item)
                    lost.append(item)
            if lost:
                summary.append(f"Lost random items: {', '.join(lost)}")

        return ", ".join(summary)

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        char = cls(name=data['name'], user_id=data.get('user_id', 'local_player'))
        char.__dict__.update(data)
        return char

    def __str__(self):
        inventory_str = ', '.join(self.inventory) if self.inventory else "Empty"
        return (
            f"{Fore.YELLOW}{Style.BRIGHT}=== {self.name}'s Stats ==={Style.RESET_ALL}\n"
            f"SKILL:   {self.skill}/{self.max_skill}\n"
            f"STAMINA: {self.stamina}/{self.max_stamina}\n"
            f"LUCK:    {self.luck}/{self.max_luck}\n"
            f"Gold: {self.gold} | Provisions: {self.provisions}\n"
            f"Inventory: {inventory_str}"
        )
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

    def apply_effects(self, effects):
        summary = []
        if "stamina" in effects and effects["stamina"] != 0:
            self.stamina = min(self.max_stamina, self.stamina + effects["stamina"])
            summary.append(f"{'+' if effects['stamina'] > 0 else ''}{effects['stamina']} STAMINA")
        if "skill" in effects and effects["skill"] != 0:
            self.skill = min(self.max_skill, self.skill + effects["skill"])
            summary.append(f"{'+' if effects['skill'] > 0 else ''}{effects['skill']} SKILL")
        if "luck" in effects and effects["luck"] != 0:
            self.luck = min(self.max_luck, self.luck + effects["luck"])
            summary.append(f"{'+' if effects['luck'] > 0 else ''}{effects['luck']} LUCK")
        if "gold" in effects and effects["gold"] != 0:
            self.gold += effects["gold"]
            summary.append(f"{'+' if effects['gold'] > 0 else ''}{effects['gold']} Gold")
        if "add_items" in effects:
            for item in effects["add_items"]:
                self.add_item(item)
                summary.append(f"Gained: {item}")
        if "remove_items" in effects:
            for item in effects["remove_items"]:
                self.remove_item(item)
                summary.append(f"Lost: {item}")
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
import random


class Character:
    def __init__(self, name):
        self.name = name
        self.skill = self.roll_dice(1) + 6
        self.stamina = self.roll_dice(2) + 12
        self.luck = self.roll_dice(1) + 6
        self.inventory = []
        self.max_skill = self.skill
        self.max_stamina = self.stamina
        self.max_luck = self.luck

    @staticmethod
    def roll_dice(number_of_dice):
        return sum(random.randint(1, 6) for _ in range(number_of_dice))

    def test_skill(self):
        return self.roll_dice(2) <= self.skill

    def test_luck(self):
        result = self.roll_dice(2) <= self.luck
        self.luck = max(0, self.luck - 1)
        return result

    def test_stamina(self):
        return self.roll_dice(4) <= self.stamina

    def increase_skill(self, amount, allow_above_max=False):
        if allow_above_max:
            self.skill += amount
        else:
            self.skill = min(self.skill + amount, self.max_skill)

    def increase_stamina(self, amount, allow_above_max=False):
        if allow_above_max:
            self.stamina += amount
        else:
            self.stamina = min(self.stamina + amount, self.max_stamina)

    def increase_luck(self, amount, allow_above_max=False):
        if allow_above_max:
            self.luck += amount
        else:
            self.luck = min(self.luck + amount, self.max_luck)

    def add_to_inventory(self, item):
        self.inventory.append(item)

    def use_item(self, item):
        if item in self.inventory:
            # Do something with the item and remove it from the inventory
            pass

    def __str__(self):
        return (
            f"{self.name}\n"
            f"SKILL: {self.skill}/{self.max_skill}\n"
            f"STAMINA: {self.stamina}/{self.max_stamina}\n"
            f"LUCK: {self.luck}/{self.max_luck}\n"
            f"Inventory: {', '.join(self.inventory)}"
        )

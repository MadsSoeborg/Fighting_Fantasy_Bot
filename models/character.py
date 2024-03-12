import random


class Character:
    def __init__(self, name):
        self.name = name
        self.skill = self.roll_dice(1) + 6
        self.stamina = self.roll_dice(2) + 12
        self.luck = self.roll_dice(1) + 6
        self.inventory = []

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

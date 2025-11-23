from models.character import Character

class GameState:
    """A class to hold the state of a single player's game."""
    def __init__(self, character: Character):
        self.character = character
        self.combat_rounds = 0

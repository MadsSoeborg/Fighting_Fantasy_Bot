import json
import os
from models.character import Character

class SaveManager:
    def __init__(self, file_path="data/characters.json"):
        self.file_path = file_path

    def _load_all(self):
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_all(self, data):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_character(self, user_id):
        data = self._load_all()
        if user_id in data:
            return Character.from_dict(data[user_id])
        return None

    def save_character(self, character):
        data = self._load_all()
        data[character.user_id] = character.to_dict()
        self._save_all(data)

    def delete_character(self, user_id):
        data = self._load_all()
        if user_id in data:
            del data[user_id]
            self._save_all(data)
            return True
        return False
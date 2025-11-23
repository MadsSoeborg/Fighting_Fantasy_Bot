from .base import BaseHandler
from engine.utils import print_error, print_success, clear_screen, print_header, print_wrapped

class StoryHandler(BaseHandler):
    
    def handle_choice(self, page_data):
        self.display(page_data)
        choices = page_data["choices"]
        options = list(choices.keys())
        
        for i, text in enumerate(options, 1):
            print(f"{i}. {text}")

        while True:
            cmd = self.game.get_input_cmd()
            if self.game.handle_global_commands(cmd): continue

            try:
                idx = int(cmd) - 1
                if 0 <= idx < len(options):
                    self.game.character.current_location = choices[options[idx]]
                    return
            except ValueError:
                pass
            print_error("Invalid choice.")

    def handle_auto(self, page_data):
        self.display(page_data)
        input("\nPress Enter to continue...")
        self.game.character.current_location = page_data["next"]

    def handle_game_over(self, page_data):
        clear_screen()
        print_header("GAME OVER")
        print_wrapped(page_data.get('text', ''))
        self.game.delete_character()
        self.game.running = False
        input("\nPress Enter to return to menu...")

    def handle_victory(self, page_data):
        clear_screen()
        print_header("VICTORY!")
        print_wrapped(page_data.get('text', ''))
        print_success("You have conquered the City of Thieves!")
        self.game.delete_character()
        self.game.running = False
        input("\nPress Enter to return to menu...")
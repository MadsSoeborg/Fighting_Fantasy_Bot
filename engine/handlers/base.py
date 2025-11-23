class BaseHandler:
    def __init__(self, game_engine):
        self.game = game_engine
        
    def display(self, page_data):
        self.game.display_page_text(page_data)
import time
import random
from colorama import Fore, Style
from .base import BaseHandler
from engine.utils import print_bold, print_error, print_success, print_warning, print_info

class CombatHandler(BaseHandler):

    def handle_combat(self, page_data):
        if "text" in page_data: 
            self.display(page_data)
        
        print_warning("⚔️  COMBAT BEGINS  ⚔️")
        
        # Load enemies
        enemies = []
        if "enemies" in page_data:
            for eid in page_data["enemies"]:
                 enemies.append(self.game.enemy_data[eid].copy())
        
        rules = page_data.get("rules", {})
        combat_rounds = 0
        escaped = False

        for enemy in enemies:
            if self.game.character.is_dead() or escaped: break
            
            # Track for condition_combat checks later
            self.game.last_enemy_fought = enemy['name'] 

            print_bold(f"\nEnemy: {enemy['name']} (SKILL: {enemy['skill']}, STAMINA: {enemy['stamina']})")
            input("Press Enter to engage...")

            while not self.game.character.is_dead() and enemy['stamina'] > 0:
                combat_rounds += 1
                
                # Check escape rules
                if "escape_after_rounds" in rules:
                    if combat_rounds > rules["escape_after_rounds"]["rounds"]:
                        print_info("You manage to escape!")
                        self.game.character.current_location = rules["escape_after_rounds"]["page"]
                        escaped = True
                        break
                
                # Check unconditional escape (e.g. Lizardine fire breath)
                if "escape_unconditional" in rules:
                     # Some logic might trigger this immediately or after 1 round. 
                     # Usually implies specific item failure or just surviving 1 round.
                     pass 

                # Rolls
                p_roll = random.randint(1,6) + random.randint(1,6)
                p_attack = p_roll + self.game.character.skill
                
                e_roll = random.randint(1,6) + random.randint(1,6)
                e_attack = e_roll + enemy['skill']

                # Modifiers (e.g. fight with wooden stick -2)
                if "player_attack_modifier" in rules:
                    p_attack += rules["player_attack_modifier"]

                print(f"Round {combat_rounds}: You {p_attack} ({p_roll}) vs Enemy {e_attack} ({e_roll})")
                time.sleep(0.3)

                damage = 2
                if "player_extra_damage_on_hit" in rules:
                    damage += rules["player_extra_damage_on_hit"]
                
                if p_attack > e_attack:
                    print_success("HIT!")
                    if self.game.character.luck > 0:
                        want_luck = input("Test Luck for double damage? (y/n): ").lower()
                        if want_luck == 'y':
                            if self.game.character.test_luck():
                                print_success("LUCKY! Double Damage!")
                                damage *= 2
                            else:
                                print_error("Unlucky. 1 Damage.")
                                damage = 1
                    
                    enemy['stamina'] -= damage
                    print(f"{enemy['name']} HP: {enemy['stamina']}")

                elif e_attack > p_attack:
                    print_error("OUCH!")
                    
                    # Special damage rules (e.g. snakes extra poison)
                    if "enemy_extra_damage" in rules:
                        damage += rules["enemy_extra_damage"]

                    if self.game.character.luck > 0:
                        want_luck = input("Test Luck to reduce damage? (y/n): ").lower()
                        if want_luck == 'y':
                            if self.game.character.test_luck():
                                print_success("LUCKY! 1 Damage taken.")
                                damage = 1
                            else:
                                print_error("Unlucky. +1 Damage taken.")
                                damage += 1
                    
                    self.game.character.take_damage(damage)
                    print(f"Your HP: {self.game.character.stamina}")

                else:
                    print("Clash! No damage.")

        # Determine outcome
        if self.game.character.is_dead():
            self.game.character.current_location = page_data["outcomes"]["lose"]
        
        elif not escaped:
            # Special win condition (Page 73 Troll escape)
            if "escape_after" in rules and "enemy" in rules["escape_after"]:
                # Logic: If we killed the specific enemy, we jump to special page
                # This is complex, for now we treat standard win if all dead
                pass 

            # Check for special time-based win conditions
            if "max_rounds" in rules:
                if combat_rounds <= rules["max_rounds"]:
                    print_success("You defeated him quickly!")
                    self.game.character.current_location = page_data["outcomes"]["win_fast"]
                else:
                    print_warning("The fight took too long...")
                    self.game.character.current_location = page_data["outcomes"]["win_slow"]
            else:
                self.game.character.current_location = page_data["outcomes"]["win"]

    def handle_multi_combat(self, page_data):
        """Simultaneous combat (1 vs 2)."""
        if "text" in page_data:
            self.display(page_data)
        
        print_warning("⚔️  SIMULTANEOUS COMBAT!  ⚔️")
        print_info("You must defend against all enemies, but you can only hurt one per round.")

        enemies = []
        if "enemies" in page_data:
            for eid in page_data["enemies"]:
                 enemies.append(self.game.enemy_data[eid].copy())
        
        combat_round = 0

        while not self.game.character.is_dead() and any(e['stamina'] > 0 for e in enemies):
            combat_round += 1
            print_bold(f"\n--- Round {combat_round} ---")
            
            active_enemies = [e for e in enemies if e['stamina'] > 0]
            
            # Player chooses target
            target = None
            if len(active_enemies) > 1:
                print("Choose your target:")
                for i, e in enumerate(active_enemies, 1):
                    print(f"{i}. {e['name']} (SK: {e['skill']}, ST: {e['stamina']})")
                while not target:
                    try:
                        choice = int(input("> ")) - 1
                        if 0 <= choice < len(active_enemies):
                            target = active_enemies[choice]
                    except ValueError:
                        pass
            else:
                target = active_enemies[0]

            print_info(f"Targeting: {target['name']}")
            time.sleep(0.5)

            # Roll Player
            p_roll = random.randint(1, 6) + random.randint(1, 6)
            p_attack = p_roll + self.game.character.skill
            print(f"You rolled {p_roll} + {self.game.character.skill} Skill = {Fore.CYAN}{p_attack} AS{Style.RESET_ALL}")

            # Process Enemies
            for enemy in active_enemies:
                e_roll = random.randint(1, 6) + random.randint(1, 6)
                e_attack = e_roll + enemy['skill']
                print(f"{enemy['name']} rolled {e_roll} + {enemy['skill']} Skill = {Fore.RED}{e_attack} AS{Style.RESET_ALL}")
                time.sleep(0.3)

                damage = 2
                if enemy == target:
                    if p_attack > e_attack:
                        print_success(f"--> You HIT {enemy['name']}!")
                        enemy['stamina'] -= damage
                    elif e_attack > p_attack:
                        print_error(f"<-- {enemy['name']} HITS YOU!")
                        self.game.character.take_damage(damage)
                    else:
                        print_info("-- Clash.")
                else:
                    if e_attack > p_attack:
                        print_error(f"<-- {enemy['name']} HITS YOU (Flanked)!")
                        self.game.character.take_damage(damage)
                    else:
                        print_info(f"-- You parried {enemy['name']}.")
                
                if self.game.character.is_dead(): break
            
            print(f"Your Stamina: {self.game.character.stamina}")
            time.sleep(1)

        if self.game.character.is_dead():
            self.game.character.current_location = page_data["outcomes"]["lose"]
        else:
            print_success("\nYou have defeated the pair!")
            self.game.character.current_location = page_data["outcomes"]["win"]
        
        input("\nPress Enter...")
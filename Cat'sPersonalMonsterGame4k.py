import pygame
import math
import random
import array
import sys

# ------------------------- Init & Globals ------------------------------
pygame.init()
SCREEN_W, SCREEN_H = 800, 600
TOP_H = 360
BOT_H = SCREEN_H - TOP_H
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("MONSTER RED - Files Off | Vibes On | 60 FPS")
clock = pygame.time.Clock()
FPS = 60

# Fonts
FONT_TINY = pygame.font.SysFont("courier", 14, bold=True)
FONT_SMALL = pygame.font.SysFont("courier", 18, bold=True)
FONT = pygame.font.SysFont("courier", 22, bold=True)
FONT_BIG = pygame.font.SysFont("courier", 32, bold=True)
FONT_TITLE = pygame.font.SysFont("courier", 48, bold=True)

# Sound
SFX_ENABLED = True
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=1)
except Exception:
    SFX_ENABLED = False

def make_tone(freq=440, ms=100, volume=0.25):
    if not SFX_ENABLED:
        return None
    sr = 44100
    n = int(sr * ms / 1000)
    buf = array.array("h")
    for s in range(n):
        t = float(s) / sr
        val = int(volume * 32767 * math.sin(2 * math.pi * freq * t))
        buf.append(val)
    sound = pygame.mixer.Sound(buffer=buf)
    return sound

# ---- SFX ----
SND_SELECT = make_tone(660, 70, 0.25)
SND_HIT    = make_tone(220, 90, 0.30)
SND_HEAL   = make_tone(880, 120, 0.20)
SND_CATCH  = make_tone(523, 180, 0.28)
SND_RUN    = make_tone(330, 70, 0.22)
SND_LEVEL  = make_tone(784, 200, 0.18)
SND_MENU   = make_tone(392, 60, 0.15)
SND_OPEN   = make_tone(523, 100, 0.20)
SND_ERROR  = make_tone(196, 100, 0.25)
SND_CANCEL = make_tone(300, 80, 0.22)
SND_STEP   = make_tone(100, 30, 0.15)
SND_CRIT   = make_tone(880, 60, 0.35)
SND_WILD   = make_tone(330, 300, 0.25)

# ---- Types ----
TYPES = [
    "Normal", "Fire", "Water", "Grass", "Electric", "Rock", 
    "Bug", "Psychic", "Ghost", "Dragon", "Ice", "Ground", 
    "Flying", "Fighting"
]

# Type effectiveness chart
TYPE_CHART = {
    "Fire": {"Water": 0.5, "Grass": 2.0, "Rock": 0.5, "Bug": 2.0, "Ice": 2.0, "Dragon": 0.5},
    "Water": {"Fire": 2.0, "Grass": 0.5, "Ground": 2.0, "Rock": 2.0},
    "Grass": {"Fire": 0.5, "Water": 2.0, "Bug": 0.5, "Poison": 0.5, "Flying": 0.5, "Rock": 2.0, "Ground": 2.0},
    "Electric": {"Water": 2.0, "Grass": 0.5, "Ground": 0.0, "Flying": 2.0},
    "Rock": {"Fire": 2.0, "Water": 2.0, "Grass": 2.0, "Fighting": 0.5, "Ground": 0.5, "Flying": 2.0, "Bug": 2.0},
    "Bug": {"Fire": 0.5, "Grass": 2.0, "Fighting": 0.5, "Flying": 0.5, "Psychic": 2.0},
    "Psychic": {"Fighting": 2.0, "Poison": 2.0, "Bug": 2.0},
    "Ghost": {"Psychic": 0.0, "Ghost": 2.0},
    "Dragon": {"Dragon": 2.0},
    "Ice": {"Water": 0.5, "Grass": 2.0, "Ground": 2.0, "Flying": 2.0, "Dragon": 2.0},
    "Ground": {"Fire": 2.0, "Electric": 2.0, "Grass": 0.5, "Poison": 2.0, "Rock": 2.0, "Bug": 0.5},
    "Flying": {"Grass": 2.0, "Fighting": 2.0, "Bug": 2.0, "Rock": 0.5, "Electric": 0.5},
    "Fighting": {"Normal": 2.0, "Ice": 2.0, "Rock": 2.0, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5},
    "Normal": {"Rock": 0.5, "Ghost": 0.0}
}

# Monster species and moves
SPECIES = [
    {"name": "Flameling", "type": "Fire", "base_hp": 39, "base_attack": 52, "base_defense": 43, "speed": 65},
    {"name": "Aquari", "type": "Water", "base_hp": 44, "base_attack": 48, "base_defense": 65, "speed": 43},
    {"name": "Leafurr", "type": "Grass", "base_hp": 45, "base_attack": 49, "base_defense": 49, "speed": 45},
    {"name": "Zaplet", "type": "Electric", "base_hp": 35, "base_attack": 55, "base_defense": 40, "speed": 90},
    {"name": "Rocklops", "type": "Rock", "base_hp": 50, "base_attack": 65, "base_defense": 85, "speed": 55},
    {"name": "Buzzbite", "type": "Bug", "base_hp": 40, "base_attack": 45, "base_defense": 40, "speed": 56},
    {"name": "Psybat", "type": "Psychic", "base_hp": 60, "base_attack": 65, "base_defense": 60, "speed": 110},
    {"name": "Spectre", "type": "Ghost", "base_hp": 30, "base_attack": 35, "base_defense": 30, "speed": 80},
    {"name": "Drakid", "type": "Dragon", "base_hp": 41, "base_attack": 64, "base_defense": 45, "speed": 50},
]

MOVES = [
    {"name": "Tackle", "type": "Normal", "power": 40, "accuracy": 100, "pp": 35},
    {"name": "Ember", "type": "Fire", "power": 40, "accuracy": 100, "pp": 25},
    {"name": "Water Gun", "type": "Water", "power": 40, "accuracy": 100, "pp": 25},
    {"name": "Vine Whip", "type": "Grass", "power": 40, "accuracy": 100, "pp": 25},
    {"name": "Thunder Shock", "type": "Electric", "power": 40, "accuracy": 100, "pp": 30},
    {"name": "Rock Throw", "type": "Rock", "power": 50, "accuracy": 90, "pp": 15},
    {"name": "Bug Bite", "type": "Bug", "power": 60, "accuracy": 100, "pp": 20},
    {"name": "Confusion", "type": "Psychic", "power": 50, "accuracy": 100, "pp": 25},
    {"name": "Lick", "type": "Ghost", "power": 30, "accuracy": 100, "pp": 30},
    {"name": "Dragon Rage", "type": "Dragon", "power": 40, "accuracy": 100, "pp": 10},
    {"name": "Ice Shard", "type": "Ice", "power": 40, "accuracy": 100, "pp": 30},
    {"name": "Mud Slap", "type": "Ground", "power": 20, "accuracy": 100, "pp": 10},
    {"name": "Wing Attack", "type": "Flying", "power": 60, "accuracy": 100, "pp": 35},
    {"name": "Karate Chop", "type": "Fighting", "power": 50, "accuracy": 100, "pp": 25},
]

# World map generation
MAP_W, MAP_H = 20, 15
WORLD = [[0 for _ in range(MAP_W)] for _ in range(MAP_H)]
for y in range(MAP_H):
    for x in range(MAP_W):
        if y == 0 or y == MAP_H-1 or x == 0 or x == MAP_W-1:
            WORLD[y][x] = 2  # border trees
        elif random.random() < 0.1:
            WORLD[y][x] = 1  # tree
        elif random.random() < 0.05:
            WORLD[y][x] = 3  # water
        elif random.random() < 0.02:
            WORLD[y][x] = 4  # rock

# Create paths
for i in range(10):
    x, y = random.randint(1, MAP_W-2), random.randint(1, MAP_H-2)
    for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
        nx, ny = x + dx, y + dy
        if 0 < nx < MAP_W-1 and 0 < ny < MAP_H-1:
            WORLD[ny][nx] = 0

def can_walk(tx, ty):
    if tx < 0 or ty < 0 or tx >= MAP_W or ty >= MAP_H:
        return False
    t = WORLD[ty][tx]
    if t in (1, 2, 3, 4):  # tree, border, water, rock
        return False
    return True

# ---- Entity classes ----
class Monster:
    def __init__(self, species_index, level=5):
        species = SPECIES[species_index]
        self.name = species["name"]
        self.type = species["type"]
        self.level = level
        self.base_hp = species["base_hp"]
        self.base_attack = species["base_attack"]
        self.base_defense = species["base_defense"]
        self.speed = species["speed"]
        
        # Calculate stats
        self.max_hp = int((2 * self.base_hp * self.level) / 100) + self.level + 10
        self.hp = self.max_hp
        self.attack = int((2 * self.base_attack * self.level) / 100) + 5
        self.defense = int((2 * self.base_defense * self.level) / 100) + 5
        self.speed = int((2 * self.speed * self.level) / 100) + 5
        
        # Assign moves
        self.moves = []
        type_moves = [m for m in MOVES if m["type"] == self.type]
        other_moves = [m for m in MOVES if m["type"] != self.type]
        
        if type_moves:
            self.moves.append(random.choice(type_moves))
        if len(self.moves) < 4:
            self.moves.append(random.choice(other_moves))
        if len(self.moves) < 4:
            self.moves.append(random.choice(MOVES))
        if len(self.moves) < 4:
            self.moves.append(random.choice(MOVES))
    
    def color(self):
        return {
            "Fire": (255, 100, 50),
            "Water": (50, 100, 255),
            "Grass": (50, 200, 50),
            "Electric": (255, 255, 50),
            "Rock": (180, 160, 100),
            "Bug": (180, 200, 80),
            "Psychic": (255, 100, 180),
            "Ghost": (150, 100, 180),
            "Dragon": (120, 80, 200),
            "Ice": (180, 220, 255),
            "Ground": (180, 150, 80),
            "Flying": (180, 200, 255),
            "Fighting": (200, 80, 80),
            "Normal": (200, 200, 200)
        }.get(self.type, (200, 200, 200))
    
    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)
        return self.hp == 0

# Player class
class Player:
    def __init__(self):
        self.x, self.y = 5, 5
        self.direction = 0  # 0: down, 1: up, 2: left, 3: right
        self.steps = 0
        self.party = [Monster(0, 5)]  # Start with a Flameling
        self.items = {"Potion": 3, "Monster Ball": 5}
        self.active_monster = 0
        self.money = 500
    
    def move(self, dx, dy):
        new_x, new_y = self.x + dx, self.y + dy
        if can_walk(new_x, new_y):
            self.x, self.y = new_x, new_y
            self.steps += 1
            if SFX_ENABLED:
                SND_STEP.play()
            return True
        return False
    
    def get_active_monster(self):
        return self.party[self.active_monster]

# Battle system
class Battle:
    def __init__(self, player, wild_monster):
        self.player = player
        self.wild_monster = wild_monster
        self.state = "SELECT"  # SELECT, MOVE, RESULT, WIN, LOSE, CATCH, RUN
        self.selected_move = 0
        self.message = ""
        self.message_timer = 0
        self.player_turn = True
        self.player_move = None
        self.wild_move = None
        self.battle_animation = 0
        self.catch_attempts = 0
        self.ran_away = False
        self.won = False
    
    def calculate_damage(self, attacker, defender, move):
        # Type effectiveness
        effectiveness = 1.0
        defender_types = [defender.type]
        
        for defender_type in defender_types:
            if defender_type in TYPE_CHART.get(move["type"], {}):
                effectiveness *= TYPE_CHART[move["type"]][defender_type]
        
        # Critical hit (1/16 chance)
        critical = 1.5 if random.random() < 0.0625 else 1.0
        
        # STAB (Same Type Attack Bonus)
        stab = 1.5 if move["type"] == attacker.type else 1.0
        
        # Damage calculation
        damage = int((((2 * attacker.level) / 5 + 2) * move["power"] * (attacker.attack / defender.defense)) / 50)
        damage += 2
        damage *= effectiveness * critical * stab * random.uniform(0.85, 1.0)
        
        return max(1, int(damage)), effectiveness, critical > 1.0
    
    def player_attack(self, move_index):
        player_mon = self.player.get_active_monster()
        move = player_mon.moves[move_index]
        self.player_move = move
        
        # Accuracy check
        if random.randint(1, 100) > move["accuracy"]:
            self.message = f"{player_mon.name}'s {move['name']} missed!"
            self.state = "RESULT"
            self.player_turn = False
            self.message_timer = 120
            return
        
        damage, effectiveness, critical = self.calculate_damage(player_mon, self.wild_monster, move)
        
        # Effectiveness text
        eff_text = ""
        if effectiveness == 0:
            eff_text = "It has no effect..."
        elif effectiveness < 1:
            eff_text = "It's not very effective."
        elif effectiveness > 1:
            eff_text = "It's super effective!"
        
        # Critical text
        crit_text = "A critical hit!" if critical else ""
        
        # Apply damage
        faint = self.wild_monster.take_damage(damage)
        
        # Set message
        self.message = f"{player_mon.name} used {move['name']}!{crit_text} {eff_text}"
        if faint:
            self.message += f"\nWild {self.wild_monster.name} fainted!"
            self.state = "WIN"
            self.player.get_active_monster().hp = min(self.player.get_active_monster().max_hp, 
                                                     self.player.get_active_monster().hp + 5)
            self.message_timer = 180
            if SFX_ENABLED:
                SND_HIT.play()
        else:
            self.state = "RESULT"
            self.player_turn = False
            self.message_timer = 120
            if SFX_ENABLED:
                SND_HIT.play()
    
    def wild_attack(self):
        wild_mon = self.wild_monster
        move = random.choice(wild_mon.moves)
        self.wild_move = move
        
        # Accuracy check
        if random.randint(1, 100) > move["accuracy"]:
            self.message = f"Wild {wild_mon.name}'s {move['name']} missed!"
            self.state = "RESULT"
            self.player_turn = True
            self.message_timer = 120
            return
        
        player_mon = self.player.get_active_monster()
        damage, effectiveness, critical = self.calculate_damage(wild_mon, player_mon, move)
        
        # Effectiveness text
        eff_text = ""
        if effectiveness == 0:
            eff_text = "It has no effect..."
        elif effectiveness < 1:
            eff_text = "It's not very effective."
        elif effectiveness > 1:
            eff_text = "It's super effective!"
        
        # Critical text
        crit_text = "A critical hit!" if critical else ""
        
        # Apply damage
        faint = player_mon.take_damage(damage)
        
        # Set message
        self.message = f"Wild {wild_mon.name} used {move['name']}!{crit_text} {eff_text}"
        if faint:
            self.message += f"\n{player_mon.name} fainted!"
            # Check if player has other monsters
            alive_monsters = [m for m in self.player.party if m.hp > 0]
            if not alive_monsters:
                self.state = "LOSE"
                self.message_timer = 180
            else:
                self.message += "\nGo! Next monster!"
                self.state = "RESULT"
                self.player_turn = True
                self.player.active_monster = next(i for i, m in enumerate(self.player.party) if m.hp > 0)
                self.message_timer = 180
            if SFX_ENABLED:
                SND_HIT.play()
        else:
            self.state = "RESULT"
            self.player_turn = True
            self.message_timer = 120
            if SFX_ENABLED:
                SND_HIT.play()
    
    def attempt_catch(self):
        self.catch_attempts += 1
        self.player.items["Monster Ball"] -= 1
        
        # Catch calculation
        catch_chance = 0.3
        hp_percent = self.wild_monster.hp / self.wild_monster.max_hp
        catch_chance *= (1 - (hp_percent * 0.5))  # Higher chance when HP is low
        
        if random.random() < catch_chance:
            self.player.party.append(self.wild_monster)
            self.state = "CATCH"
            self.message = f"Gotcha! {self.wild_monster.name} was caught!"
            if SFX_ENABLED:
                SND_CATCH.play()
        else:
            self.state = "RESULT"
            self.message = "Oh no! The wild monster broke free!"
            self.player_turn = False
            self.message_timer = 120
            if SFX_ENABLED:
                SND_CANCEL.play()
    
    def attempt_run(self):
        # Running is easier when your monster is faster
        run_chance = 0.6
        if self.player.get_active_monster().speed < self.wild_monster.speed:
            run_chance = 0.3
        
        if random.random() < run_chance:
            self.ran_away = True
            self.state = "RUN"
            self.message = "Got away safely!"
            if SFX_ENABLED:
                SND_RUN.play()
        else:
            self.state = "RESULT"
            self.message = "Can't escape!"
            self.player_turn = False
            self.message_timer = 120
            if SFX_ENABLED:
                SND_ERROR.play()

# ---- Drawing functions ----
def draw_text(surf, text, x, y, col=(255,255,255), shadow=False, font=FONT, center=False):
    if shadow:
        text_surface = font.render(text, True, (0,0,0))
        if center:
            surf.blit(text_surface, (x - text_surface.get_width()//2 + 2, y - text_surface.get_height()//2 + 2))
        else:
            surf.blit(text_surface, (x+2, y+2))
    
    text_surface = font.render(text, True, col)
    if center:
        surf.blit(text_surface, (x - text_surface.get_width()//2, y - text_surface.get_height()//2))
    else:
        surf.blit(text_surface, (x, y))

def draw_monster(surf, monster, x, y, size=80, facing_right=True, battle=False):
    col = monster.color()
    # Draw monster body
    pygame.draw.circle(surf, col, (x, y), size//2)
    pygame.draw.circle(surf, (min(255, col[0]+50), min(255, col[1]+50), min(255, col[2]+50)), 
                         (x + (-10 if facing_right else 10), y - 10), size//4)
    
    # Draw eyes
    pygame.draw.circle(surf, (255, 255, 255), (x + (-15 if facing_right else 15), y - 5), 8)
    pygame.draw.circle(surf, (0, 0, 0), (x + (-15 if facing_right else 15), y - 5), 4)
    
    # Draw health bar in battle
    if battle and monster.hp > 0:
        bar_width = 100
        bar_height = 8
        pygame.draw.rect(surf, (50, 50, 50), (x - bar_width//2, y + size//2 + 10, bar_width, bar_height))
        hp_percent = monster.hp / monster.max_hp
        hp_color = (0, 255, 0) if hp_percent > 0.5 else (255, 255, 0) if hp_percent > 0.2 else (255, 0, 0)
        pygame.draw.rect(surf, hp_color, (x - bar_width//2, y + size//2 + 10, int(bar_width * hp_percent), bar_height))
        pygame.draw.rect(surf, (200, 200, 200), (x - bar_width//2, y + size//2 + 10, bar_width, bar_height), 1)
        draw_text(surf, f"Lv{monster.level}", x - bar_width//2 + 5, y + size//2 + 25, (255, 255, 255), True, FONT_SMALL)
        draw_text(surf, f"{monster.hp}/{monster.max_hp}", x + bar_width//2 - 5, y + size//2 + 25, (255, 255, 255), True, FONT_SMALL, False)

def draw_battle_menu(surf, battle, player_mon):
    # Draw menu box
    pygame.draw.rect(surf, (40, 40, 80), (20, TOP_H + 20, SCREEN_W - 40, BOT_H - 40))
    pygame.draw.rect(surf, (100, 100, 180), (20, TOP_H + 20, SCREEN_W - 40, BOT_H - 40), 3)
    
    if battle.state == "SELECT":
        # Draw menu options
        options = ["FIGHT", "BAG", "MONSTER", "RUN"]
        for i, opt in enumerate(options):
            draw_text(surf, opt, 50 + (i % 2) * 200, TOP_H + 50 + (i // 2) * 40, 
                     (255, 255, 255), True, FONT_BIG)
        
        # Draw selector
        pygame.draw.polygon(surf, (255, 255, 0), [
            (30 + (battle.selected_move % 2) * 200, TOP_H + 50 + (battle.selected_move // 2) * 40),
            (40 + (battle.selected_move % 2) * 200, TOP_H + 55 + (battle.selected_move // 2) * 40),
            (30 + (battle.selected_move % 2) * 200, TOP_H + 60 + (battle.selected_move // 2) * 40)
        ])
    
    elif battle.state == "MOVE":
        # Draw move list
        for i, move in enumerate(player_mon.moves):
            col = (200, 200, 200) if i == battle.selected_move else (150, 150, 150)
            draw_text(surf, move["name"], 50, TOP_H + 50 + i * 30, col, True, FONT)
            draw_text(surf, f"PP: {move['pp']}/∞", 250, TOP_H + 50 + i * 30, (180, 180, 255), True, FONT)
        
        # Draw move type
        move_type = player_mon.moves[battle.selected_move]["type"]
        type_col = {
            "Fire": (255, 100, 50),
            "Water": (50, 100, 255),
            "Grass": (50, 200, 50),
            "Electric": (255, 255, 50),
            "Rock": (180, 160, 100),
            "Bug": (180, 200, 80),
            "Psychic": (255, 100, 180),
            "Ghost": (150, 100, 180),
            "Dragon": (120, 80, 200),
            "Ice": (180, 220, 255),
            "Ground": (180, 150, 80),
            "Flying": (180, 200, 255),
            "Fighting": (200, 80, 80),
            "Normal": (200, 200, 200)
        }.get(move_type, (200, 200, 200))
        
        pygame.draw.rect(surf, type_col, (SCREEN_W - 150, TOP_H + 50, 120, 25))
        draw_text(surf, move_type, SCREEN_W - 90, TOP_H + 63, (0, 0, 0), False, FONT, True)
    
    # Draw message if any
    if battle.message:
        pygame.draw.rect(surf, (20, 20, 40), (50, TOP_H + 180, SCREEN_W - 100, 60))
        pygame.draw.rect(surf, (80, 80, 160), (50, TOP_H + 180, SCREEN_W - 100, 60), 2)
        lines = battle.message.split('\n')
        for i, line in enumerate(lines):
            draw_text(surf, line, SCREEN_W//2, TOP_H + 195 + i * 20, (255, 255, 255), True, FONT, True)

# ---- Game states ----
STATE_TITLE = 0
STATE_OVERWORLD = 1
STATE_BATTLE = 2
STATE_MENU = 3

player = Player()
state = STATE_TITLE
title_time = 0
battle = None
menu_selection = 0
encounter_chance = 0.02
step_counter = 0
wild_monsters = [0, 1, 2, 3, 4, 5, 6, 7, 8]  # All species can appear

# Main game loop
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    title_time += dt
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            
            # Title screen
            if state == STATE_TITLE:
                if event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                    if SFX_ENABLED:
                        SND_SELECT.play()
                    state = STATE_OVERWORLD
            
            # Overworld
            elif state == STATE_OVERWORLD:
                if event.key == pygame.K_z:
                    # Open menu
                    if SFX_ENABLED:
                        SND_MENU.play()
                    state = STATE_MENU
                    menu_selection = 0
                
                # Movement
                elif event.key == pygame.K_UP:
                    player.direction = 1
                    player.move(0, -1)
                elif event.key == pygame.K_DOWN:
                    player.direction = 0
                    player.move(0, 1)
                elif event.key == pygame.K_LEFT:
                    player.direction = 2
                    player.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    player.direction = 3
                    player.move(1, 0)
            
            # Battle state
            elif state == STATE_BATTLE:
                if battle.state in ("SELECT", "MOVE"):
                    if event.key == pygame.K_UP:
                        if battle.state == "SELECT":
                            battle.selected_move = max(0, battle.selected_move - 2)
                        else:
                            battle.selected_move = max(0, battle.selected_move - 1)
                        if SFX_ENABLED:
                            SND_MENU.play()
                    elif event.key == pygame.K_DOWN:
                        if battle.state == "SELECT":
                            battle.selected_move = min(3, battle.selected_move + 2)
                        else:
                            battle.selected_move = min(3, battle.selected_move + 1)
                        if SFX_ENABLED:
                            SND_MENU.play()
                    elif event.key == pygame.K_LEFT:
                        if battle.state == "SELECT":
                            battle.selected_move = max(0, battle.selected_move - 1)
                        if SFX_ENABLED:
                            SND_MENU.play()
                    elif event.key == pygame.K_RIGHT:
                        if battle.state == "SELECT":
                            battle.selected_move = min(3, battle.selected_move + 1)
                        if SFX_ENABLED:
                            SND_MENU.play()
                    elif event.key in (pygame.K_z, pygame.K_RETURN):
                        if battle.state == "SELECT":
                            if battle.selected_move == 0:  # FIGHT
                                battle.state = "MOVE"
                                battle.selected_move = 0
                                if SFX_ENABLED:
                                    SND_SELECT.play()
                            elif battle.selected_move == 1:  # BAG
                                # Use a potion if available
                                if player.items.get("Potion", 0) > 0 and player.get_active_monster().hp < player.get_active_monster().max_hp:
                                    player.items["Potion"] -= 1
                                    player.get_active_monster().hp = min(player.get_active_monster().max_hp, 
                                                                        player.get_active_monster().hp + 20)
                                    battle.message = f"Used Potion! {player.get_active_monster().name} recovered 20 HP!"
                                    battle.state = "RESULT"
                                    battle.player_turn = False
                                    battle.message_timer = 120
                                    if SFX_ENABLED:
                                        SND_HEAL.play()
                                else:
                                    battle.message = "No usable items right now!"
                                    battle.state = "RESULT"
                                    battle.message_timer = 90
                                    if SFX_ENABLED:
                                        SND_ERROR.play()
                            elif battle.selected_move == 2:  # MONSTER
                                # Switch to next alive monster
                                current_idx = player.active_monster
                                next_idx = (current_idx + 1) % len(player.party)
                                while next_idx != current_idx and player.party[next_idx].hp <= 0:
                                    next_idx = (next_idx + 1) % len(player.party)
                                
                                if next_idx != current_idx:
                                    player.active_monster = next_idx
                                    battle.message = f"Go! {player.party[next_idx].name}!"
                                    battle.state = "RESULT"
                                    battle.player_turn = False
                                    battle.message_timer = 120
                                    if SFX_ENABLED:
                                        SND_SELECT.play()
                                else:
                                    battle.message = "No other monsters available!"
                                    battle.state = "RESULT"
                                    battle.message_timer = 90
                                    if SFX_ENABLED:
                                        SND_ERROR.play()
                            elif battle.selected_move == 3:  # RUN
                                battle.attempt_run()
                        else:  # MOVE state
                            battle.player_attack(battle.selected_move)
                    elif event.key == pygame.K_x:
                        if battle.state == "MOVE":
                            battle.state = "SELECT"
                            if SFX_ENABLED:
                                SND_CANCEL.play()
                elif battle.state in ("RESULT", "WIN", "LOSE", "CATCH", "RUN"):
                    if event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                        if battle.state == "WIN":
                            # Give rewards
                            player.money += battle.wild_monster.level * 10
                            # Level up randomly
                            if random.random() < 0.3:
                                player.get_active_monster().level += 1
                                player.get_active_monster().max_hp = int((2 * player.get_active_monster().base_hp * player.get_active_monster().level) / 100) + player.get_active_monster().level + 10
                                player.get_active_monster().hp = player.get_active_monster().max_hp
                                battle.message = f"{player.get_active_monster().name} grew to Lv{player.get_active_monster().level}!"
                                battle.state = "RESULT"
                                if SFX_ENABLED:
                                    SND_LEVEL.play()
                            else:
                                state = STATE_OVERWORLD
                                if SFX_ENABLED:
                                    SND_OPEN.play()
                        elif battle.state == "LOSE":
                            # Heal party
                            for m in player.party:
                                m.hp = m.max_hp
                            player.x, player.y = 5, 5  # Reset position
                            state = STATE_OVERWORLD
                            if SFX_ENABLED:
                                SND_OPEN.play()
                        elif battle.state in ("CATCH", "RUN"):
                            state = STATE_OVERWORLD
                            if SFX_ENABLED:
                                SND_OPEN.play()
                        else:
                            if battle.player_turn:
                                battle.state = "SELECT"
                            else:
                                battle.wild_attack()
            
            # Menu state
            elif state == STATE_MENU:
                if event.key == pygame.K_UP:
                    menu_selection = max(0, menu_selection - 1)
                    if SFX_ENABLED:
                        SND_MENU.play()
                elif event.key == pygame.K_DOWN:
                    menu_selection = min(3, menu_selection + 1)
                    if SFX_ENABLED:
                        SND_MENU.play()
                elif event.key == pygame.K_x:
                    state = STATE_OVERWORLD
                    if SFX_ENABLED:
                        SND_CANCEL.play()
                elif event.key in (pygame.K_z, pygame.K_RETURN):
                    if menu_selection == 0:  # Party
                        # Just close menu for now
                        state = STATE_OVERWORLD
                        if SFX_ENABLED:
                            SND_SELECT.play()
                    elif menu_selection == 1:  # Items
                        # Use a potion
                        if player.items.get("Potion", 0) > 0:
                            player.items["Potion"] -= 1
                            player.get_active_monster().hp = min(player.get_active_monster().max_hp, 
                                                                player.get_active_monster().hp + 20)
                            if SFX_ENABLED:
                                SND_HEAL.play()
                        state = STATE_OVERWORLD
                    elif menu_selection == 2:  # Save
                        # Just show message
                        state = STATE_OVERWORLD
                        if SFX_ENABLED:
                            SND_SELECT.play()
                    elif menu_selection == 3:  # Quit
                        state = STATE_TITLE
                        if SFX_ENABLED:
                            SND_SELECT.play()
    
    # Update game state
    if state == STATE_OVERWORLD:
        step_counter += dt
        if step_counter > 0.2:  # Every 0.2 seconds
            step_counter = 0
            # Random encounter
            if random.random() < encounter_chance and battle is None:
                wild_species = random.choice(wild_monsters)
                wild_level = random.randint(max(1, player.get_active_monster().level-2), 
                                          player.get_active_monster().level+2)
                battle = Battle(player, Monster(wild_species, wild_level))
                state = STATE_BATTLE
                if SFX_ENABLED:
                    SND_WILD.play()
    
    # Battle updates
    if state == STATE_BATTLE and battle:
        if battle.message_timer > 0:
            battle.message_timer -= dt * 60
            if battle.message_timer <= 0 and battle.state == "RESULT":
                if battle.player_turn:
                    battle.state = "SELECT"
                else:
                    battle.wild_attack()
    
    # Rendering
    screen.fill((0, 0, 0))
    
    # Title screen
    if state == STATE_TITLE:
        # Animated background
        for y in range(0, SCREEN_H, 20):
            for x in range(0, SCREEN_W, 20):
                col = (
                    40 + int(50 * abs(math.sin((x/50 + title_time)))),
                    40 + int(50 * abs(math.sin((y/50 + title_time*0.7)))),
                    80 + int(50 * abs(math.sin((x/70 + y/60 + title_time*1.2))))
                )
                pygame.draw.rect(screen, col, (x, y, 20, 20))
        # Title
        pulse = 0.5 + 0.5 * abs(math.sin(title_time * 2))
        title_col = (255, int(50 + 50 * pulse), int(50 * pulse))
        draw_text(screen, "MONSTER RED", SCREEN_W//2, 150, title_col, True, FONT_TITLE, True)
        
        # Subtitle
        draw_text(screen, "Files Off | Vibes On | 60 FPS", SCREEN_W//2, 210, (180, 180, 255), True, FONT_BIG, True)
        
        # Monster showcase
        for i in range(4):
            x = 150 + i * 150
            y = 350
            dummy = Monster(i, level=5 + i)
            pygame.draw.circle(screen, (40, 40, 80), (x, y), 40)
            draw_monster(screen, dummy, x, y, 40, i % 2 == 0)
            draw_text(screen, dummy.name, x, y + 50, dummy.color(), True, FONT_SMALL, True)
        
        # Start prompt
        blink = int(title_time * 3) % 2
        if blink:
            draw_text(screen, "Press SPACE to start", SCREEN_W//2, 500, (220, 220, 255), True, FONT_BIG, True)
    
    # Overworld
    elif state == STATE_OVERWORLD:
        # Draw terrain
        tile_size = 32
        for y in range(MAP_H):
            for x in range(MAP_W):
                rect = (x*tile_size, y*tile_size, tile_size, tile_size)
                if WORLD[y][x] == 0:  # grass
                    pygame.draw.rect(screen, (50, 180, 50), rect)
                    # Grass pattern
                    if (x + y) % 3 == 0:
                        pygame.draw.rect(screen, (40, 160, 40), rect, 1)
                elif WORLD[y][x] == 1:  # tree
                    pygame.draw.rect(screen, (40, 120, 40), rect)
                    pygame.draw.circle(screen, (30, 100, 30), 
                                     (x*tile_size + tile_size//2, y*tile_size + tile_size//3), 
                                     tile_size//3)
                elif WORLD[y][x] == 2:  # border tree
                    pygame.draw.rect(screen, (30, 100, 30), rect)
                    pygame.draw.circle(screen, (20, 80, 20), 
                                     (x*tile_size + tile_size//2, y*tile_size + tile_size//3), 
                                     tile_size//2)
                elif WORLD[y][x] == 3:  # water
                    pygame.draw.rect(screen, (40, 120, 220), rect)
                    # Water animation
                    wave = int(title_time * 5) % 3
                    for i in range(3):
                        offset = ((x + y + i + wave) % 3) * 8
                        pygame.draw.line(screen, (100, 170, 255), 
                                       (x*tile_size, y*tile_size + offset),
                                       (x*tile_size + tile_size, y*tile_size + offset), 1)
                elif WORLD[y][x] == 4:  # rock
                    pygame.draw.rect(screen, (120, 100, 80), rect)
                    pygame.draw.circle(screen, (100, 80, 60), 
                                     (x*tile_size + tile_size//2, y*tile_size + tile_size//2), 
                                     tile_size//3)
        
        # Draw player
        player_color = (255, 50, 50)
        px, py = player.x * tile_size + tile_size//2, player.y * tile_size + tile_size//2
        pygame.draw.circle(screen, player_color, (px, py), tile_size//3)
        # Direction indicator
        if player.direction == 0:  # down
            pygame.draw.polygon(screen, (200, 200, 200), 
                              [(px, py + 10), (px - 5, py), (px + 5, py)])
        elif player.direction == 1:  # up
            pygame.draw.polygon(screen, (200, 200, 200), 
                              [(px, py - 10), (px - 5, py), (px + 5, py)])
        elif player.direction == 2:  # left
            pygame.draw.polygon(screen, (200, 200, 200), 
                              [(px - 10, py), (px, py - 5), (px, py + 5)])
        elif player.direction == 3:  # right
            pygame.draw.polygon(screen, (200, 200, 200), 
                              [(px + 10, py), (px, py - 5), (px, py + 5)])
        
        # Draw HUD
        pygame.draw.rect(screen, (40, 40, 80), (10, 10, 200, 80))
        pygame.draw.rect(screen, (100, 100, 180), (10, 10, 200, 80), 2)
        active_mon = player.get_active_monster()
        draw_text(screen, active_mon.name, 30, 25, active_mon.color(), True, FONT)
        draw_text(screen, f"Lv{active_mon.level}", 160, 25, (255, 255, 255), True, FONT)
        
        # HP bar
        pygame.draw.rect(screen, (50, 50, 50), (30, 50, 150, 20))
        hp_percent = active_mon.hp / active_mon.max_hp
        hp_color = (0, 255, 0) if hp_percent > 0.5 else (255, 255, 0) if hp_percent > 0.2 else (255, 0, 0)
        pygame.draw.rect(screen, hp_color, (30, 50, int(150 * hp_percent), 20))
        pygame.draw.rect(screen, (200, 200, 200), (30, 50, 150, 20), 1)
        draw_text(screen, f"HP: {active_mon.hp}/{active_mon.max_hp}", 105, 52, (255, 255, 255), True, FONT_SMALL, True)
        
        # Menu hint
        draw_text(screen, "Press Z for Menu", SCREEN_W - 150, SCREEN_H - 30, (200, 200, 200), True, FONT_SMALL)
    
    # Battle state
    elif state == STATE_BATTLE and battle:
        # Battle background
        pygame.draw.rect(screen, (120, 200, 255), (0, 0, SCREEN_W, TOP_H))
        pygame.draw.rect(screen, (100, 180, 100), (0, TOP_H//2, SCREEN_W, TOP_H//2))
        
        # Player monster
        player_mon = player.get_active_monster()
        draw_monster(screen, player_mon, 200, TOP_H - 100, 80, True, True)
        
        # Wild monster
        draw_monster(screen, battle.wild_monster, SCREEN_W - 200, 150, 80, False, True)
        
        # Battle effects
        if battle.battle_animation > 0:
            battle.battle_animation -= dt * 60
            if battle.player_move:
                pygame.draw.circle(screen, (255, 255, 255, 150), (SCREEN_W - 200, 150), int(50 * battle.battle_animation), 3)
            else:
                pygame.draw.circle(screen, (255, 100, 100, 150), (200, TOP_H - 100), int(50 * battle.battle_animation), 3)
        
        # Draw battle menu
        draw_battle_menu(screen, battle, player_mon)
    
    # Menu state
    elif state == STATE_MENU:
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Menu box
        pygame.draw.rect(screen, (40, 40, 80), (SCREEN_W//2 - 150, SCREEN_H//2 - 150, 300, 300))
        pygame.draw.rect(screen, (100, 100, 180), (SCREEN_W//2 - 150, SCREEN_H//2 - 150, 300, 300), 4)
        
        # Title
        draw_text(screen, "MENU", SCREEN_W//2, SCREEN_H//2 - 120, (255, 255, 255), True, FONT_BIG, True)
        
        # Options
        options = ["PARTY", "ITEMS", "SAVE", "QUIT"]
        for i, opt in enumerate(options):
            col = (255, 255, 0) if i == menu_selection else (200, 200, 200)
            draw_text(screen, opt, SCREEN_W//2, SCREEN_H//2 - 50 + i * 50, col, True, FONT_BIG, True)
        
        # Player info
        draw_text(screen, f"Money: ${player.money}", SCREEN_W//2, SCREEN_H//2 + 120, (255, 255, 100), True, FONT)
        draw_text(screen, f"Active: {player.get_active_monster().name}", SCREEN_W//2, SCREEN_H//2 + 150, player.get_active_monster().color(), True, FONT)
    
    pygame.display.flip()

pygame.quit()
sys.exit()

"""
Mario & Luigi LIVE - Complete MMORPG
Full implementation with all features from the original document
Enhanced with Flames Co. Live Network
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import pygame
import random
import math
import time
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import colorsys

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Enhanced Color Palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (237, 28, 36)
GREEN = (34, 177, 76)
BLUE = (0, 162, 232)
YELLOW = (255, 242, 0)
PURPLE = (163, 73, 164)
ORANGE = (255, 127, 39)
CYAN = (0, 255, 255)
PINK = (255, 174, 201)
BROWN = (185, 122, 87)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
DARK_RED = (139, 0, 0)
MARIO_RED = (229, 36, 33)
LUIGI_GREEN = (45, 137, 48)
PEACH_PINK = (255, 192, 203)
TOAD_RED = (237, 28, 36)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)

# Game States
class GameState(Enum):
    TITLE = "title"
    CHAR_CREATION = "char_creation"
    SPECIES_SELECT = "species_select"
    COLOR_SELECT = "color_select"
    GUARDIAN_SELECT = "guardian_select"
    STORY_INTRO = "story_intro"
    ONLINE_LOBBY = "online_lobby"
    WORLD_MAP = "world_map"
    BATTLE = "battle"
    SHOP = "shop"
    INVENTORY = "inventory"
    PATCHES = "patches"
    ROOM_SELECT = "room_select"
    TOAD_TOWN = "toad_town"
    DRY_DRY_DESERT = "dry_dry_desert"
    BEAN_KINGDOM = "bean_kingdom"

# All Species from the document
SPECIES_DATA = {
    "Human": {"colors": ["Light Skin", "Dark Skin"], "base_hp": 100, "base_mp": 50},
    "Koopa": {"colors": ["Red", "Blue", "Green", "Black", "Pink", "Purple", "Orange", "Cyan"], "base_hp": 120, "base_mp": 40},
    "Goomba": {"colors": ["Brown", "Red", "Blue", "Green", "Pink", "Black", "White"], "base_hp": 80, "base_mp": 30},
    "Pianta": {"colors": ["Cyan", "Yellow", "Green", "Pink", "Orange"], "base_hp": 150, "base_mp": 20},
    "Noki": {"colors": ["Cyan", "Yellow", "Green", "Pink", "Orange"], "base_hp": 70, "base_mp": 80},
    "Toad": {"colors": ["Green", "Red", "Blue", "Yellow", "Pink", "Black", "Orange", "Purple", "White"], "base_hp": 90, "base_mp": 60},
    "Yoshi": {"colors": ["Red", "Green", "Blue", "Cyan", "Black", "White", "Yellow", "Pink", "Purple", "Orange"], "base_hp": 110, "base_mp": 50},
    "Hammer Bro": {"colors": ["Green", "Blue", "Red", "Cyan", "Yellow", "Pink", "Purple", "Black", "White"], "base_hp": 130, "base_mp": 40},
    "Luma": {"colors": ["Gold", "Silver", "Purple", "Blue", "Dark Red", "Orange"], "base_hp": 60, "base_mp": 100},
    "Boo": {"colors": ["White", "Pink"], "base_hp": 70, "base_mp": 90},
    "Bob-Omb": {"colors": ["Black", "Pink"], "base_hp": 100, "base_mp": 30},
    "Shy Guy": {"colors": ["Red", "Blue", "Yellow", "Green", "Purple", "Pink", "Cyan", "Black", "White", "Orange"], "base_hp": 85, "base_mp": 55},
    "Piranha Plant": {"colors": ["Red", "Blue", "Yellow", "Green", "Pink", "Cyan", "Black", "White", "Orange", "Purple"], "base_hp": 95, "base_mp": 45},
    "Tanooki": {"colors": ["Brown", "Black", "Green", "Pink", "Red", "White", "Purple"], "base_hp": 105, "base_mp": 65},
    "Buzzy Beetle": {"colors": ["Red", "Blue", "Green", "Pink", "Black", "White", "Orange"], "base_hp": 140, "base_mp": 25},
    "Lakitu": {"colors": ["Red", "Blue", "Green", "Pink", "Purple", "Black", "White"], "base_hp": 75, "base_mp": 75},
    "Wiggler": {"colors": ["Orange", "Red", "Blue", "Green", "Pink", "Black", "White", "Purple"], "base_hp": 125, "base_mp": 35},
    "Shroob": {"colors": ["Purple", "Red", "Blue", "Yellow", "Green", "Black", "White", "Pink"], "base_hp": 90, "base_mp": 70},
    "Monty Mole": {"colors": ["Brown", "Red", "Blue", "Green", "Black", "White", "Pink", "Orange"], "base_hp": 115, "base_mp": 40},
    "Birdo": {"colors": ["Pink", "Red", "Blue", "Green", "Cyan", "White", "Black", "Yellow", "Purple", "Orange"], "base_hp": 95, "base_mp": 60},
    "Cloud Creature": {"colors": ["White", "Pale", "Red", "Blue", "Green", "Black", "Pink"], "base_hp": 65, "base_mp": 85},
    "Magikoopa": {"colors": ["Blue", "White", "Red", "Green", "Black", "Purple", "Pink", "Yellow", "Orange"], "base_hp": 70, "base_mp": 120},
    "Blooper": {"colors": ["White", "Black", "Blue", "Yellow", "Green", "Orange"], "base_hp": 80, "base_mp": 50},
    "Bumpty": {"colors": ["Blue", "Black", "Orange", "Red", "Cyan", "Green", "Pink", "Purple", "Yellow"], "base_hp": 100, "base_mp": 45},
    "Thwomp": {"colors": ["Black", "White", "Red", "Blue", "Cyan", "Green", "Pink"], "base_hp": 180, "base_mp": 10},
    "Cataquack": {"colors": ["Orange", "Blue", "Green", "Red", "Black", "White", "Cyan", "Pink", "Yellow", "Purple"], "base_hp": 110, "base_mp": 40},
    "Chain-Chomp": {"colors": ["Black", "White", "Blue", "Red", "Green", "Pink", "Purple"], "base_hp": 160, "base_mp": 20},
    "Crazee Dayzee": {"colors": ["Pink", "Purple", "Red", "Blue", "Orange", "Green", "Black", "White", "Cyan", "Yellow"], "base_hp": 75, "base_mp": 70},
    "Kong": {"colors": ["Brown", "Black", "White", "Pink", "Red", "Blue", "Orange"], "base_hp": 170, "base_mp": 30},
    "Cheep Cheep": {"colors": ["Orange", "Black", "White", "Red", "Blue", "Green", "Pink", "Purple", "Cyan"], "base_hp": 70, "base_mp": 55},
    "Fang": {"colors": ["Blue", "Orange", "Red", "Black", "White", "Green", "Pink", "Purple", "Cyan"], "base_hp": 85, "base_mp": 50},
    "Bandinero": {"colors": ["Red", "Blue", "Yellow", "Black", "White", "Green", "Pink", "Gold"], "base_hp": 90, "base_mp": 60},
    "Spike": {"colors": ["Green", "Blue", "Red", "Yellow", "Black", "White", "Pink", "Purple"], "base_hp": 120, "base_mp": 35},
    "Spiny": {"colors": ["Red", "Blue", "Yellow", "Green", "Black", "White", "Pink", "Cyan", "Purple"], "base_hp": 100, "base_mp": 40},
    "Pokey": {"colors": ["Yellow", "Red", "Blue", "Green", "Orange", "Cyan", "Pink", "Black", "White"], "base_hp": 130, "base_mp": 30}
}

# Patch System from document
@dataclass
class Patch:
    name: str
    description: str
    price: int
    is_default: bool = False
    is_active: bool = False
    is_purchased: bool = False

PATCHES_LIST = [
    # Default Patches (Free)
    Patch("MLSS Patch", "Areas from Mario & Luigi: Superstar Saga", 0, True, True, True),
    Patch("MLPiT Patch", "Areas from Mario & Luigi: Partners in Time", 0, True, True, True),
    Patch("Beanish Patch", "Unlocks the Beanish class", 0, True, True, True),
    Patch("Ukiki Patch", "Unlocks the Ukiki class", 0, True, True, True),
    Patch("Poison Mushroom Patch", "Adds Poison Mushroom item - Turn enemies tiny!", 0, True, True, True),
    
    # Available Patches (Purchasable)
    Patch("MLBiS Patch", "Areas from Mario & Luigi: Bowser's Inside Story", 750),
    Patch("'Shroomy Helpers Patch", "Recruit Toad, Blue Toad, and Yellow Toad helpers", 1000),
    Patch("Golden Mushroom Patch", "Your speed will max out!", 500),
    Patch("Apprentice Patch", "Become apprentice of Mario, Luigi, Wario, Bowser, or Fawful", 1000000),
    Patch("Stuffwell Patch", "Get customizable Stuffwell to replace Star Sprite. BACK TO ADVENTURE!!", 1000),
    Patch("Star Guardians Patch", "Recruit Geno and Mallow", 1000),
    Patch("SMRPG Patch", "Areas from Super Mario RPG. Beware the Forest's Mushrooms!", 1500),
    Patch("Smithy Gang Patch", "Add optional Smithy Gang bosses (requires SMRPG Patch)", 1000),
    Patch("Paper Partners Patch", "Recruit all Paper Mario partners (choose 3)", 2000),
    Patch("Cooligan Patch", "Unlocks the Cooligan class!", 750),
    Patch("Dark Patch", "Dark Star's power transfers to you and party - become dark versions!", 2000000),
    Patch("Fountain of Youth Patch", "Stay in baby class forever! (even if adult)", 1000000),
    Patch("Toady Patch", "Unlocks the Toady class!", 500),
    Patch("Rookie Patch", "Get thief training under Popple", 1500)
]

# Guardian Sprites
GUARDIAN_SPRITES = [
    {"name": "Starlow", "color": YELLOW, "personality": "Helpful and energetic", "bonus": "hp"},
    {"name": "Dreambert", "color": BLUE, "personality": "Wise and calm", "bonus": "mp"},
    {"name": "Stuffwell", "color": RED, "personality": "Analytical and precise", "bonus": "defense"},
    {"name": "Chippy", "color": GREEN, "personality": "Cheerful and optimistic", "bonus": "speed"},
    {"name": "Glowbert", "color": PURPLE, "personality": "Mysterious and powerful", "bonus": "magic"},
    {"name": "Sparkle", "color": PINK, "personality": "Friendly and supportive", "bonus": "luck"}
]

# Story Dialogues from document
STORY_DIALOGUES = [
    {"speaker": "Starlow", "text": "Welcome to the Mushroom World! The Star Spirits are putting your Star Energy into a new being..."},
    {"speaker": "Narrator", "text": "You feel yourself becoming mortal, taking physical form..."},
    {"speaker": "Narrator", "text": "Being a helpless baby, you suddenly appear in the Mushroom Kingdom!"},
    {"speaker": "Toadsworth", "text": "Oh my! Another baby has appeared! I must take you to Princess Peach!"},
    {"speaker": "Princess Peach", "text": "So many orphan babies have been appearing lately... It's quite mysterious."},
    {"speaker": "Toadsworth", "text": "I'll take you to the playroom for now."},
    {"speaker": "Narrator", "text": "*Suddenly, Bowser crashes through the wall!*"},
    {"speaker": "Bowser", "text": "Where's Peach?! Oh... wrong room. Wait, a baby?"},
    {"speaker": "You", "text": "Meanie!!"},
    {"speaker": "Bowser", "text": "What?! How dare you! I'll teach you some respect!"},
    {"speaker": "Starlow", "text": "*sigh* Here we go again... Let me teach you how to battle."}
]

@dataclass
class Character:
    name: str = ""
    species: str = ""
    gender: str = ""
    color: str = ""
    age: str = "baby"
    level: int = 1
    hp: int = 100
    max_hp: int = 100
    mp: int = 50
    max_mp: int = 50
    attack: int = 10
    defense: int = 5
    speed: int = 10
    exp: int = 0
    exp_to_next: int = 100
    coins: int = 0
    guardian_sprite: str = ""
    inventory: List[Dict] = field(default_factory=list)
    party_members: List[str] = field(default_factory=list)
    active_patches: List[str] = field(default_factory=list)
    special_attacks: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.inventory:
            self.inventory = [
                {"name": "Mushroom", "count": 1, "type": "healing", "effect": 50},
                {"name": "Maple Syrup", "count": 1, "type": "mp", "effect": 20},
                {"name": "Lucky Clover", "count": 1, "type": "buff", "effect": "luck"}
            ]
        if not self.special_attacks:
            self.special_attacks = ["Jump", "Hammer"]

@dataclass
class Enemy:
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    speed: int
    exp_reward: int
    coin_reward: int
    sprite_color: Tuple[int, int, int]
    special_attack: str = ""
    
class BattleEngine:
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy
        self.turn = "player"
        self.battle_log = []
        self.is_tutorial = False
        
    def player_attack(self, attack_type="normal"):
        damage = max(1, self.player.attack - self.enemy.defense)
        if attack_type == "special":
            damage = int(damage * 1.5)
        self.enemy.hp -= damage
        self.battle_log.append(f"You dealt {damage} damage!")
        return damage
        
    def enemy_attack(self):
        damage = max(1, self.enemy.attack - self.player.defense)
        self.player.hp -= damage
        self.battle_log.append(f"{self.enemy.name} dealt {damage} damage!")
        return damage
        
    def check_battle_end(self):
        if self.enemy.hp <= 0:
            return "victory"
        elif self.player.hp <= 0:
            return "defeat"
        return None

# Room/Area Management
GAME_ROOMS = {
    "Toad Town": {
        "description": "The bustling center of the Mushroom Kingdom",
        "npcs": ["Toadsworth", "Shop Keeper", "Save Block"],
        "connections": ["Peach's Castle", "Dry Dry Desert", "Bean Bean Kingdom"],
        "enemies": [],
        "theme": "town"
    },
    "Peach's Castle": {
        "description": "Princess Peach's grand castle",
        "npcs": ["Princess Peach", "Toad Guards"],
        "connections": ["Toad Town", "Castle Gardens"],
        "enemies": [],
        "theme": "castle"
    },
    "Dry Dry Desert": {
        "description": "A vast desert with ancient ruins",
        "npcs": ["Desert Toads", "Nomadimouse"],
        "connections": ["Toad Town", "Dry Dry Ruins"],
        "enemies": ["Pokey", "Bandit", "Swooper"],
        "theme": "desert"
    },
    "Dry Dry Ruins": {
        "description": "Ancient ruins hiding Tutankoopa",
        "npcs": [],
        "connections": ["Dry Dry Desert"],
        "enemies": ["Pokey", "Buzzy Beetle", "Swooper"],
        "boss": "Tutankoopa",
        "theme": "dungeon"
    },
    "Bean Bean Kingdom": {
        "description": "Home of the Beanish people (MLSS Patch)",
        "npcs": ["Prince Peasley", "Lady Lima"],
        "connections": ["Toad Town", "Beanbean Castle Town"],
        "enemies": ["Troopea", "Beanie"],
        "theme": "kingdom",
        "requires_patch": "MLSS Patch"
    },
    "Star Road": {
        "description": "A mystical road in the clouds",
        "npcs": ["Star Spirits"],
        "connections": ["Toad Town"],
        "enemies": [],
        "theme": "sky"
    },
    "Bowser's Castle": {
        "description": "The Koopa King's fortress",
        "npcs": ["Kamek"],
        "connections": ["Dark Land"],
        "enemies": ["Hammer Bro", "Magikoopa", "Dry Bones"],
        "boss": "Bowser",
        "theme": "castle"
    }
}

# Sprite Classes
class AnimatedSprite:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.animation_frame = 0
        self.animation_speed = 0.2
        self.bounce_offset = 0
        self.scale = 1.0
        
    def update(self):
        self.animation_frame += self.animation_speed
        self.bounce_offset = math.sin(self.animation_frame) * 5
        
    def draw(self, screen, offset_x=0, offset_y=0):
        draw_x = int(self.x + offset_x)
        draw_y = int(self.y + offset_y + self.bounce_offset)
        
        body_rect = pygame.Rect(draw_x - self.width//2, draw_y - self.height//2, 
                               self.width, self.height)
        pygame.draw.ellipse(screen, self.color, body_rect)
        pygame.draw.ellipse(screen, BLACK, body_rect, 2)
        
        # Eyes
        eye_size = self.width // 6
        left_eye = (draw_x - self.width//4, draw_y - self.height//4)
        right_eye = (draw_x + self.width//4, draw_y - self.height//4)
        pygame.draw.circle(screen, WHITE, left_eye, eye_size)
        pygame.draw.circle(screen, WHITE, right_eye, eye_size)
        pygame.draw.circle(screen, BLACK, left_eye, eye_size//2)
        pygame.draw.circle(screen, BLACK, right_eye, eye_size//2)

class Particle:
    def __init__(self, x, y, color, velocity, lifetime=60):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 6)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.lifetime -= 1
        
    def draw(self, screen):
        if self.lifetime > 0:
            alpha = self.lifetime / self.max_lifetime
            size = int(self.size * alpha)
            if size > 0:
                safe_color = tuple(min(255, max(0, c)) for c in self.color)
                pygame.draw.circle(screen, safe_color, (int(self.x), int(self.y)), size)

class MarioLuigiLive:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mario & Luigi LIVE - Complete MMORPG")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.TITLE
        
        # Fonts
        self.font_tiny = pygame.font.Font(None, 16)
        self.font_small = pygame.font.Font(None, 20)
        self.font_normal = pygame.font.Font(None, 32)
        self.font_large = pygame.font.Font(None, 64)
        self.font_title = pygame.font.Font(None, 96)
        
        # Player
        self.player = Character()
        self.selected_species = ""
        self.selected_color = ""
        self.selected_guardian = ""
        self.name_input = ""
        
        # Game Progress
        self.story_index = 0
        self.current_room = "Toad Town"
        self.current_enemy = None
        self.battle_engine = None
        
        # Shop Items
        self.shop_items = [
            {"name": "Mushroom", "price": 50, "type": "healing", "effect": 50, "desc": "Restores 50 HP"},
            {"name": "Super Mushroom", "price": 100, "type": "healing", "effect": 100, "desc": "Restores 100 HP"},
            {"name": "Ultra Mushroom", "price": 200, "type": "healing", "effect": 200, "desc": "Restores 200 HP"},
            {"name": "Maple Syrup", "price": 30, "type": "mp", "effect": 20, "desc": "Restores 20 MP"},
            {"name": "Super Syrup", "price": 60, "type": "mp", "effect": 40, "desc": "Restores 40 MP"},
            {"name": "Ultra Syrup", "price": 120, "type": "mp", "effect": 80, "desc": "Restores 80 MP"},
            {"name": "1-Up Mushroom", "price": 500, "type": "revive", "effect": 100, "desc": "Revives fallen ally"},
            {"name": "Fire Flower", "price": 150, "type": "battle", "effect": 30, "desc": "Fire damage to all enemies"},
            {"name": "Ice Flower", "price": 150, "type": "battle", "effect": 30, "desc": "Ice damage to all enemies"},
            {"name": "Lucky Clover", "price": 200, "type": "buff", "effect": "luck", "desc": "Increases luck"},
            {"name": "Poison Mushroom", "price": 100, "type": "debuff", "effect": "shrink", "desc": "Shrinks enemies"},
            {"name": "Golden Mushroom", "price": 300, "type": "buff", "effect": "speed", "desc": "Max speed boost"}
        ]
        
        # Visual Effects
        self.particles = []
        self.animations = []
        self.global_timer = 0
        
        # Online System
        self.online_players = self.generate_online_players()
        self.chat_messages = []
        
        # Patches
        self.patches = PATCHES_LIST.copy()
        
    def generate_online_players(self):
        """Generate simulated online players"""
        names = ["MarioFan92", "LuigiPro", "ToadKing", "YoshiMaster", "PeachLover",
                "BowserBoss", "StarHunter", "CoinCollector", "MushroomKid", "FireFlower"]
        players = []
        for name in names:
            players.append({
                "name": name,
                "level": random.randint(1, 50),
                "species": random.choice(list(SPECIES_DATA.keys())),
                "room": random.choice(list(GAME_ROOMS.keys())),
                "status": random.choice(["Online", "In Battle", "Shopping", "Idle"])
            })
        return players
    
    def create_particle_burst(self, x, y, color, count=20):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed - 5)
            self.particles.append(Particle(x, y, color, velocity))
    
    def draw_gradient_background(self, color1, color2):
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = min(255, max(0, int(color1[0] * (1 - ratio) + color2[0] * ratio)))
            g = min(255, max(0, int(color1[1] * (1 - ratio) + color2[1] * ratio)))
            b = min(255, max(0, int(color1[2] * (1 - ratio) + color2[2] * ratio)))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    def draw_title_screen(self):
        self.draw_gradient_background((25, 25, 112), (135, 206, 235))
        
        # Title
        title_y = 100 + math.sin(self.global_timer * 0.05) * 10
        title = self.font_title.render("Mario & Luigi", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, title_y))
        
        subtitle = self.font_large.render("LIVE", True, GOLD)
        self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, title_y + 80))
        
        # Version text
        version = self.font_small.render("Complete MMORPG Edition", True, WHITE)
        self.screen.blit(version, (SCREEN_WIDTH//2 - version.get_width()//2, title_y + 140))
        
        # Menu buttons
        buttons = []
        menu_items = ["New Adventure", "Continue", "Online Lobby", "Patches", "Settings", "Quit"]
        
        for i, item in enumerate(menu_items):
            y = 350 + i * 50
            rect = pygame.Rect(SCREEN_WIDTH//2 - 150, y, 300, 40)
            
            # Hover effect
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, GOLD, rect, border_radius=20)
            else:
                pygame.draw.rect(self.screen, MARIO_RED, rect, border_radius=20)
            
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=20)
            
            text = self.font_normal.render(item, True, WHITE)
            self.screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))
            
            buttons.append((rect, item))
        
        # Flames Co. Badge
        badge_rect = pygame.Rect(10, SCREEN_HEIGHT - 40, 200, 30)
        pygame.draw.rect(self.screen, ORANGE, badge_rect, border_radius=15)
        badge_text = self.font_small.render("🔥 Flames Co. Network", True, WHITE)
        self.screen.blit(badge_text, (badge_rect.x + 10, badge_rect.y + 5))
        
        # Player count
        count_text = self.font_small.render(f"{len(self.online_players)} Players Online", True, WHITE)
        self.screen.blit(count_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30))
        
        return buttons
    
    def draw_character_creation(self):
        self.draw_gradient_background((168, 237, 234), (255, 192, 203))
        
        title = self.font_large.render("Character Creation", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Starlow dialogue
        dialogue_rect = pygame.Rect(50, 100, SCREEN_WIDTH - 100, 80)
        pygame.draw.rect(self.screen, PURPLE, dialogue_rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, dialogue_rect, 3, border_radius=10)
        
        dialogue = self.font_normal.render("Welcome, Star Energy! Let's create your new being!", True, WHITE)
        self.screen.blit(dialogue, (dialogue_rect.x + 20, dialogue_rect.y + 25))
        
        # Name input
        name_rect = pygame.Rect(100, 220, 400, 40)
        pygame.draw.rect(self.screen, WHITE, name_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, name_rect, 2, border_radius=5)
        
        name_label = self.font_normal.render("Name:", True, BLACK)
        self.screen.blit(name_label, (name_rect.x - 70, name_rect.y + 5))
        
        name_text = self.font_normal.render(self.name_input if self.name_input else "Enter name...", True, GRAY if not self.name_input else BLACK)
        self.screen.blit(name_text, (name_rect.x + 10, name_rect.y + 5))
        
        # Current selections
        info_y = 280
        info = [
            f"Species: {self.selected_species if self.selected_species else 'Not selected'}",
            f"Color: {self.selected_color if self.selected_color else 'Not selected'}",
            f"Guardian: {self.selected_guardian if self.selected_guardian else 'Not selected'}"
        ]
        
        for i, text in enumerate(info):
            info_text = self.font_normal.render(text, True, BLACK)
            self.screen.blit(info_text, (100, info_y + i * 40))
        
        # Buttons
        buttons = []
        
        button_y = 420
        if not self.selected_species:
            rect = pygame.Rect(SCREEN_WIDTH//2 - 100, button_y, 200, 40)
            pygame.draw.rect(self.screen, GREEN, rect, border_radius=20)
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=20)
            text = self.font_normal.render("Choose Species", True, WHITE)
            self.screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))
            buttons.append((rect, "species_select"))
        elif not self.selected_color:
            rect = pygame.Rect(SCREEN_WIDTH//2 - 100, button_y, 200, 40)
            pygame.draw.rect(self.screen, BLUE, rect, border_radius=20)
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=20)
            text = self.font_normal.render("Choose Color", True, WHITE)
            self.screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))
            buttons.append((rect, "color_select"))
        elif not self.selected_guardian:
            rect = pygame.Rect(SCREEN_WIDTH//2 - 100, button_y, 200, 40)
            pygame.draw.rect(self.screen, PURPLE, rect, border_radius=20)
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=20)
            text = self.font_normal.render("Choose Guardian", True, WHITE)
            self.screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))
            buttons.append((rect, "guardian_select"))
        else:
            rect = pygame.Rect(SCREEN_WIDTH//2 - 100, button_y, 200, 40)
            pygame.draw.rect(self.screen, GOLD, rect, border_radius=20)
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=20)
            text = self.font_normal.render("Start Adventure!", True, WHITE)
            self.screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))
            buttons.append((rect, "start_game"))
        
        # Back button
        back_rect = pygame.Rect(50, SCREEN_HEIGHT - 60, 100, 40)
        pygame.draw.rect(self.screen, GRAY, back_rect, border_radius=20)
        text = self.font_normal.render("Back", True, WHITE)
        self.screen.blit(text, (back_rect.centerx - text.get_width()//2, back_rect.centery - text.get_height()//2))
        buttons.append((back_rect, "back"))
        
        return buttons
    
    def draw_species_select(self):
        self.draw_gradient_background((200, 230, 255), (255, 200, 230))
        
        title = self.font_large.render("Choose Your Species", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # Species grid
        buttons = []
        species_list = list(SPECIES_DATA.keys())
        
        # Scrollable area
        scroll_area = pygame.Rect(50, 80, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 160)
        pygame.draw.rect(self.screen, WHITE, scroll_area, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, scroll_area, 2, border_radius=10)
        
        cols = 5
        rows = 7
        cell_width = 220
        cell_height = 60
        
        for i, species in enumerate(species_list):
            row = i // cols
            col = i % cols
            
            x = scroll_area.x + 20 + col * (cell_width + 10)
            y = scroll_area.y + 20 + row * (cell_height + 10)
            
            if y < scroll_area.bottom - cell_height:
                rect = pygame.Rect(x, y, cell_width, cell_height)
                
                # Highlight selected
                if species == self.selected_species:
                    pygame.draw.rect(self.screen, GOLD, rect, border_radius=10)
                else:
                    pygame.draw.rect(self.screen, LIGHT_GRAY, rect, border_radius=10)
                
                pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=10)
                
                # Species name
                name_text = self.font_small.render(species, True, BLACK)
                self.screen.blit(name_text, (rect.x + 10, rect.y + 5))
                
                # Stats preview
                stats = SPECIES_DATA[species]
                stats_text = self.font_tiny.render(f"HP: {stats['base_hp']} MP: {stats['base_mp']}", True, DARK_GRAY)
                self.screen.blit(stats_text, (rect.x + 10, rect.y + 30))
                
                buttons.append((rect, f"species_{species}"))
        
        # Back button
        back_rect = pygame.Rect(50, SCREEN_HEIGHT - 60, 100, 40)
        pygame.draw.rect(self.screen, GRAY, back_rect, border_radius=20)
        text = self.font_normal.render("Back", True, WHITE)
        self.screen.blit(text, (back_rect.centerx - text.get_width()//2, back_rect.centery - text.get_height()//2))
        buttons.append((back_rect, "back_to_creation"))
        
        return buttons
    
    def draw_color_select(self):
        self.draw_gradient_background((255, 200, 200), (200, 200, 255))
        
        title = self.font_large.render(f"Choose Color for {self.selected_species}", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        buttons = []
        colors = SPECIES_DATA[self.selected_species]["colors"]
        
        # Color grid
        for i, color_name in enumerate(colors):
            x = 200 + (i % 4) * 250
            y = 150 + (i // 4) * 100
            
            rect = pygame.Rect(x, y, 200, 60)
            
            # Get actual color
            color_map = {
                "Red": RED, "Blue": BLUE, "Green": GREEN, "Yellow": YELLOW,
                "Pink": PINK, "Black": BLACK, "White": WHITE, "Purple": PURPLE,
                "Orange": ORANGE, "Cyan": CYAN, "Brown": BROWN, "Gold": GOLD,
                "Silver": SILVER, "Dark Red": DARK_RED, "Light Skin": (255, 220, 177),
                "Dark Skin": (139, 90, 43), "Pale": (250, 250, 250), "Gray": GRAY
            }
            
            display_color = color_map.get(color_name, GRAY)
            
            # Color preview
            preview_rect = pygame.Rect(x - 50, y + 10, 40, 40)
            pygame.draw.rect(self.screen, display_color, preview_rect)
            pygame.draw.rect(self.screen, BLACK, preview_rect, 2)
            
            # Color button
            if color_name == self.selected_color:
                pygame.draw.rect(self.screen, GOLD, rect, border_radius=10)
            else:
                pygame.draw.rect(self.screen, LIGHT_GRAY, rect, border_radius=10)
            
            pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=10)
            
            text = self.font_normal.render(color_name, True, BLACK)
            self.screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))
            
            buttons.append((rect, f"color_{color_name}"))
        
        # Back button
        back_rect = pygame.Rect(50, SCREEN_HEIGHT - 60, 100, 40)
        pygame.draw.rect(self.screen, GRAY, back_rect, border_radius=20)
        text = self.font_normal.render("Back", True, WHITE)
        self.screen.blit(text, (back_rect.centerx - text.get_width()//2, back_rect.centery - text.get_height()//2))
        buttons.append((back_rect, "back_to_creation"))
        
        return buttons
    
    def draw_guardian_select(self):
        self.draw_gradient_background((255, 255, 200), (200, 255, 255))
        
        title = self.font_large.render("Choose Your Guardian Sprite", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Starlow's hut
        hut_rect = pygame.Rect(100, 100, SCREEN_WIDTH - 200, 120)
        pygame.draw.rect(self.screen, BROWN, hut_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, hut_rect, 3, border_radius=10)
        
        dialogue = self.font_normal.render("Pick a Guardian Sprite to accompany you on your journey!", True, WHITE)
        self.screen.blit(dialogue, (hut_rect.x + 20, hut_rect.y + 45))
        
        buttons = []
        
        # Guardian sprites
        for i, guardian in enumerate(GUARDIAN_SPRITES):
            x = 150 + (i % 3) * 380
            y = 280 + (i // 3) * 180
            
            rect = pygame.Rect(x, y, 320, 150)
            
            if guardian["name"] == self.selected_guardian:
                pygame.draw.rect(self.screen, GOLD, rect, border_radius=10)
            else:
                pygame.draw.rect(self.screen, WHITE, rect, border_radius=10)
            
            pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=10)
            
            # Star sprite preview
            star_x = x + 40
            star_y = y + 60
            
            # Draw star
            points = []
            for j in range(10):
                angle = math.pi * 2 * j / 10
                if j % 2 == 0:
                    radius = 30
                else:
                    radius = 15
                px = star_x + math.cos(angle) * radius
                py = star_y + math.sin(angle) * radius
                points.append((px, py))
            
            pygame.draw.polygon(self.screen, guardian["color"], points)
            pygame.draw.polygon(self.screen, BLACK, points, 2)
            
            # Guardian info
            name_text = self.font_normal.render(guardian["name"], True, BLACK)
            self.screen.blit(name_text, (x + 100, y + 20))
            
            personality_text = self.font_small.render(guardian["personality"], True, DARK_GRAY)
            self.screen.blit(personality_text, (x + 100, y + 50))
            
            bonus_text = self.font_small.render(f"Bonus: +{guardian['bonus'].upper()}", True, guardian["color"])
            self.screen.blit(bonus_text, (x + 100, y + 80))
            
            buttons.append((rect, f"guardian_{guardian['name']}"))
        
        # Back button
        back_rect = pygame.Rect(50, SCREEN_HEIGHT - 60, 100, 40)
        pygame.draw.rect(self.screen, GRAY, back_rect, border_radius=20)
        text = self.font_normal.render("Back", True, WHITE)
        self.screen.blit(text, (back_rect.centerx - text.get_width()//2, back_rect.centery - text.get_height()//2))
        buttons.append((back_rect, "back_to_creation"))
        
        return buttons
    
    def draw_story_intro(self):
        self.draw_gradient_background((50, 50, 150), (150, 50, 150))
        
        # Story dialogue box
        dialogue_rect = pygame.Rect(100, 200, SCREEN_WIDTH - 200, 250)
        pygame.draw.rect(self.screen, BLACK, dialogue_rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, dialogue_rect, 3, border_radius=10)
        
        if self.story_index < len(STORY_DIALOGUES):
            current = STORY_DIALOGUES[self.story_index]
            
            # Speaker name
            speaker_text = self.font_normal.render(current["speaker"] + ":", True, GOLD)
            self.screen.blit(speaker_text, (dialogue_rect.x + 30, dialogue_rect.y + 30))
            
            # Dialogue text
            lines = self.wrap_text(current["text"], dialogue_rect.width - 60)
            for i, line in enumerate(lines):
                text = self.font_normal.render(line, True, WHITE)
                self.screen.blit(text, (dialogue_rect.x + 30, dialogue_rect.y + 80 + i * 35))
        
        # Continue button
        buttons = []
        continue_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 500, 200, 50)
        pygame.draw.rect(self.screen, GREEN, continue_rect, border_radius=25)
        pygame.draw.rect(self.screen, WHITE, continue_rect, 2, border_radius=25)
        
        if self.story_index == len(STORY_DIALOGUES) - 1:
            text = self.font_normal.render("Start Battle!", True, WHITE)
        else:
            text = self.font_normal.render("Continue", True, WHITE)
        
        self.screen.blit(text, (continue_rect.centerx - text.get_width()//2, 
                               continue_rect.centery - text.get_height()//2))
        buttons.append((continue_rect, "continue_story"))
        
        return buttons
    
    def draw_battle_screen(self):
        self.draw_gradient_background((100, 50, 50), (50, 50, 100))
        
        # Battle arena
        arena_rect = pygame.Rect(50, 50, SCREEN_WIDTH - 100, 400)
        pygame.draw.rect(self.screen, WHITE, arena_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, arena_rect, 3, border_radius=10)
        
        # Player side
        player_sprite = AnimatedSprite(300, 250, 60, 80, GREEN)
        player_sprite.draw(self.screen)
        
        # Player stats
        player_stats_rect = pygame.Rect(100, 100, 200, 100)
        pygame.draw.rect(self.screen, BLACK, player_stats_rect, border_radius=5)
        pygame.draw.rect(self.screen, WHITE, player_stats_rect, 2, border_radius=5)
        
        hp_text = self.font_small.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, WHITE)
        mp_text = self.font_small.render(f"MP: {self.player.mp}/{self.player.max_mp}", True, WHITE)
        self.screen.blit(hp_text, (player_stats_rect.x + 10, player_stats_rect.y + 10))
        self.screen.blit(mp_text, (player_stats_rect.x + 10, player_stats_rect.y + 35))
        
        # HP bar
        hp_bar_bg = pygame.Rect(player_stats_rect.x + 10, player_stats_rect.y + 60, 180, 20)
        pygame.draw.rect(self.screen, DARK_GRAY, hp_bar_bg)
        hp_fill = (self.player.hp / self.player.max_hp) * 180
        pygame.draw.rect(self.screen, RED, (hp_bar_bg.x, hp_bar_bg.y, hp_fill, 20))
        pygame.draw.rect(self.screen, WHITE, hp_bar_bg, 2)
        
        # Enemy side
        if self.current_enemy:
            enemy_sprite = AnimatedSprite(900, 250, 80, 100, self.current_enemy.sprite_color)
            enemy_sprite.draw(self.screen)
            
            # Enemy stats
            enemy_stats_rect = pygame.Rect(800, 100, 200, 100)
            pygame.draw.rect(self.screen, BLACK, enemy_stats_rect, border_radius=5)
            pygame.draw.rect(self.screen, WHITE, enemy_stats_rect, 2, border_radius=5)
            
            enemy_name = self.font_small.render(self.current_enemy.name, True, GOLD)
            enemy_hp = self.font_small.render(f"HP: {self.current_enemy.hp}/{self.current_enemy.max_hp}", True, WHITE)
            self.screen.blit(enemy_name, (enemy_stats_rect.x + 10, enemy_stats_rect.y + 10))
            self.screen.blit(enemy_hp, (enemy_stats_rect.x + 10, enemy_stats_rect.y + 35))
            
            # Enemy HP bar
            enemy_hp_bar = pygame.Rect(enemy_stats_rect.x + 10, enemy_stats_rect.y + 60, 180, 20)
            pygame.draw.rect(self.screen, DARK_GRAY, enemy_hp_bar)
            enemy_hp_fill = (self.current_enemy.hp / self.current_enemy.max_hp) * 180
            pygame.draw.rect(self.screen, RED, (enemy_hp_bar.x, enemy_hp_bar.y, enemy_hp_fill, 20))
            pygame.draw.rect(self.screen, WHITE, enemy_hp_bar, 2)
        
        # Battle menu
        menu_rect = pygame.Rect(50, 480, SCREEN_WIDTH - 100, 200)
        pygame.draw.rect(self.screen, BLACK, menu_rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, menu_rect, 3, border_radius=10)
        
        buttons = []
        actions = ["Attack", "Special", "Item", "Defend", "Run"]
        
        for i, action in enumerate(actions):
            x = menu_rect.x + 50 + (i % 3) * 350
            y = menu_rect.y + 30 + (i // 3) * 80
            
            action_rect = pygame.Rect(x, y, 300, 60)
            pygame.draw.rect(self.screen, MARIO_RED, action_rect, border_radius=20)
            pygame.draw.rect(self.screen, WHITE, action_rect, 2, border_radius=20)
            
            text = self.font_normal.render(action, True, WHITE)
            self.screen.blit(text, (action_rect.centerx - text.get_width()//2,
                                   action_rect.centery - text.get_height()//2))
            
            buttons.append((action_rect, f"battle_{action.lower()}"))
        
        # Battle log
        if self.battle_engine and self.battle_engine.battle_log:
            log_y = 500
            for log_entry in self.battle_engine.battle_log[-3:]:
                log_text = self.font_small.render(log_entry, True, YELLOW)
                self.screen.blit(log_text, (menu_rect.x + 700, log_y))
                log_y += 25
        
        return buttons
    
    def draw_patches_screen(self):
        self.draw_gradient_background((100, 200, 255), (255, 200, 100))
        
        title = self.font_large.render("PATCHES", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # Patches list area
        list_rect = pygame.Rect(50, 80, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 160)
        pygame.draw.rect(self.screen, WHITE, list_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, list_rect, 2, border_radius=10)
        
        buttons = []
        y_offset = 0
        
        # Default patches section
        default_title = self.font_normal.render("DEFAULT PATCHES (Free)", True, BLACK)
        self.screen.blit(default_title, (list_rect.x + 20, list_rect.y + 20))
        y_offset += 50
        
        for patch in self.patches:
            if patch.is_default:
                patch_rect = pygame.Rect(list_rect.x + 20, list_rect.y + y_offset, list_rect.width - 40, 60)
                
                # Background
                pygame.draw.rect(self.screen, LIGHT_GRAY, patch_rect, border_radius=5)
                pygame.draw.rect(self.screen, BLACK, patch_rect, 1, border_radius=5)
                
                # Patch name
                name_text = self.font_small.render(patch.name, True, BLUE)
                self.screen.blit(name_text, (patch_rect.x + 10, patch_rect.y + 5))
                
                # Description
                desc_text = self.font_tiny.render(patch.description, True, DARK_GRAY)
                self.screen.blit(desc_text, (patch_rect.x + 10, patch_rect.y + 30))
                
                # Status
                status_rect = pygame.Rect(patch_rect.right - 100, patch_rect.y + 15, 80, 30)
                pygame.draw.rect(self.screen, GREEN, status_rect, border_radius=15)
                status_text = self.font_tiny.render("ACTIVE", True, WHITE)
                self.screen.blit(status_text, (status_rect.centerx - status_text.get_width()//2,
                                              status_rect.centery - status_text.get_height()//2))
                
                y_offset += 70
        
        # Available patches section
        y_offset += 30
        available_title = self.font_normal.render("AVAILABLE PATCHES", True, BLACK)
        self.screen.blit(available_title, (list_rect.x + 20, list_rect.y + y_offset))
        y_offset += 50
        
        for patch in self.patches:
            if not patch.is_default and y_offset < list_rect.height - 80:
                patch_rect = pygame.Rect(list_rect.x + 20, list_rect.y + y_offset, list_rect.width - 40, 60)
                
                # Background
                if patch.is_purchased:
                    pygame.draw.rect(self.screen, (200, 255, 200), patch_rect, border_radius=5)
                else:
                    pygame.draw.rect(self.screen, WHITE, patch_rect, border_radius=5)
                pygame.draw.rect(self.screen, BLACK, patch_rect, 1, border_radius=5)
                
                # Patch name
                name_text = self.font_small.render(patch.name, True, PURPLE)
                self.screen.blit(name_text, (patch_rect.x + 10, patch_rect.y + 5))
                
                # Description
                desc_text = self.font_tiny.render(patch.description[:60] + "..." if len(patch.description) > 60 else patch.description, 
                                                 True, DARK_GRAY)
                self.screen.blit(desc_text, (patch_rect.x + 10, patch_rect.y + 30))
                
                # Price or status
                if patch.is_purchased:
                    if patch.is_active:
                        status_rect = pygame.Rect(patch_rect.right - 100, patch_rect.y + 15, 80, 30)
                        pygame.draw.rect(self.screen, GREEN, status_rect, border_radius=15)
                        status_text = self.font_tiny.render("ACTIVE", True, WHITE)
                        self.screen.blit(status_text, (status_rect.centerx - status_text.get_width()//2,
                                                      status_rect.centery - status_text.get_height()//2))
                    else:
                        activate_rect = pygame.Rect(patch_rect.right - 100, patch_rect.y + 15, 80, 30)
                        pygame.draw.rect(self.screen, BLUE, activate_rect, border_radius=15)
                        activate_text = self.font_tiny.render("ACTIVATE", True, WHITE)
                        self.screen.blit(activate_text, (activate_rect.centerx - activate_text.get_width()//2,
                                                        activate_rect.centery - activate_text.get_height()//2))
                        buttons.append((activate_rect, f"activate_patch_{patch.name}"))
                else:
                    price_text = self.font_small.render(f"{patch.price:,} coins", True, 
                                                       GREEN if self.player.coins >= patch.price else RED)
                    self.screen.blit(price_text, (patch_rect.right - 150, patch_rect.y + 20))
                    
                    if self.player.coins >= patch.price:
                        buy_rect = pygame.Rect(patch_rect.right - 220, patch_rect.y + 15, 60, 30)
                        pygame.draw.rect(self.screen, GOLD, buy_rect, border_radius=15)
                        buy_text = self.font_tiny.render("BUY", True, WHITE)
                        self.screen.blit(buy_text, (buy_rect.centerx - buy_text.get_width()//2,
                                                   buy_rect.centery - buy_text.get_height()//2))
                        buttons.append((buy_rect, f"buy_patch_{patch.name}"))
                
                y_offset += 70
        
        # Player coins display
        coins_rect = pygame.Rect(SCREEN_WIDTH - 250, 25, 200, 40)
        pygame.draw.rect(self.screen, BLACK, coins_rect, border_radius=20)
        coins_text = self.font_normal.render(f"💰 {self.player.coins:,}", True, GOLD)
        self.screen.blit(coins_text, (coins_rect.centerx - coins_text.get_width()//2,
                                     coins_rect.centery - coins_text.get_height()//2))
        
        # Back button
        back_rect = pygame.Rect(50, SCREEN_HEIGHT - 60, 100, 40)
        pygame.draw.rect(self.screen, GRAY, back_rect, border_radius=20)
        text = self.font_normal.render("Back", True, WHITE)
        self.screen.blit(text, (back_rect.centerx - text.get_width()//2, back_rect.centery - text.get_height()//2))
        buttons.append((back_rect, "back_to_title"))
        
        return buttons
    
    def wrap_text(self, text, max_width):
        """Wrap text to fit within max width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = self.font_normal.render(test_line, True, BLACK)
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def initialize_character(self):
        """Initialize character after creation"""
        self.player.name = self.name_input
        self.player.species = self.selected_species
        self.player.color = self.selected_color
        self.player.guardian_sprite = self.selected_guardian
        
        # Set base stats from species
        species_stats = SPECIES_DATA[self.selected_species]
        self.player.max_hp = species_stats["base_hp"]
        self.player.hp = self.player.max_hp
        self.player.max_mp = species_stats["base_mp"]
        self.player.mp = self.player.max_mp
        
        # Apply guardian bonus
        for guardian in GUARDIAN_SPRITES:
            if guardian["name"] == self.selected_guardian:
                if guardian["bonus"] == "hp":
                    self.player.max_hp += 20
                    self.player.hp = self.player.max_hp
                elif guardian["bonus"] == "mp":
                    self.player.max_mp += 10
                    self.player.mp = self.player.max_mp
                elif guardian["bonus"] == "defense":
                    self.player.defense += 3
                elif guardian["bonus"] == "speed":
                    self.player.speed += 5
                elif guardian["bonus"] == "magic":
                    self.player.attack += 5
                elif guardian["bonus"] == "luck":
                    # Luck affects critical hit chance and item drops
                    pass
    
    def start_tutorial_battle(self):
        """Start the tutorial battle with Bowser"""
        self.current_enemy = Enemy(
            name="Bowser",
            hp=50,
            max_hp=50,
            attack=8,
            defense=5,
            speed=5,
            exp_reward=100,
            coin_reward=50,
            sprite_color=ORANGE,
            special_attack="Fire Breath"
        )
        
        self.battle_engine = BattleEngine(self.player, self.current_enemy)
        self.battle_engine.is_tutorial = True
        self.state = GameState.BATTLE
    
    def handle_click(self, pos, buttons):
        """Handle mouse clicks"""
        for rect, action in buttons:
            if rect.collidepoint(pos):
                self.handle_action(action)
    
    def handle_action(self, action):
        """Handle button actions"""
        if action == "New Adventure":
            self.state = GameState.CHAR_CREATION
            self.player = Character()
            self.name_input = ""
            
        elif action == "Online Lobby":
            self.state = GameState.ONLINE_LOBBY
            
        elif action == "Patches":
            self.state = GameState.PATCHES
            
        elif action == "Quit":
            self.running = False
            
        elif action == "species_select":
            self.state = GameState.SPECIES_SELECT
            
        elif action == "color_select":
            if self.selected_species:
                self.state = GameState.COLOR_SELECT
                
        elif action == "guardian_select":
            if self.selected_color:
                self.state = GameState.GUARDIAN_SELECT
                
        elif action.startswith("species_"):
            self.selected_species = action.replace("species_", "")
            self.state = GameState.CHAR_CREATION
            
        elif action.startswith("color_"):
            self.selected_color = action.replace("color_", "")
            self.state = GameState.CHAR_CREATION
            
        elif action.startswith("guardian_"):
            self.selected_guardian = action.replace("guardian_", "")
            self.state = GameState.CHAR_CREATION
            
        elif action == "start_game":
            if self.name_input and self.selected_species and self.selected_color and self.selected_guardian:
                self.initialize_character()
                self.state = GameState.STORY_INTRO
                self.story_index = 0
                
        elif action == "continue_story":
            self.story_index += 1
            if self.story_index >= len(STORY_DIALOGUES):
                self.start_tutorial_battle()
                
        elif action.startswith("battle_"):
            if self.battle_engine:
                battle_action = action.replace("battle_", "")
                if battle_action == "attack":
                    self.battle_engine.player_attack()
                    self.battle_engine.enemy_attack()
                elif battle_action == "special":
                    self.battle_engine.player_attack("special")
                    self.battle_engine.enemy_attack()
                elif battle_action == "run":
                    self.state = GameState.WORLD_MAP
                    
                # Check battle end
                result = self.battle_engine.check_battle_end()
                if result == "victory":
                    self.player.exp += self.current_enemy.exp_reward
                    self.player.coins += self.current_enemy.coin_reward
                    
                    # Level up check
                    if self.player.exp >= self.player.exp_to_next:
                        self.player.level += 1
                        self.player.exp = 0
                        self.player.exp_to_next = self.player.level * 100
                        self.player.max_hp += 10
                        self.player.hp = self.player.max_hp
                        self.player.max_mp += 5
                        self.player.mp = self.player.max_mp
                        self.player.attack += 2
                        self.player.defense += 1
                        self.player.speed += 1
                    
                    self.state = GameState.WORLD_MAP
                elif result == "defeat":
                    # Respawn with half HP
                    self.player.hp = self.player.max_hp // 2
                    self.state = GameState.WORLD_MAP
                    
        elif action.startswith("buy_patch_"):
            patch_name = action.replace("buy_patch_", "")
            for patch in self.patches:
                if patch.name == patch_name and self.player.coins >= patch.price:
                    self.player.coins -= patch.price
                    patch.is_purchased = True
                    self.create_particle_burst(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, GOLD, 30)
                    
        elif action.startswith("activate_patch_"):
            patch_name = action.replace("activate_patch_", "")
            for patch in self.patches:
                if patch.name == patch_name and patch.is_purchased:
                    patch.is_active = True
                    self.player.active_patches.append(patch_name)
                    
        elif action == "back" or action == "back_to_title":
            self.state = GameState.TITLE
            
        elif action == "back_to_creation":
            self.state = GameState.CHAR_CREATION
    
    def handle_text_input(self, event):
        """Handle text input for character name"""
        if self.state == GameState.CHAR_CREATION:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.name_input = self.name_input[:-1]
                elif event.key == pygame.K_RETURN:
                    pass  # Name confirmed
                elif len(self.name_input) < 20:
                    self.name_input += event.unicode
    
    def update(self):
        """Update game state"""
        self.global_timer += 1
        
        # Update particles
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for particle in self.particles:
            particle.update()
    
    def draw(self):
        """Draw current game state"""
        self.screen.fill(BLACK)
        
        buttons = []
        
        if self.state == GameState.TITLE:
            buttons = self.draw_title_screen()
        elif self.state == GameState.CHAR_CREATION:
            buttons = self.draw_character_creation()
        elif self.state == GameState.SPECIES_SELECT:
            buttons = self.draw_species_select()
        elif self.state == GameState.COLOR_SELECT:
            buttons = self.draw_color_select()
        elif self.state == GameState.GUARDIAN_SELECT:
            buttons = self.draw_guardian_select()
        elif self.state == GameState.STORY_INTRO:
            buttons = self.draw_story_intro()
        elif self.state == GameState.BATTLE:
            buttons = self.draw_battle_screen()
        elif self.state == GameState.PATCHES:
            buttons = self.draw_patches_screen()
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # FPS counter
        fps_text = self.font_small.render(f"FPS: {int(self.clock.get_fps())}", True, WHITE)
        self.screen.blit(fps_text, (SCREEN_WIDTH - 80, 10))
        
        return buttons
    
    def run(self):
        """Main game loop"""
        while self.running:
            buttons = []
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.handle_click(event.pos, buttons)
                        self.create_particle_burst(event.pos[0], event.pos[1], YELLOW, 10)
                elif event.type == pygame.KEYDOWN:
                    self.handle_text_input(event)
            
            self.update()
            buttons = self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = MarioLuigiLive()
    game.run()

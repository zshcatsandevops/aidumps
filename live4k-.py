"""
Mario & Luigi LIVE - MMORPG
By Bomb Productions Games & Sprak Co.
Pygame Implementation with Flames Co. WFC and Flames Co. Live
"""

import pygame
import random
import json
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import time

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

# Game States
class GameState(Enum):
    TITLE = "title"
    CHAR_CREATION = "char_creation"
    NAME_ENTRY = "name_entry"
    SPECIES_SELECT = "species_select"
    COLOR_SELECT = "color_select"
    INTRO_STORY = "intro_story"
    MAIN_GAME = "main_game"
    BATTLE = "battle"
    SHOP = "shop"
    INVENTORY = "inventory"
    PATCHES = "patches"
    ONLINE_LOBBY = "online_lobby"
    GUARDIAN_SELECT = "guardian_select"

# Species Data
SPECIES_LIST = [
    "Human", "Koopa", "Goomba", "Pianta", "Noki", "Toad", "Yoshi",
    "Hammer Bro", "Luma", "Boo", "Bob-Omb", "Shy Guy", "Piranha Plant",
    "Tanooki", "Buzzy Beetle", "Lakitu", "Wiggler", "Shroob", "Monty Mole",
    "Birdo", "Cloud Creature", "Magikoopa", "Blooper", "Bumpty", "Thwomp",
    "Cataquack", "Chain-Chomp", "Crazee Dayzee", "Kong", "Cheep Cheep",
    "Fang", "Bandinero", "Spike", "Spiny", "Pokey"
]

# Color variants for each species
SPECIES_COLORS = {
    "Human": ["Light Skin", "Dark Skin"],
    "Koopa": ["Red", "Blue", "Green", "Black", "Pink", "Purple", "Orange", "Cyan"],
    "Goomba": ["Brown", "Red", "Blue", "Green", "Pink", "Black", "White"],
    "Toad": ["Red", "Blue", "Green", "Yellow", "Pink", "Black", "Orange", "Purple", "White"],
    "Yoshi": ["Red", "Green", "Blue", "Cyan", "Black", "White", "Yellow", "Pink", "Purple", "Orange"],
    "Luma": ["Gold", "Silver", "Purple", "Blue", "Dark Red", "Orange"],
    "Default": ["Red", "Blue", "Green", "Yellow", "Pink", "Black", "White", "Purple", "Orange", "Cyan"]
}

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
    exp: int = 0
    exp_to_next: int = 100
    coins: int = 0
    inventory: List[Dict] = None
    guardian_sprite: str = ""
    party_members: List[str] = None
    active_patches: List[str] = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = [
                {"name": "Mushroom", "count": 1},
                {"name": "Maple Syrup", "count": 1},
                {"name": "Lucky Clover", "count": 1}
            ]
        if self.party_members is None:
            self.party_members = []
        if self.active_patches is None:
            self.active_patches = ["MLSS Patch", "MLPiT Patch", "Beanish Patch", 
                                  "Ukiki Patch", "Poison Mushroom Patch"]

@dataclass
class Patch:
    name: str
    description: str
    price: int
    is_default: bool
    is_active: bool = False

class Enemy:
    def __init__(self, name, hp, attack, defense, exp_reward, coin_reward):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.exp_reward = exp_reward
        self.coin_reward = coin_reward

class MarioLuigiLive:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mario & Luigi LIVE - MMORPG")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.TITLE
        self.font_small = pygame.font.Font(None, 24)
        self.font_normal = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 72)
        self.font_title = pygame.font.Font(None, 96)
        
        # Game Data
        self.player = Character()
        self.current_enemy = None
        self.story_progress = 0
        self.dialogue_index = 0
        self.input_text = ""
        self.selected_species = ""
        self.selected_color = ""
        self.selected_guardian = ""
        self.battle_menu_index = 0
        self.shop_index = 0
        self.patch_index = 0
        
        # Online Players (simulated)
        self.online_players = self.generate_online_players()
        
        # Patches System
        self.patches = self.initialize_patches()
        
        # Shop Items
        self.shop_items = [
            {"name": "Mushroom", "price": 50, "description": "Restores 50 HP"},
            {"name": "Super Mushroom", "price": 100, "description": "Restores 100 HP"},
            {"name": "Maple Syrup", "price": 30, "description": "Restores 20 MP"},
            {"name": "Ultra Syrup", "price": 80, "description": "Restores 50 MP"},
            {"name": "1-Up Mushroom", "price": 500, "description": "Revives fallen ally"},
            {"name": "Lucky Clover", "price": 200, "description": "Increases luck"},
            {"name": "Fire Flower", "price": 150, "description": "Fire attack item"},
            {"name": "Ice Flower", "price": 150, "description": "Ice attack item"}
        ]
        
        # Guardian Sprites
        self.guardian_sprites = [
            {"name": "Starlow", "color": YELLOW, "personality": "Helpful and energetic"},
            {"name": "Dreambert", "color": BLUE, "personality": "Wise and calm"},
            {"name": "Stuffwell", "color": RED, "personality": "Analytical and precise"},
            {"name": "Chippy", "color": GREEN, "personality": "Cheerful and optimistic"},
            {"name": "Glowbert", "color": PURPLE, "personality": "Mysterious and powerful"},
            {"name": "Sparkle", "color": PINK, "personality": "Friendly and supportive"}
        ]
        
        # Story Dialogues
        self.story_dialogues = [
            "Starlow: Welcome to the Mushroom World! I'm here to guide you!",
            "The Star Spirits are putting your Star Energy into a new being...",
            "You feel yourself becoming mortal, taking physical form...",
            "Toadsworth: Oh my! Another baby has appeared! I must take you to Princess Peach!",
            "Princess Peach: So many orphan babies have been appearing lately... It's quite mysterious.",
            "Suddenly, Bowser crashes through the wall!",
            "Bowser: Where's Peach?! Oh... wrong room. Wait, a baby?",
            "You: Meanie!!",
            "Bowser: What?! How dare you! Let's battle!"
        ]
        
        # Flames Co. WFC Connection
        self.flames_co_connected = True
        self.connection_status = "Connected to Flames Co. WFC"
        
        # Animation timers
        self.animation_timer = 0
        self.star_animation = 0
        
    def generate_online_players(self):
        """Generate simulated online players"""
        names = ["MarioFan92", "LuigiLover", "ToadKing", "YoshiMaster", "PeachPower",
                 "BowserBoss", "StarPower", "Goomba123", "KoopaKid", "ShyGuy99"]
        players = []
        for name in names:
            players.append({
                "name": name,
                "level": random.randint(1, 50),
                "species": random.choice(SPECIES_LIST),
                "status": random.choice(["Online", "In Battle", "Shopping", "Idle"])
            })
        return players
    
    def initialize_patches(self):
        """Initialize all patches from the document"""
        patches = [
            # Default Patches
            Patch("MLSS Patch", "Areas from Mario & Luigi: Superstar Saga", 0, True, True),
            Patch("MLPiT Patch", "Areas from Mario & Luigi: Partners in Time", 0, True, True),
            Patch("Beanish Patch", "Unlocks the Beanish class", 0, True, True),
            Patch("Ukiki Patch", "Unlocks the Ukiki class", 0, True, True),
            Patch("Poison Mushroom Patch", "Adds Poison Mushroom item", 0, True, True),
            
            # Available Patches
            Patch("MLBiS Patch", "Areas from Bowser's Inside Story", 750, False),
            Patch("'Shroomy Helpers Patch", "Recruit Toad helpers", 1000, False),
            Patch("Golden Mushroom Patch", "Max out your speed!", 500, False),
            Patch("Apprentice Patch", "Become an apprentice!", 1000000, False),
            Patch("Stuffwell Patch", "Get Stuffwell companion", 1000, False),
            Patch("Star Guardians Patch", "Recruit Geno and Mallow", 1000, False),
            Patch("SMRPG Patch", "Areas from Super Mario RPG", 1500, False),
            Patch("Smithy Gang Patch", "Add Smithy Gang bosses", 1000, False),
            Patch("Paper Partners Patch", "Recruit Paper Mario partners", 2000, False),
            Patch("Cooligan Patch", "Unlocks Cooligan class", 750, False),
            Patch("Dark Patch", "Dark Star power!", 2000000, False),
            Patch("Fountain of Youth Patch", "Stay baby forever!", 1000000, False),
            Patch("Toady Patch", "Unlocks Toady class", 500, False),
            Patch("Rookie Patch", "Train under Popple", 1500, False)
        ]
        return patches
    
    def draw_gradient_rect(self, x, y, width, height, color1, color2):
        """Draw a gradient rectangle"""
        for i in range(height):
            color = [
                color1[j] + (color2[j] - color1[j]) * i // height
                for j in range(3)
            ]
            pygame.draw.line(self.screen, color, (x, y + i), (x + width, y + i))
    
    def draw_button(self, x, y, width, height, text, selected=False):
        """Draw a styled button"""
        if selected:
            self.draw_gradient_rect(x, y, width, height, PURPLE, BLUE)
            border_color = WHITE
        else:
            self.draw_gradient_rect(x, y, width, height, DARK_GRAY, GRAY)
            border_color = BLACK
        
        pygame.draw.rect(self.screen, border_color, (x, y, width, height), 3)
        
        text_surface = self.font_normal.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=(x + width//2, y + height//2))
        self.screen.blit(text_surface, text_rect)
        
        return pygame.Rect(x, y, width, height)
    
    def draw_title_screen(self):
        """Draw the title screen"""
        # Animated gradient background
        self.draw_gradient_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 
                               (102, 126, 234), (118, 75, 162))
        
        # Animated stars
        self.star_animation += 0.05
        for i in range(20):
            x = (i * 73) % SCREEN_WIDTH
            y = (i * 47 + self.star_animation * 20) % SCREEN_HEIGHT
            pygame.draw.circle(self.screen, WHITE, (int(x), int(y)), 2)
        
        # Title with shadow
        title_shadow = self.font_title.render("Mario & Luigi LIVE", True, BLACK)
        title_text = self.font_title.render("Mario & Luigi LIVE", True, WHITE)
        self.screen.blit(title_shadow, (SCREEN_WIDTH//2 - title_shadow.get_width()//2 + 3, 103))
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
        
        # Subtitle
        subtitle = self.font_normal.render("MMORPG by Bomb Productions Games & Sprak Co.", True, WHITE)
        self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 200))
        
        # Flames Co. Badge
        badge_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 250, 300, 40)
        self.draw_gradient_rect(badge_rect.x, badge_rect.y, badge_rect.width, badge_rect.height,
                               (255, 107, 107), (255, 217, 61))
        pygame.draw.rect(self.screen, WHITE, badge_rect, 2)
        badge_text = self.font_small.render("🔥 Flames Co. WFC Connected", True, WHITE)
        self.screen.blit(badge_text, (badge_rect.centerx - badge_text.get_width()//2, badge_rect.centery - 10))
        
        # Menu buttons
        buttons = [
            "Start New Adventure",
            "Flames Co. Live",
            "View Patches",
            "Online Lobby",
            "Quit Game"
        ]
        
        button_rects = []
        for i, button_text in enumerate(buttons):
            rect = self.draw_button(SCREEN_WIDTH//2 - 150, 350 + i * 70, 300, 50, button_text)
            button_rects.append((rect, button_text))
        
        # Copyright
        copyright_text = self.font_small.render("© Bomb Productions - Do not edit except for spelling errors", True, WHITE)
        self.screen.blit(copyright_text, (SCREEN_WIDTH//2 - copyright_text.get_width()//2, SCREEN_HEIGHT - 30))
        
        return button_rects
    
    def draw_character_creation(self):
        """Draw character creation screen"""
        self.screen.fill((168, 237, 234))
        
        # Title
        title = self.font_large.render("Character Creation", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Starlow dialogue box
        dialogue_rect = pygame.Rect(50, 120, SCREEN_WIDTH - 100, 100)
        self.draw_gradient_rect(dialogue_rect.x, dialogue_rect.y, 
                               dialogue_rect.width, dialogue_rect.height,
                               (102, 126, 234), (118, 75, 162))
        pygame.draw.rect(self.screen, WHITE, dialogue_rect, 3)
        
        dialogue = self.font_normal.render("Welcome, Star Energy! Let's create your new being!", True, WHITE)
        self.screen.blit(dialogue, (dialogue_rect.x + 20, dialogue_rect.y + 35))
        
        # Character info display
        info_y = 250
        info_items = [
            f"Name: {self.player.name}",
            f"Species: {self.player.species}",
            f"Gender: {self.player.gender}",
            f"Color: {self.player.color}",
            f"Age: {self.player.age}"
        ]
        
        for i, info in enumerate(info_items):
            text = self.font_normal.render(info, True, BLACK)
            self.screen.blit(text, (100, info_y + i * 40))
        
        # Buttons
        button_rects = []
        if not self.player.name:
            rect = self.draw_button(SCREEN_WIDTH//2 - 100, 500, 200, 50, "Enter Name")
            button_rects.append((rect, "enter_name"))
        elif not self.player.species:
            rect = self.draw_button(SCREEN_WIDTH//2 - 100, 500, 200, 50, "Choose Species")
            button_rects.append((rect, "choose_species"))
        elif not self.player.color:
            rect = self.draw_button(SCREEN_WIDTH//2 - 100, 500, 200, 50, "Choose Color")
            button_rects.append((rect, "choose_color"))
        else:
            rect1 = self.draw_button(SCREEN_WIDTH//2 - 250, 550, 200, 50, "Confirm")
            rect2 = self.draw_button(SCREEN_WIDTH//2 + 50, 550, 200, 50, "Reset")
            button_rects.append((rect1, "confirm"))
            button_rects.append((rect2, "reset"))
        
        rect_back = self.draw_button(50, SCREEN_HEIGHT - 80, 150, 50, "Back")
        button_rects.append((rect_back, "back"))
        
        return button_rects
    
    def draw_name_entry(self):
        """Draw name entry screen"""
        self.screen.fill((168, 237, 234))
        
        title = self.font_large.render("Enter Your Name", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        
        # Input box
        input_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 300, 400, 60)
        pygame.draw.rect(self.screen, WHITE, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 3)
        
        # Display input text
        text_surface = self.font_large.render(self.input_text, True, BLACK)
        self.screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))
        
        # Cursor
        if int(time.time() * 2) % 2:
            cursor_x = input_rect.x + 10 + text_surface.get_width()
            pygame.draw.line(self.screen, BLACK, 
                           (cursor_x, input_rect.y + 10),
                           (cursor_x, input_rect.y + 50), 3)
        
        # Instructions
        inst = self.font_normal.render("Type your name and press ENTER", True, BLACK)
        self.screen.blit(inst, (SCREEN_WIDTH//2 - inst.get_width()//2, 400))
        
        button_rects = []
        rect = self.draw_button(SCREEN_WIDTH//2 - 100, 500, 200, 50, "Confirm")
        button_rects.append((rect, "confirm_name"))
        
        return button_rects
    
    def draw_species_select(self):
        """Draw species selection screen"""
        self.screen.fill((168, 237, 234))
        
        title = self.font_large.render("Choose Your Species", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Species grid
        cols = 6
        rows = 6
        button_width = 150
        button_height = 40
        start_x = 100
        start_y = 120
        
        button_rects = []
        for i, species in enumerate(SPECIES_LIST):
            row = i // cols
            col = i % cols
            x = start_x + col * (button_width + 20)
            y = start_y + row * (button_height + 15)
            
            selected = species == self.selected_species
            rect = self.draw_button(x, y, button_width, button_height, species, selected)
            button_rects.append((rect, species))
        
        # Back button
        rect_back = self.draw_button(50, SCREEN_HEIGHT - 80, 150, 50, "Back")
        button_rects.append((rect_back, "back"))
        
        return button_rects
    
    def draw_color_select(self):
        """Draw color selection screen"""
        self.screen.fill((168, 237, 234))
        
        title = self.font_large.render(f"Choose Color for {self.player.species}", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Get colors for selected species
        colors = SPECIES_COLORS.get(self.player.species, SPECIES_COLORS["Default"])
        
        button_rects = []
        for i, color_name in enumerate(colors):
            x = SCREEN_WIDTH//2 - 150
            y = 150 + i * 60
            
            # Draw color preview
            color_preview = self.get_color_from_name(color_name)
            pygame.draw.rect(self.screen, color_preview, (x - 60, y + 10, 40, 30))
            pygame.draw.rect(self.screen, BLACK, (x - 60, y + 10, 40, 30), 2)
            
            selected = color_name == self.selected_color
            rect = self.draw_button(x, y, 300, 50, color_name, selected)
            button_rects.append((rect, color_name))
        
        # Back button
        rect_back = self.draw_button(50, SCREEN_HEIGHT - 80, 150, 50, "Back")
        button_rects.append((rect_back, "back"))
        
        return button_rects
    
    def get_color_from_name(self, color_name):
        """Convert color name to RGB tuple"""
        color_map = {
            "Red": RED, "Blue": BLUE, "Green": GREEN, "Yellow": YELLOW,
            "Pink": PINK, "Black": BLACK, "White": WHITE, "Purple": PURPLE,
            "Orange": ORANGE, "Cyan": CYAN, "Brown": (139, 69, 19),
            "Gray": GRAY, "Light Skin": (255, 220, 177), "Dark Skin": (139, 90, 43),
            "Gold": (255, 215, 0), "Silver": (192, 192, 192), "Dark Red": (139, 0, 0)
        }
        return color_map.get(color_name, GRAY)
    
    def draw_guardian_select(self):
        """Draw guardian sprite selection screen"""
        self.screen.fill((168, 237, 234))
        
        title = self.font_large.render("Choose Your Guardian Sprite", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Starlow's hut background
        hut_rect = pygame.Rect(100, 100, SCREEN_WIDTH - 200, 150)
        self.draw_gradient_rect(hut_rect.x, hut_rect.y, hut_rect.width, hut_rect.height,
                               (139, 69, 19), (160, 82, 45))
        pygame.draw.rect(self.screen, BLACK, hut_rect, 3)
        
        dialogue = self.font_normal.render("Pick a Guardian Sprite to accompany you!", True, WHITE)
        self.screen.blit(dialogue, (hut_rect.x + 20, hut_rect.y + 60))
        
        # Guardian sprites
        button_rects = []
        for i, guardian in enumerate(self.guardian_sprites):
            x = 150 + (i % 3) * 350
            y = 300 + (i // 3) * 200
            
            # Draw sprite
            self.draw_star_sprite(x + 75, y, guardian["color"])
            
            # Name and personality
            name_text = self.font_normal.render(guardian["name"], True, BLACK)
            self.screen.blit(name_text, (x, y + 60))
            
            personality_text = self.font_small.render(guardian["personality"], True, DARK_GRAY)
            self.screen.blit(personality_text, (x, y + 90))
            
            rect = pygame.Rect(x - 10, y - 10, 200, 120)
            if self.selected_guardian == guardian["name"]:
                pygame.draw.rect(self.screen, guardian["color"], rect, 3)
            
            button_rects.append((rect, guardian["name"]))
        
        # Confirm button
        if self.selected_guardian:
            rect_confirm = self.draw_button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 120, 200, 50, "Confirm")
            button_rects.append((rect_confirm, "confirm_guardian"))
        
        return button_rects
    
    def draw_star_sprite(self, x, y, color):
        """Draw an animated star sprite"""
        # Glowing effect
        for i in range(3):
            alpha = 50 - i * 15
            size = 30 + i * 10
            glow_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*color, alpha), (size, size), size)
            self.screen.blit(glow_surface, (x - size, y - size))
        
        # Main star
        angle = self.star_animation
        points = []
        for i in range(10):
            angle_offset = math.pi * 2 * i / 10
            if i % 2 == 0:
                radius = 25
            else:
                radius = 12
            px = x + math.cos(angle + angle_offset) * radius
            py = y + math.sin(angle + angle_offset) * radius
            points.append((px, py))
        
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, WHITE, points, 2)
    
    def draw_main_game(self):
        """Draw main game screen"""
        self.draw_gradient_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
                               (255, 236, 210), (252, 182, 159))
        
        # HUD
        self.draw_hud()
        
        # Game area
        game_rect = pygame.Rect(50, 150, SCREEN_WIDTH - 100, 400)
        pygame.draw.rect(self.screen, WHITE, game_rect)
        pygame.draw.rect(self.screen, BLACK, game_rect, 3)
        
        # Story/Dialogue
        if self.story_progress < len(self.story_dialogues):
            dialogue = self.story_dialogues[self.story_progress]
            lines = self.wrap_text(dialogue, game_rect.width - 40)
            y_offset = 0
            for line in lines:
                text = self.font_normal.render(line, True, BLACK)
                self.screen.blit(text, (game_rect.x + 20, game_rect.y + 20 + y_offset))
                y_offset += 35
            
            # Continue button
            button_rects = []
            rect = self.draw_button(game_rect.centerx - 100, game_rect.bottom - 60, 200, 40, "Continue")
            button_rects.append((rect, "continue_story"))
        else:
            # Game menu
            text = self.font_normal.render("Welcome to Toad Town!", True, BLACK)
            self.screen.blit(text, (game_rect.x + 20, game_rect.y + 20))
            
            button_rects = []
            buttons = [
                ("Battle Monsters", "battle"),
                ("Visit Shop", "shop"),
                ("View Inventory", "inventory"),
                ("Manage Patches", "patches"),
                ("Online Lobby", "online")
            ]
            
            for i, (text, action) in enumerate(buttons):
                x = game_rect.x + 20 + (i % 3) * 320
                y = game_rect.y + 100 + (i // 3) * 80
                rect = self.draw_button(x, y, 280, 60, text)
                button_rects.append((rect, action))
        
        # Party display
        self.draw_party_display()
        
        # Online players
        self.draw_online_players_mini()
        
        return button_rects
    
    def draw_hud(self):
        """Draw the HUD"""
        hud_rect = pygame.Rect(50, 20, SCREEN_WIDTH - 100, 100)
        pygame.draw.rect(self.screen, WHITE, hud_rect)
        pygame.draw.rect(self.screen, BLACK, hud_rect, 3)
        
        # HP Bar
        hp_text = self.font_normal.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, BLACK)
        self.screen.blit(hp_text, (70, 30))
        hp_bar_rect = pygame.Rect(200, 35, 200, 20)
        pygame.draw.rect(self.screen, GRAY, hp_bar_rect)
        hp_fill = (self.player.hp / self.player.max_hp) * 200
        pygame.draw.rect(self.screen, RED, (200, 35, hp_fill, 20))
        pygame.draw.rect(self.screen, BLACK, hp_bar_rect, 2)
        
        # MP Bar
        mp_text = self.font_normal.render(f"MP: {self.player.mp}/{self.player.max_mp}", True, BLACK)
        self.screen.blit(mp_text, (70, 60))
        mp_bar_rect = pygame.Rect(200, 65, 200, 20)
        pygame.draw.rect(self.screen, GRAY, mp_bar_rect)
        mp_fill = (self.player.mp / self.player.max_mp) * 200
        pygame.draw.rect(self.screen, BLUE, (200, 65, mp_fill, 20))
        pygame.draw.rect(self.screen, BLACK, mp_bar_rect, 2)
        
        # Level and EXP
        level_text = self.font_normal.render(f"Level: {self.player.level}", True, BLACK)
        self.screen.blit(level_text, (450, 30))
        
        exp_bar_rect = pygame.Rect(570, 35, 150, 20)
        pygame.draw.rect(self.screen, GRAY, exp_bar_rect)
        exp_fill = (self.player.exp / self.player.exp_to_next) * 150
        pygame.draw.rect(self.screen, PURPLE, (570, 35, exp_fill, 20))
        pygame.draw.rect(self.screen, BLACK, exp_bar_rect, 2)
        
        # Coins
        coin_text = self.font_normal.render(f"💰 Coins: {self.player.coins}", True, BLACK)
        self.screen.blit(coin_text, (450, 60))
        
        # Guardian Sprite
        if self.player.guardian_sprite:
            guardian = next((g for g in self.guardian_sprites if g["name"] == self.player.guardian_sprite), None)
            if guardian:
                self.draw_star_sprite(850, 55, guardian["color"])
                name_text = self.font_small.render(self.player.guardian_sprite, True, BLACK)
                self.screen.blit(name_text, (900, 45))
    
    def draw_party_display(self):
        """Draw party members"""
        party_rect = pygame.Rect(50, 570, SCREEN_WIDTH - 100, 80)
        pygame.draw.rect(self.screen, WHITE, party_rect)
        pygame.draw.rect(self.screen, BLACK, party_rect, 3)
        
        party_text = self.font_normal.render("Party:", True, BLACK)
        self.screen.blit(party_text, (70, 580))
        
        # Player
        member_rect = pygame.Rect(150, 580, 100, 60)
        self.draw_gradient_rect(member_rect.x, member_rect.y, member_rect.width, member_rect.height,
                               (102, 126, 234), (118, 75, 162))
        pygame.draw.rect(self.screen, WHITE, member_rect, 2)
        player_text = self.font_small.render("You", True, WHITE)
        self.screen.blit(player_text, (member_rect.centerx - player_text.get_width()//2, member_rect.centery - 10))
        
        # Party members
        for i, member in enumerate(self.player.party_members):
            member_rect = pygame.Rect(270 + i * 120, 580, 100, 60)
            self.draw_gradient_rect(member_rect.x, member_rect.y, member_rect.width, member_rect.height,
                                   (102, 126, 234), (118, 75, 162))
            pygame.draw.rect(self.screen, WHITE, member_rect, 2)
            member_text = self.font_small.render(member, True, WHITE)
            self.screen.blit(member_text, (member_rect.centerx - member_text.get_width()//2, member_rect.centery - 10))
    
    def draw_online_players_mini(self):
        """Draw mini online players display"""
        online_rect = pygame.Rect(50, 670, SCREEN_WIDTH - 100, 100)
        pygame.draw.rect(self.screen, WHITE, online_rect)
        pygame.draw.rect(self.screen, BLACK, online_rect, 3)
        
        title = self.font_normal.render("Players Online (Flames Co. WFC):", True, BLACK)
        self.screen.blit(title, (70, 680))
        
        # Display first few online players
        for i, player in enumerate(self.online_players[:8]):
            x = 70 + (i % 4) * 280
            y = 710 + (i // 4) * 30
            
            status_color = GREEN if player["status"] == "Online" else ORANGE
            pygame.draw.circle(self.screen, status_color, (x, y + 10), 5)
            
            player_text = self.font_small.render(f"{player['name']} (Lv.{player['level']})", True, BLACK)
            self.screen.blit(player_text, (x + 15, y))
    
    def draw_battle_screen(self):
        """Draw battle screen"""
        self.draw_gradient_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
                               (245, 247, 250), (195, 207, 226))
        
        title = self.font_large.render("BATTLE!", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Battle arena
        arena_rect = pygame.Rect(100, 100, SCREEN_WIDTH - 200, 350)
        pygame.draw.rect(self.screen, WHITE, arena_rect)
        pygame.draw.rect(self.screen, BLACK, arena_rect, 3)
        
        # Player side
        player_rect = pygame.Rect(200, 200, 150, 150)
        self.draw_gradient_rect(player_rect.x, player_rect.y, player_rect.width, player_rect.height,
                               (102, 126, 234), (118, 75, 162))
        pygame.draw.rect(self.screen, WHITE, player_rect, 3)
        
        player_sprite = self.font_large.render("👤", True, WHITE)
        self.screen.blit(player_sprite, (player_rect.centerx - 30, player_rect.centery - 30))
        
        player_name = self.font_normal.render(self.player.name, True, BLACK)
        self.screen.blit(player_name, (player_rect.centerx - player_name.get_width()//2, player_rect.bottom + 10))
        
        # Player HP
        hp_text = self.font_small.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, BLACK)
        self.screen.blit(hp_text, (player_rect.x, player_rect.top - 30))
        
        # Enemy side
        if self.current_enemy:
            enemy_rect = pygame.Rect(700, 200, 150, 150)
            self.draw_gradient_rect(enemy_rect.x, enemy_rect.y, enemy_rect.width, enemy_rect.height,
                                   (244, 67, 54), (233, 30, 99))
            pygame.draw.rect(self.screen, WHITE, enemy_rect, 3)
            
            enemy_sprite = self.font_large.render("👹", True, WHITE)
            self.screen.blit(enemy_sprite, (enemy_rect.centerx - 30, enemy_rect.centery - 30))
            
            enemy_name = self.font_normal.render(self.current_enemy.name, True, BLACK)
            self.screen.blit(enemy_name, (enemy_rect.centerx - enemy_name.get_width()//2, enemy_rect.bottom + 10))
            
            # Enemy HP
            hp_text = self.font_small.render(f"HP: {self.current_enemy.hp}/{self.current_enemy.max_hp}", True, BLACK)
            self.screen.blit(hp_text, (enemy_rect.x, enemy_rect.top - 30))
        
        # Battle menu
        menu_rect = pygame.Rect(100, 480, SCREEN_WIDTH - 200, 200)
        pygame.draw.rect(self.screen, WHITE, menu_rect)
        pygame.draw.rect(self.screen, BLACK, menu_rect, 3)
        
        button_rects = []
        menu_items = ["Attack", "Special Attack", "Item", "Defend", "Run"]
        
        for i, item in enumerate(menu_items):
            x = menu_rect.x + 50 + (i % 3) * 300
            y = menu_rect.y + 30 + (i // 3) * 80
            selected = i == self.battle_menu_index
            rect = self.draw_button(x, y, 250, 60, item, selected)
            button_rects.append((rect, item.lower().replace(" ", "_")))
        
        return button_rects
    
    def draw_shop_screen(self):
        """Draw shop screen"""
        self.draw_gradient_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
                               (255, 236, 210), (252, 182, 159))
        
        title = self.font_large.render("SHOP", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Coins display
        coins_text = self.font_normal.render(f"Your Coins: {self.player.coins}", True, BLACK)
        self.screen.blit(coins_text, (100, 100))
        
        # Shop grid
        button_rects = []
        for i, item in enumerate(self.shop_items):
            x = 100 + (i % 4) * 250
            y = 180 + (i // 4) * 180
            
            item_rect = pygame.Rect(x, y, 220, 150)
            pygame.draw.rect(self.screen, WHITE, item_rect)
            pygame.draw.rect(self.screen, BLACK, item_rect, 3)
            
            # Item icon
            icon_rect = pygame.Rect(x + 85, y + 10, 50, 50)
            self.draw_gradient_rect(icon_rect.x, icon_rect.y, icon_rect.width, icon_rect.height,
                                   (102, 126, 234), (118, 75, 162))
            pygame.draw.rect(self.screen, WHITE, icon_rect, 2)
            
            # Item name
            name_text = self.font_small.render(item["name"], True, BLACK)
            self.screen.blit(name_text, (item_rect.centerx - name_text.get_width()//2, y + 70))
            
            # Description
            desc_lines = self.wrap_text(item["description"], 200)
            for j, line in enumerate(desc_lines):
                desc_text = self.font_small.render(line, True, DARK_GRAY)
                self.screen.blit(desc_text, (x + 10, y + 95 + j * 20))
            
            # Price
            price_text = self.font_normal.render(f"{item['price']} coins", True, GREEN if self.player.coins >= item['price'] else RED)
            self.screen.blit(price_text, (item_rect.centerx - price_text.get_width()//2, y + 120))
            
            button_rects.append((item_rect, f"buy_{i}"))
        
        # Back button
        rect_back = self.draw_button(SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT - 80, 150, 50, "Back")
        button_rects.append((rect_back, "back"))
        
        return button_rects
    
    def draw_patches_screen(self):
        """Draw patches screen"""
        self.draw_gradient_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
                               (137, 247, 254), (102, 166, 255))
        
        title = self.font_large.render("PATCHES", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Scroll area
        scroll_rect = pygame.Rect(50, 100, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200)
        pygame.draw.rect(self.screen, WHITE, scroll_rect)
        pygame.draw.rect(self.screen, BLACK, scroll_rect, 3)
        
        button_rects = []
        y_offset = 0
        
        for i, patch in enumerate(self.patches):
            patch_rect = pygame.Rect(70, 120 + y_offset, SCREEN_WIDTH - 140, 80)
            pygame.draw.rect(self.screen, LIGHT_GRAY if i % 2 == 0 else WHITE, patch_rect)
            pygame.draw.rect(self.screen, BLACK, patch_rect, 2)
            
            # Patch name
            name_text = self.font_normal.render(patch.name, True, BLUE)
            self.screen.blit(name_text, (patch_rect.x + 20, patch_rect.y + 10))
            
            # Description
            desc_text = self.font_small.render(patch.description, True, BLACK)
            self.screen.blit(desc_text, (patch_rect.x + 20, patch_rect.y + 40))
            
            # Status/Price
            if patch.is_active:
                status_rect = pygame.Rect(patch_rect.right - 120, patch_rect.y + 25, 100, 30)
                pygame.draw.rect(self.screen, GREEN, status_rect)
                pygame.draw.rect(self.screen, BLACK, status_rect, 2)
                status_text = self.font_small.render("ACTIVE", True, WHITE)
                self.screen.blit(status_text, (status_rect.centerx - status_text.get_width()//2, status_rect.centery - 8))
            elif patch.is_default:
                status_rect = pygame.Rect(patch_rect.right - 120, patch_rect.y + 25, 100, 30)
                pygame.draw.rect(self.screen, BLUE, status_rect)
                pygame.draw.rect(self.screen, BLACK, status_rect, 2)
                status_text = self.font_small.render("DEFAULT", True, WHITE)
                self.screen.blit(status_text, (status_rect.centerx - status_text.get_width()//2, status_rect.centery - 8))
            else:
                price_text = self.font_normal.render(f"{patch.price} coins", True, GREEN if self.player.coins >= patch.price else RED)
                self.screen.blit(price_text, (patch_rect.right - 150, patch_rect.y + 25))
                
                if self.player.coins >= patch.price:
                    buy_rect = pygame.Rect(patch_rect.right - 100, patch_rect.y + 50, 80, 25)
                    pygame.draw.rect(self.screen, GREEN, buy_rect)
                    pygame.draw.rect(self.screen, BLACK, buy_rect, 1)
                    buy_text = self.font_small.render("BUY", True, WHITE)
                    self.screen.blit(buy_text, (buy_rect.centerx - buy_text.get_width()//2, buy_rect.centery - 8))
                    button_rects.append((buy_rect, f"buy_patch_{i}"))
            
            y_offset += 85
            
            if 120 + y_offset > scroll_rect.bottom - 100:
                break
        
        # Back button
        rect_back = self.draw_button(SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT - 70, 150, 50, "Back")
        button_rects.append((rect_back, "back"))
        
        return button_rects
    
    def wrap_text(self, text, max_width):
        """Wrap text to fit within max_width"""
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
    
    def handle_click(self, pos, button_rects):
        """Handle mouse clicks"""
        for rect, action in button_rects:
            if rect.collidepoint(pos):
                self.handle_action(action)
    
    def handle_action(self, action):
        """Handle button actions"""
        if action == "Start New Adventure":
            self.state = GameState.CHAR_CREATION
            self.player = Character()
        elif action == "Flames Co. Live":
            self.show_notification("Connected to Flames Co. Live!")
        elif action == "View Patches":
            self.state = GameState.PATCHES
        elif action == "Online Lobby":
            self.state = GameState.ONLINE_LOBBY
        elif action == "Quit Game":
            self.running = False
        elif action == "enter_name":
            self.state = GameState.NAME_ENTRY
            self.input_text = ""
        elif action == "choose_species":
            self.state = GameState.SPECIES_SELECT
        elif action == "choose_color":
            self.state = GameState.COLOR_SELECT
        elif action == "confirm":
            if self.player.name and self.player.species and self.player.color:
                self.player.gender = "male"  # Default for now
                self.state = GameState.GUARDIAN_SELECT
        elif action == "reset":
            self.player = Character()
        elif action == "back":
            if self.state in [GameState.CHAR_CREATION, GameState.PATCHES]:
                self.state = GameState.TITLE
            elif self.state in [GameState.NAME_ENTRY, GameState.SPECIES_SELECT, GameState.COLOR_SELECT]:
                self.state = GameState.CHAR_CREATION
            else:
                self.state = GameState.MAIN_GAME
        elif action == "confirm_name":
            if self.input_text:
                self.player.name = self.input_text
                self.state = GameState.CHAR_CREATION
        elif action in SPECIES_LIST:
            self.selected_species = action
            self.player.species = action
            self.state = GameState.CHAR_CREATION
        elif action in ["Red", "Blue", "Green", "Yellow", "Pink", "Black", "White", 
                        "Purple", "Orange", "Cyan", "Brown", "Light Skin", "Dark Skin",
                        "Gold", "Silver", "Dark Red"]:
            self.selected_color = action
            self.player.color = action
            self.state = GameState.CHAR_CREATION
        elif action == "confirm_guardian":
            if self.selected_guardian:
                self.player.guardian_sprite = self.selected_guardian
                self.state = GameState.MAIN_GAME
                self.story_progress = 0
        elif action in [g["name"] for g in self.guardian_sprites]:
            self.selected_guardian = action
        elif action == "continue_story":
            self.story_progress += 1
            if self.story_progress == 8:  # Bowser battle
                self.start_battle()
        elif action == "battle":
            self.start_battle()
        elif action == "shop":
            self.state = GameState.SHOP
        elif action == "inventory":
            self.show_notification("Inventory: " + ", ".join([f"{item['name']} x{item['count']}" for item in self.player.inventory]))
        elif action == "patches":
            self.state = GameState.PATCHES
        elif action == "online":
            self.state = GameState.ONLINE_LOBBY
        elif action.startswith("buy_"):
            if action.startswith("buy_patch_"):
                patch_index = int(action.split("_")[-1])
                patch = self.patches[patch_index]
                if self.player.coins >= patch.price and not patch.is_active:
                    self.player.coins -= patch.price
                    patch.is_active = True
                    self.player.active_patches.append(patch.name)
                    self.show_notification(f"Purchased {patch.name}!")
            else:
                item_index = int(action.split("_")[-1])
                item = self.shop_items[item_index]
                if self.player.coins >= item["price"]:
                    self.player.coins -= item["price"]
                    # Add to inventory
                    existing = next((i for i in self.player.inventory if i["name"] == item["name"]), None)
                    if existing:
                        existing["count"] += 1
                    else:
                        self.player.inventory.append({"name": item["name"], "count": 1})
                    self.show_notification(f"Purchased {item['name']}!")
        elif action == "attack":
            if self.current_enemy:
                damage = random.randint(10, 25)
                self.current_enemy.hp -= damage
                self.show_notification(f"Dealt {damage} damage!")
                if self.current_enemy.hp <= 0:
                    self.win_battle()
                else:
                    self.enemy_turn()
        elif action == "run":
            self.state = GameState.MAIN_GAME
            self.current_enemy = None
            self.show_notification("Escaped from battle!")
    
    def start_battle(self):
        """Start a battle"""
        self.state = GameState.BATTLE
        enemies = [
            Enemy("Goomba", 50, 10, 5, 20, 10),
            Enemy("Koopa Troopa", 70, 15, 8, 30, 15),
            Enemy("Pokey", 90, 20, 10, 40, 20),
            Enemy("Hammer Bro", 100, 25, 12, 50, 25),
            Enemy("Bowser", 200, 30, 15, 100, 100)
        ]
        
        if self.story_progress == 8:
            self.current_enemy = enemies[-1]  # Bowser
        else:
            self.current_enemy = random.choice(enemies[:-1])
    
    def enemy_turn(self):
        """Enemy's turn in battle"""
        if self.current_enemy:
            damage = random.randint(5, self.current_enemy.attack)
            self.player.hp -= damage
            self.show_notification(f"{self.current_enemy.name} dealt {damage} damage!")
            
            if self.player.hp <= 0:
                self.player.hp = 1  # Can't lose in this demo
                self.show_notification("You were defeated... but your guardian sprite revived you!")
    
    def win_battle(self):
        """Win the battle"""
        if self.current_enemy:
            self.player.exp += self.current_enemy.exp_reward
            self.player.coins += self.current_enemy.coin_reward
            self.show_notification(f"Victory! Gained {self.current_enemy.exp_reward} EXP and {self.current_enemy.coin_reward} coins!")
            
            # Level up check
            if self.player.exp >= self.player.exp_to_next:
                self.player.level += 1
                self.player.exp = 0
                self.player.exp_to_next = self.player.level * 100
                self.player.max_hp += 20
                self.player.hp = self.player.max_hp
                self.player.max_mp += 10
                self.player.mp = self.player.max_mp
                self.show_notification(f"LEVEL UP! Now level {self.player.level}!")
            
            if self.story_progress == 8:
                self.story_progress = 9
            
            self.current_enemy = None
            self.state = GameState.MAIN_GAME
    
    notification_timer = 0
    notification_text = ""
    
    def show_notification(self, text):
        """Show a notification"""
        self.notification_text = text
        self.notification_timer = 180  # 3 seconds at 60 FPS
    
    def draw_notification(self):
        """Draw notification if active"""
        if self.notification_timer > 0:
            notification_rect = pygame.Rect(SCREEN_WIDTH - 420, 20, 400, 60)
            self.draw_gradient_rect(notification_rect.x, notification_rect.y,
                                   notification_rect.width, notification_rect.height,
                                   (102, 126, 234), (118, 75, 162))
            pygame.draw.rect(self.screen, WHITE, notification_rect, 3)
            
            text = self.font_small.render(self.notification_text, True, WHITE)
            self.screen.blit(text, (notification_rect.x + 20, notification_rect.centery - 10))
            
            self.notification_timer -= 1
    
    def run(self):
        """Main game loop"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if self.state == GameState.NAME_ENTRY:
                        if event.key == pygame.K_RETURN:
                            if self.input_text:
                                self.player.name = self.input_text
                                self.state = GameState.CHAR_CREATION
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        else:
                            if len(self.input_text) < 20:
                                self.input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        button_rects = []
                        
                        if self.state == GameState.TITLE:
                            button_rects = self.draw_title_screen()
                        elif self.state == GameState.CHAR_CREATION:
                            button_rects = self.draw_character_creation()
                        elif self.state == GameState.NAME_ENTRY:
                            button_rects = self.draw_name_entry()
                        elif self.state == GameState.SPECIES_SELECT:
                            button_rects = self.draw_species_select()
                        elif self.state == GameState.COLOR_SELECT:
                            button_rects = self.draw_color_select()
                        elif self.state == GameState.GUARDIAN_SELECT:
                            button_rects = self.draw_guardian_select()
                        elif self.state == GameState.MAIN_GAME:
                            button_rects = self.draw_main_game()
                        elif self.state == GameState.BATTLE:
                            button_rects = self.draw_battle_screen()
                        elif self.state == GameState.SHOP:
                            button_rects = self.draw_shop_screen()
                        elif self.state == GameState.PATCHES:
                            button_rects = self.draw_patches_screen()
                        
                        self.handle_click(event.pos, button_rects)
            
            # Clear screen
            self.screen.fill(WHITE)
            
            # Update animations
            self.animation_timer += 1
            self.star_animation += 0.05
            
            # Draw current screen
            if self.state == GameState.TITLE:
                self.draw_title_screen()
            elif self.state == GameState.CHAR_CREATION:
                self.draw_character_creation()
            elif self.state == GameState.NAME_ENTRY:
                self.draw_name_entry()
            elif self.state == GameState.SPECIES_SELECT:
                self.draw_species_select()
            elif self.state == GameState.COLOR_SELECT:
                self.draw_color_select()
            elif self.state == GameState.GUARDIAN_SELECT:
                self.draw_guardian_select()
            elif self.state == GameState.MAIN_GAME:
                self.draw_main_game()
            elif self.state == GameState.BATTLE:
                self.draw_battle_screen()
            elif self.state == GameState.SHOP:
                self.draw_shop_screen()
            elif self.state == GameState.PATCHES:
                self.draw_patches_screen()
            
            # Draw notification
            self.draw_notification()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = MarioLuigiLive()
    game.run()

import pygame
import math
import random
import sys
import numpy as np

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mario RPG Boss Battle")

# Colors
SKY_BLUE = (135, 206, 235)
GROUND_GREEN = (34, 139, 34)
RED = (255, 50, 50)
DARK_RED = (180, 0, 0)
BLUE = (30, 144, 255)
YELLOW = (255, 215, 0)
BROWN = (139, 69, 19)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
GREEN = (50, 205, 50)
DARK_GREEN = (0, 100, 0)
PURPLE = (128, 0, 128)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)
LIGHT_RED = (255, 99, 71)
DARK_BLUE = (0, 0, 139)

# Game variables
clock = pygame.time.Clock()
FPS = 60

# Procedural sound generation
def generate_sine_wave(frequency, duration, volume=0.5):
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    samples = np.zeros(num_samples, dtype=np.float32)
    
    for i in range(num_samples):
        samples[i] = volume * np.sin(2 * np.pi * frequency * i / sample_rate)
    
    return samples

def generate_beep(frequency=440, duration=0.1, volume=0.5):
    return pygame.mixer.Sound(buffer=generate_sine_wave(frequency, duration, volume))

def generate_hit_sound():
    samples = []
    for i in range(3):
        freq = random.randint(200, 400)
        duration = random.uniform(0.05, 0.1)
        samples.append(generate_sine_wave(freq, duration, 0.3))
    return pygame.mixer.Sound(buffer=np.concatenate(samples))

def generate_explosion_sound():
    samples = []
    for i in range(5):
        freq = random.randint(50, 200)
        duration = random.uniform(0.05, 0.15)
        samples.append(generate_sine_wave(freq, duration, 0.4))
    return pygame.mixer.Sound(buffer=np.concatenate(samples))

# Create sound effects
beep_sound = generate_beep()
select_sound = generate_beep(660, 0.1)
confirm_sound = generate_beep(880, 0.15)
jump_sound = generate_beep(330, 0.2)
fireball_sound = generate_beep(523, 0.1, 0.4)
hit_sound = generate_hit_sound()
big_hit_sound = generate_explosion_sound()
heal_sound = generate_beep(392, 0.3, 0.3)
victory_sound = generate_beep(784, 0.5)

# Font setup
font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 36)

# Player class
class Player:
    def __init__(self):
        self.max_hp = 100
        self.hp = self.max_hp
        self.status = "Normal"
        self.x = 150
        self.y = 400
        self.jump_height = 0
        self.jumping = False
        self.attack_animation = 0
        self.special_animation = 0
        self.hurt_animation = 0
        self.poison_timer = 0
        self.guard_active = False
        self.guard_timer = 0
        
    def draw(self):
        # Draw Mario
        body_color = RED
        overalls_color = BLUE
        skin_color = (255, 204, 153)
        hat_color = RED
        hair_color = (139, 69, 19)
        
        # Apply hurt animation
        offset = 0
        if self.hurt_animation > 0:
            offset = 3 * math.sin(self.hurt_animation * 10)
            self.hurt_animation -= 1
        
        # Apply jump offset
        y_offset = self.y - min(self.jump_height, 100)
        
        # Draw shadow
        pygame.draw.ellipse(screen, (50, 50, 50, 100), 
                           (self.x - 20, self.y + 40, 40, 10))
        
        # Draw body
        pygame.draw.circle(screen, skin_color, (self.x + offset, y_offset - 15), 15)  # Head
        pygame.draw.rect(screen, body_color, (self.x - 15 + offset, y_offset, 30, 30))  # Body
        pygame.draw.rect(screen, overalls_color, (self.x - 15 + offset, y_offset + 15, 30, 15))  # Overalls
        
        # Hat
        pygame.draw.rect(screen, hat_color, (self.x - 20 + offset, y_offset - 30, 40, 15))
        pygame.draw.circle(screen, hat_color, (self.x + offset, y_offset - 30), 15)
        
        # Eyes
        pygame.draw.circle(screen, WHITE, (self.x - 5 + offset, y_offset - 18), 4)
        pygame.draw.circle(screen, WHITE, (self.x + 5 + offset, y_offset - 18), 4)
        pygame.draw.circle(screen, BLACK, (self.x - 5 + offset, y_offset - 18), 2)
        pygame.draw.circle(screen, BLACK, (self.x + 5 + offset, y_offset - 18), 2)
        
        # Mustache
        pygame.draw.rect(screen, hair_color, (self.x - 10 + offset, y_offset - 10, 20, 5))
        
        # Arms
        pygame.draw.rect(screen, skin_color, (self.x - 20 + offset, y_offset + 10, 10, 15))
        pygame.draw.rect(screen, skin_color, (self.x + 10 + offset, y_offset + 10, 10, 15))
        
        # Legs
        pygame.draw.rect(screen, BLUE, (self.x - 15 + offset, y_offset + 30, 10, 15))
        pygame.draw.rect(screen, BLUE, (self.x + 5 + offset, y_offset + 30, 10, 15))
        
        # Attack animation
        if self.attack_animation > 0:
            pygame.draw.circle(screen, YELLOW, (self.x + 30 + offset, y_offset - 5), 10)
            self.attack_animation -= 1
            
        # Special animation
        if self.special_animation > 0:
            pygame.draw.circle(screen, ORANGE, (self.x + 30 + offset, y_offset - 15), 15)
            pygame.draw.circle(screen, RED, (self.x + 45 + offset, y_offset - 15), 10)
            self.special_animation -= 1
        
        # Guard effect
        if self.guard_active:
            pygame.draw.circle(screen, LIGHT_BLUE, (self.x + offset, y_offset), 40, 2)
            self.guard_timer -= 1
            if self.guard_timer <= 0:
                self.guard_active = False
    
    def jump(self):
        if not self.jumping:
            self.jumping = True
            jump_sound.play()
    
    def update(self):
        # Handle jumping
        if self.jumping:
            self.jump_height += 5
            if self.jump_height >= 100:
                self.jumping = False
        elif self.jump_height > 0:
            self.jump_height -= 5
        
        # Handle poison status
        if self.status == "Poisoned":
            self.poison_timer += 1
            if self.poison_timer >= 100:  # Poison damage every 100 frames
                self.take_damage(5)
                self.poison_timer = 0
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        self.hurt_animation = 10
        hit_sound.play()
    
    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        heal_sound.play()
    
    def guard(self):
        self.guard_active = True
        self.guard_timer = 30
    
    def apply_poison(self):
        self.status = "Poisoned"

# Boss class
class Boss:
    def __init__(self):
        self.max_hp = 300
        self.hp = self.max_hp
        self.x = 600
        self.y = 350
        self.attack_timer = 0
        self.attack_cooldown = 120  # 2 seconds at 60 FPS
        self.attack_type = "idle"
        self.attack_progress = 0
        self.hurt_animation = 0
        self.phase = 1
        self.bullets = []
        self.color = PURPLE
        self.eye_color = RED
        self.mouth_open = False
        self.mouth_timer = 0
        
    def draw(self):
        # Draw boss (King Goomba)
        body_color = self.color
        eye_color = self.eye_color
        crown_color = YELLOW
        
        # Apply hurt animation
        offset = 0
        if self.hurt_animation > 0:
            offset = 5 * math.sin(self.hurt_animation * 10)
            self.hurt_animation -= 1
        
        # Draw body
        pygame.draw.circle(screen, body_color, (self.x + offset, self.y), 60)
        
        # Draw eyes
        pygame.draw.circle(screen, WHITE, (self.x - 20 + offset, self.y - 10), 15)
        pygame.draw.circle(screen, WHITE, (self.x + 20 + offset, self.y - 10), 15)
        pygame.draw.circle(screen, eye_color, (self.x - 20 + offset, self.y - 10), 8)
        pygame.draw.circle(screen, eye_color, (self.x + 20 + offset, self.y - 10), 8)
        pygame.draw.circle(screen, BLACK, (self.x - 20 + offset, self.y - 10), 4)
        pygame.draw.circle(screen, BLACK, (self.x + 20 + offset, self.y - 10), 4)
        
        # Draw crown
        pygame.draw.rect(screen, crown_color, (self.x - 50 + offset, self.y - 80, 100, 20))
        pygame.draw.rect(screen, crown_color, (self.x - 60 + offset, self.y - 60, 120, 20))
        
        # Crown jewels
        pygame.draw.circle(screen, RED, (self.x - 40 + offset, self.y - 70), 6)
        pygame.draw.circle(screen, BLUE, (self.x + offset, self.y - 70), 8)
        pygame.draw.circle(screen, GREEN, (self.x + 40 + offset, self.y - 70), 6)
        
        # Draw mouth
        if self.mouth_open:
            pygame.draw.ellipse(screen, BLACK, (self.x - 25 + offset, self.y + 15, 50, 30))
            # Teeth
            for i in range(4):
                pygame.draw.rect(screen, WHITE, (self.x - 20 + i*15 + offset, self.y + 15, 8, 10))
        else:
            pygame.draw.arc(screen, BLACK, (self.x - 25 + offset, self.y + 5, 50, 30), 0, math.pi, 3)
        
        # Draw attack effects
        if self.attack_type == "fireball" and self.attack_progress > 0:
            for i in range(3):
                size = 15 - i*4
                pygame.draw.circle(screen, ORANGE, 
                                  (self.x - 60 + (self.attack_progress * 2) + offset, self.y + 20), 
                                  size)
        
        # Draw bullets
        for bullet in self.bullets:
            pygame.draw.circle(screen, RED, (bullet[0], bullet[1]), 8)
    
    def update(self):
        # Update attack timer
        self.attack_timer += 1
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet[0] -= 5
            if bullet[0] < -10:
                self.bullets.remove(bullet)
        
        # Update attack progress
        if self.attack_progress > 0:
            self.attack_progress -= 1
        
        # Update mouth animation
        self.mouth_timer += 1
        if self.mouth_timer >= 30:
            self.mouth_open = not self.mouth_open
            self.mouth_timer = 0
        
        # Phase transition
        if self.hp < self.max_hp * 0.5 and self.phase == 1:
            self.phase = 2
            self.color = DARK_RED
            self.eye_color = ORANGE
    
    def attack(self):
        if self.attack_timer >= self.attack_cooldown:
            self.attack_timer = 0
            attack_types = ["fireball", "bullet_hell"]
            
            if self.phase == 1:
                self.attack_type = random.choice(attack_types)
            else:
                self.attack_type = "bullet_hell"  # More aggressive in phase 2
            
            if self.attack_type == "fireball":
                self.attack_progress = 60
                fireball_sound.play()
                return "fireball"
            elif self.attack_type == "bullet_hell":
                # Create a spread of bullets
                for i in range(-2, 3):
                    self.bullets.append([self.x - 60, self.y + 20 + i * 30])
                big_hit_sound.play()
                return "bullet_hell"
        return None
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        self.hurt_animation = 10
        hit_sound.play()
    
    def reset_attack(self):
        self.attack_type = "idle"
        self.bullets = []

# Timing bar class
class TimingBar:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.progress = 0
        self.speed = 5
        self.active = False
        self.target_zone = 0
        self.target_width = 30
        self.result = 0
        
    def start(self):
        self.active = True
        self.progress = 0
        self.target_zone = random.randint(30, self.width - 30 - self.target_width)
        self.result = 0
        
    def update(self):
        if self.active:
            self.progress += self.speed
            if self.progress >= self.width:
                self.progress = 0
                
    def check_hit(self):
        if not self.active:
            return 0
            
        self.active = False
        if self.target_zone <= self.progress <= self.target_zone + self.target_width:
            self.result = 2  # Perfect
            return 2
        elif abs(self.progress - (self.target_zone + self.target_width/2)) < self.target_width:
            self.result = 1  # Good
            return 1
        return 0  # Miss
    
    def draw(self):
        if not self.active:
            return
            
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
        pygame.draw.rect(screen, LIGHT_GRAY, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, GREEN, (self.x + self.progress, self.y, 10, self.height))
        
        # Draw target zone
        pygame.draw.rect(screen, YELLOW, (self.x + self.target_zone, self.y, self.target_width, self.height))
        
        # Draw result
        if self.result > 0:
            result_text = "PERFECT!" if self.result == 2 else "Good!"
            text = big_font.render(result_text, True, YELLOW if self.result == 2 else GREEN)
            screen.blit(text, (self.x + self.width//2 - text.get_width()//2, self.y - 30))

# Battle UI class
class BattleUI:
    def __init__(self):
        self.menu_options = ["ATTACK", "SPECIAL", "ITEM", "DEFEND"]
        self.selected_option = 0
        self.active_menu = "main"
        self.item_options = ["MUSHROOM", "POISON SHROOM", "SUPER NUT"]
        self.selected_item = 0
        self.message = ""
        self.message_timer = 0
        self.message_duration = 120
        self.attack_timing = TimingBar(200, 500, 400, 30)
        self.dodge_active = False
        
    def draw(self, player, boss):
        # Draw player stats
        pygame.draw.rect(screen, LIGHT_GRAY, (20, 20, 200, 80))
        pygame.draw.rect(screen, BLACK, (20, 20, 200, 80), 2)
        
        # Draw player HP bar
        pygame.draw.rect(screen, RED, (40, 40, 160, 20))
        pygame.draw.rect(screen, GREEN, (40, 40, 160 * (player.hp / player.max_hp), 20))
        pygame.draw.rect(screen, BLACK, (40, 40, 160, 20), 2)
        
        # Draw player text
        name_text = font.render("MARIO", True, BLACK)
        hp_text = font.render(f"HP: {player.hp}/{player.max_hp}", True, BLACK)
        status_text = font.render(f"Status: {player.status}", True, 
                                RED if player.status == "Poisoned" else BLACK)
        
        screen.blit(name_text, (40, 25))
        screen.blit(hp_text, (40, 60))
        screen.blit(status_text, (120, 60))
        
        # Draw boss stats
        pygame.draw.rect(screen, LIGHT_GRAY, (580, 20, 200, 40))
        pygame.draw.rect(screen, BLACK, (580, 20, 200, 40), 2)
        
        # Draw boss HP bar
        pygame.draw.rect(screen, RED, (600, 30, 160, 20))
        pygame.draw.rect(screen, DARK_RED, (600, 30, 160 * (boss.hp / boss.max_hp), 20))
        pygame.draw.rect(screen, BLACK, (600, 30, 160, 20), 2)
        
        # Draw boss text
        name_text = font.render("KING GOOMBA", True, BLACK)
        screen.blit(name_text, (600, 25))
        
        # Draw action menu
        if self.active_menu == "main":
            pygame.draw.rect(screen, LIGHT_GRAY, (20, 450, 300, 120))
            pygame.draw.rect(screen, BLACK, (20, 450, 300, 120), 2)
            
            for i, option in enumerate(self.menu_options):
                color = BLUE if i == self.selected_option else BLACK
                option_text = font.render(option, True, color)
                screen.blit(option_text, (40, 470 + i * 25))
                
        elif self.active_menu == "item":
            pygame.draw.rect(screen, LIGHT_GRAY, (20, 450, 300, 120))
            pygame.draw.rect(screen, BLACK, (20, 450, 300, 120), 2)
            
            for i, item in enumerate(self.item_options):
                color = BLUE if i == self.selected_item else BLACK
                item_text = font.render(item, True, color)
                screen.blit(item_text, (40, 470 + i * 25))
        
        # Draw dodge area
        if self.dodge_active:
            pygame.draw.rect(screen, LIGHT_BLUE, (150, 300, 500, 150), 2)
        
        # Draw message box
        if self.message:
            pygame.draw.rect(screen, LIGHT_GRAY, (200, 400, 400, 50))
            pygame.draw.rect(screen, BLACK, (200, 400, 400, 50), 2)
            message_text = font.render(self.message, True, BLACK)
            screen.blit(message_text, (210, 415))
            
        # Draw timing bar if active
        self.attack_timing.draw()
    
    def show_message(self, text):
        self.message = text
        self.message_timer = self.message_duration
    
    def update(self):
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.message = ""
        
        # Update timing bar
        self.attack_timing.update()

# Game states
class GameState:
    PLAYER_TURN = 0
    PLAYER_ATTACK = 1
    PLAYER_SPECIAL = 2
    PLAYER_ITEM = 3
    PLAYER_DEFEND = 4
    BOSS_TURN = 5
    BOSS_ATTACK = 6
    PLAYER_DODGE = 7
    VICTORY = 8
    GAME_OVER = 9

# Main game class
class Game:
    def __init__(self):
        self.player = Player()
        self.boss = Boss()
        self.ui = BattleUI()
        self.state = GameState.PLAYER_TURN
        self.dialogue = [
            "KING GOOMBA: You dare challenge me?!",
            "MARIO: Let's-a go!",
            "KING GOOMBA: Prepare to be squashed!"
        ]
        self.dialogue_index = 0
        self.dialogue_active = True
        self.dodge_x = 400
        self.dodge_y = 375
        self.victory_timer = 0
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                # Dialogue advancing
                if self.dialogue_active:
                    if event.key == pygame.K_RETURN:
                        self.dialogue_index += 1
                        if self.dialogue_index >= len(self.dialogue):
                            self.dialogue_active = False
                        beep_sound.play()
                    return
                
                # Victory or Game Over screen
                if self.state == GameState.VICTORY or self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self.__init__()  # Restart game
                    return
                
                # Player turn menu
                if self.state == GameState.PLAYER_TURN:
                    if event.key == pygame.K_DOWN:
                        self.ui.selected_option = (self.ui.selected_option + 1) % len(self.ui.menu_options)
                        beep_sound.play()
                    elif event.key == pygame.K_UP:
                        self.ui.selected_option = (self.ui.selected_option - 1) % len(self.ui.menu_options)
                        beep_sound.play()
                    elif event.key == pygame.K_RETURN:
                        if self.ui.active_menu == "main":
                            if self.ui.selected_option == 0:  # Attack
                                self.ui.attack_timing.start()
                                self.state = GameState.PLAYER_ATTACK
                            elif self.ui.selected_option == 1:  # Special
                                self.ui.attack_timing.start()
                                self.state = GameState.PLAYER_SPECIAL
                            elif self.ui.selected_option == 2:  # Item
                                self.ui.active_menu = "item"
                                beep_sound.play()
                            elif self.ui.selected_option == 3:  # Defend
                                self.player.guard()
                                self.ui.show_message("Mario braces for impact!")
                                self.state = GameState.BOSS_TURN
                                confirm_sound.play()
                        elif self.ui.active_menu == "item":
                            if self.ui.selected_item == 0:  # Mushroom
                                self.player.heal(30)
                                self.ui.show_message("Mario healed 30 HP!")
                                self.state = GameState.BOSS_TURN
                                confirm_sound.play()
                            elif self.ui.selected_item == 1:  # Poison Shroom
                                self.boss.apply_poison()
                                self.ui.show_message("King Goomba is poisoned!")
                                self.state = GameState.BOSS_TURN
                                confirm_sound.play()
                            elif self.ui.selected_item == 2:  # Super Nut
                                self.player.heal(15)
                                self.player.guard()
                                self.ui.show_message("Mario healed and braced for impact!")
                                self.state = GameState.BOSS_TURN
                                confirm_sound.play()
                            self.ui.active_menu = "main"
                    elif event.key == pygame.K_ESCAPE and self.ui.active_menu == "item":
                        self.ui.active_menu = "main"
                        beep_sound.play()
                
                # Attack timing minigame
                elif self.state in [GameState.PLAYER_ATTACK, GameState.PLAYER_SPECIAL]:
                    if event.key == pygame.K_SPACE:
                        result = self.ui.attack_timing.check_hit()
                        if self.state == GameState.PLAYER_ATTACK:
                            damage = 0
                            if result == 2:  # Perfect
                                damage = 40
                                self.player.attack_animation = 20
                                self.ui.show_message("Perfect hit! 40 damage!")
                            elif result == 1:  # Good
                                damage = 25
                                self.player.attack_animation = 20
                                self.ui.show_message("Good hit! 25 damage!")
                            else:
                                self.ui.show_message("Missed!")
                            
                            if damage > 0:
                                self.boss.take_damage(damage)
                            
                            self.state = GameState.BOSS_TURN
                        else:  # Special attack
                            if result >= 1:  # Good or perfect
                                self.player.special_animation = 30
                                damage = 50 if result == 2 else 35
                                self.boss.take_damage(damage)
                                self.ui.show_message(f"Fireball! {damage} damage!")
                            else:
                                self.ui.show_message("Special attack failed!")
                            
                            self.state = GameState.BOSS_TURN
                        confirm_sound.play()
                
                # Dodge minigame
                elif self.state == GameState.PLAYER_DODGE:
                    if event.key == pygame.K_LEFT:
                        self.dodge_x = max(150, self.dodge_x - 20)
                    elif event.key == pygame.K_RIGHT:
                        self.dodge_x = min(650, self.dodge_x + 20)
                    elif event.key == pygame.K_UP:
                        self.dodge_y = max(300, self.dodge_y - 20)
                    elif event.key == pygame.K_DOWN:
                        self.dodge_y = min(450, self.dodge_y + 20)
    
    def update(self):
        self.player.update()
        self.boss.update()
        self.ui.update()
        
        # Check if boss is defeated
        if self.boss.hp <= 0 and self.state not in [GameState.VICTORY, GameState.GAME_OVER]:
            self.state = GameState.VICTORY
            victory_sound.play()
        
        # Check if player is defeated
        if self.player.hp <= 0 and self.state not in [GameState.VICTORY, GameState.GAME_OVER]:
            self.state = GameState.GAME_OVER
        
        # Victory timer
        if self.state == GameState.VICTORY:
            self.victory_timer += 1
        
        # Boss turn logic
        if self.state == GameState.BOSS_TURN:
            attack = self.boss.attack()
            if attack:
                if attack == "fireball":
                    self.ui.show_message("King Goomba shoots fireballs!")
                    self.state = GameState.BOSS_ATTACK
                elif attack == "bullet_hell":
                    self.ui.show_message("King Goomba unleashes bullet hell!")
                    self.ui.dodge_active = True
                    self.state = GameState.PLAYER_DODGE
        
        # Boss attack logic
        if self.state == GameState.BOSS_ATTACK:
            if self.boss.attack_progress <= 0:
                damage = 25
                if self.player.guard_active:
                    damage = max(5, damage - 15)
                    self.ui.show_message("Mario guarded! Reduced damage!")
                
                self.player.take_damage(damage)
                self.state = GameState.PLAYER_TURN
                self.boss.reset_attack()
        
        # Dodge minigame logic
        if self.state == GameState.PLAYER_DODGE:
            # Check for bullet collisions
            hit = False
            for bullet in self.boss.bullets[:]:
                # Simple collision detection
                if (abs(bullet[0] - self.dodge_x) < 20 and 
                    abs(bullet[1] - self.dodge_y) < 20):
                    self.boss.bullets.remove(bullet)
                    hit = True
            
            if hit:
                damage = 15
                if self.player.guard_active:
                    damage = max(5, damage - 10)
                    self.ui.show_message("Mario guarded! Reduced damage!")
                
                self.player.take_damage(damage)
            
            # End dodge minigame if all bullets are gone
            if not self.boss.bullets:
                self.ui.dodge_active = False
                self.state = GameState.PLAYER_TURN
                self.boss.reset_attack()
    
    def draw(self):
        # Draw sky background
        screen.fill(SKY_BLUE)
        
        # Draw clouds
        for i in range(3):
            x = (i * 300 + pygame.time.get_ticks() // 50) % 900 - 100
            pygame.draw.ellipse(screen, WHITE, (x, 80, 100, 50))
            pygame.draw.ellipse(screen, WHITE, (x + 30, 60, 80, 50))
            pygame.draw.ellipse(screen, WHITE, (x + 60, 80, 100, 50))
        
        # Draw ground
        pygame.draw.rect(screen, GROUND_GREEN, (0, 500, SCREEN_WIDTH, 100))
        
        # Draw decorative elements
        for i in range(10):
            pygame.draw.rect(screen, DARK_GREEN, (i * 80, 500, 40, 20))
        
        # Draw battle platform
        pygame.draw.rect(screen, BROWN, (100, 350, 600, 20))
        pygame.draw.rect(screen, (160, 82, 45), (100, 350, 600, 20), 2)
        
        # Draw player and boss
        self.player.draw()
        self.boss.draw()
        
        # Draw UI
        self.ui.draw(self.player, self.boss)
        
        # Draw dialogue box
        if self.dialogue_active:
            pygame.draw.rect(screen, LIGHT_GRAY, (50, 450, 700, 120))
            pygame.draw.rect(screen, BLACK, (50, 450, 700, 120), 3)
            
            dialogue_text = font.render(self.dialogue[self.dialogue_index], True, BLACK)
            screen.blit(dialogue_text, (70, 480))
            
            prompt_text = font.render("Press ENTER to continue", True, BLUE)
            screen.blit(prompt_text, (70, 520))
        
        # Draw dodge character
        if self.state == GameState.PLAYER_DODGE:
            pygame.draw.circle(screen, RED, (self.dodge_x, self.dodge_y), 15)
            pygame.draw.circle(screen, BLUE, (self.dodge_x, self.dodge_y), 10)
        
        # Draw victory screen
        if self.state == GameState.VICTORY:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            victory_text = big_font.render("VICTORY!", True, YELLOW)
            screen.blit(victory_text, (SCREEN_WIDTH//2 - victory_text.get_width()//2, 200))
            
            message = "King Goomba has been defeated!"
            message_text = font.render(message, True, WHITE)
            screen.blit(message_text, (SCREEN_WIDTH//2 - message_text.get_width()//2, 250))
            
            prompt = "Press ENTER to play again"
            prompt_text = font.render(prompt, True, GREEN)
            screen.blit(prompt_text, (SCREEN_WIDTH//2 - prompt_text.get_width()//2, 350))
            
            # Draw animated stars
            t = pygame.time.get_ticks() // 10
            for i in range(5):
                size = 20 + 5 * math.sin(t/100 + i)
                x = 200 + i * 100
                y = 400 + 20 * math.sin(t/50 + i)
                pygame.draw.polygon(screen, YELLOW, [
                    (x, y - size),
                    (x + size * 0.4, y - size * 0.4),
                    (x + size, y),
                    (x + size * 0.4, y + size * 0.4),
                    (x, y + size),
                    (x - size * 0.4, y + size * 0.4),
                    (x - size, y),
                    (x - size * 0.4, y - size * 0.4)
                ])
        
        # Draw game over screen
        if self.state == GameState.GAME_OVER:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            game_over_text = big_font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 200))
            
            message = "Mario has been defeated..."
            message_text = font.render(message, True, WHITE)
            screen.blit(message_text, (SCREEN_WIDTH//2 - message_text.get_width()//2, 250))
            
            prompt = "Press ENTER to try again"
            prompt_text = font.render(prompt, True, GREEN)
            screen.blit(prompt_text, (SCREEN_WIDTH//2 - prompt_text.get_width()//2, 350))
        
        pygame.display.flip()
    
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)

# Start the game
if __name__ == "__main__":
    game = Game()
    game.run()

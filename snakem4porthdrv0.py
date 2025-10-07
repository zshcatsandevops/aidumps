import pygame
import random
import array

# FLAMES OS INITIALIZATION - RAW MODE ENABLED
pygame.init()

# VIBRANT COLORS FOR RETRO VISION
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# SCREEN SETUP FOR OG RETRO SCALE
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NEO SNAKE - ULTIMATE MODE")

clock = pygame.time.Clock()
font = pygame.font.SysFont('consolas', 24)

# SNAKE ENGINE - CLASSIC TEMPO
class Snake:
    def __init__(self):
        self.positions = [(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)]
        self.length = 1
        self.directions = 'RIGHT'
        self.color = GREEN
        self.speed = 15
        self.grow = False
        
    def update(self):
        head = self.positions[0]
        x, y = head
        
        if self.directions == 'RIGHT':
            x += 20
        elif self.directions == 'LEFT':
            x -= 20
        elif self.directions == 'UP':
            y -= 20
        elif self.directions == 'DOWN':
            y += 20
            
        new_positions = [(x, y)]
        new_positions.extend(self.positions)
        
        if not self.grow:
            new_positions.pop()
        else:
            self.grow = False
            
        self.positions = new_positions
        
    def change_direction(self, direction):
        if direction == 'RIGHT' and self.directions != 'LEFT':
            self.directions = 'RIGHT'
        elif direction == 'LEFT' and self.directions != 'RIGHT':
            self.directions = 'LEFT'
        elif direction == 'UP' and self.directions != 'DOWN':
            self.directions = 'UP'
        elif direction == 'DOWN' and self.directions != 'UP':
            self.directions = 'DOWN'

    def grow_snake(self):
        self.grow = True
        
    def draw(self, surface):
        for i, pos in enumerate(self.positions):
            pygame.draw.rect(surface, self.color, (pos[0], pos[1], 20, 20))
            if i == 0:  # HEAD HIGHLIGHT
                pygame.draw.rect(surface, RED, (pos[0], pos[1], 20, 20))
                # DIRECTIONAL EYE
                if self.directions == 'RIGHT':
                    eye_x = pos[0] + 12
                    eye_y = pos[1] + 5
                elif self.directions == 'LEFT':
                    eye_x = pos[0] + 2
                    eye_y = pos[1] + 5
                elif self.directions == 'UP':
                    eye_x = pos[0] + 5
                    eye_y = pos[1] + 2
                else:  # DOWN
                    eye_x = pos[0] + 5
                    eye_y = pos[1] + 12
                pygame.draw.rect(surface, BLACK, (eye_x, eye_y, 3, 3))

# FOOD ENGINE - SPICY TASTE SIMULATION
class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = (255, 0, 0)
        self.is_food = True
        self.generate_new_food()
        
    def generate_new_food(self):
        x = random.randrange(1, (SCREEN_WIDTH//20))
        y = random.randrange(1, (SCREEN_HEIGHT//20))
        self.position = (x*20, y*20)
        
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.position[0], self.position[1], 20, 20))

# NES-LIKE PALETTE GRID
def draw_grid(surface):
    for x in range(0, SCREEN_WIDTH, 20):
        pygame.draw.line(surface, (40, 40, 40), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 20):
        pygame.draw.line(surface, (40, 40, 40), (0, y), (0 + SCREEN_WIDTH, y))

# SOUND ENGINE - NES MOCK-UP
class SoundEngine:
    def __init__(self):
        self.channel = pygame.mixer.Channel(0)
        
    def play_food_collect(self):
        # SHORT BEEP ONLY WHEN FOOD IS COLLECTED
        sample_rate = 22050
        frames = int(sample_rate * 0.1)  # SHORT BEEP
        arr = array.array('h')  # SIGNED SHORT FOR AUDIO BUFFER
        for i in range(frames):
            # BASIC SQUARE WAVE AT 440Hz
            phase = (i * 440) / sample_rate
            value = 32767 if (phase % 1) < 0.5 else -32767
            arr.append(value)
        sample = pygame.mixer.Sound(buffer=arr.tobytes())
        self.channel.play(sample)

# INTEGRATED GAME SYSTEM
class Game:
    def __init__(self):
        self.snake = Snake()
        self.food = Food()
        self.sound_engine = SoundEngine()
        
    def update(self):
        self.snake.update()
        
    def draw(self, surface):
        surface.fill(BLACK)
        draw_grid(surface)
        self.food.draw(surface)
        self.snake.draw(surface)
        
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        self.snake.change_direction('RIGHT')
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction('LEFT')
                    elif event.key == pygame.K_UP:
                        self.snake.change_direction('UP')
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction('DOWN')
                        
            self.update()
            
            # FOOD COLLISION CHECK
            if self.snake.positions[0] == self.food.position:
                self.snake.grow_snake()
                self.food.generate_new_food()
                self.sound_engine.play_food_collect()  # BEEP ONLY ON FOOD COLLECT
                
            # SELF COLLISION CHECK
            if self.snake.positions[0] in self.snake.positions[1:]:
                print("GAME OVER - Snake bit itself!")
                running = False
                
            # BOUNDARY CHECK
            x, y = self.snake.positions[0]
            if not (0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT):
                print("GAME OVER - Escape Failed")
                running = False
                
            self.draw(screen)
            pygame.display.flip()
            clock.tick(self.snake.speed)
            
        pygame.quit()

# ACTIVATE THE CORE
if __name__ == '__main__':
    game = Game()
    game.run()

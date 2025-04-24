import pygame
import sys
import threading
import socket
import random

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
CHAT_HEIGHT = 200
ZONE_COLORS = [(30,30,60), (60,30,60), (30,60,30)]
BLACK = (0,0,0)
WHITE = (255,255,255)

# --- Networking ---
BROADCAST_IP = '255.255.255.255'
PORT = 50007
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setblocking(False)

# --- Game State ---
chat_input = ''
messages = []
friend_requests = set()
ZONE_UNLOCK_THRESHOLD = 2
unlocked_zones = 1
running = True

# --- Pygame Setup ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Sonic & Knuckles & Facebook')
clock = pygame.time.Clock()
chat_font = pygame.font.SysFont('Consolas', 20)
input_font = pygame.font.SysFont('Consolas', 24)

# --- Player/Enemy Classes ---
class Player:
    def __init__(self):
        self.x = WIDTH//2
        self.y = HEIGHT//2
        self.color = (0,200,255)
        self.radius = 30
    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (self.x, self.y), self.radius)
    def rhythm_battle(self):
        messages.append('You performed a rhythm attack!')

class Enemy:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 25
    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (self.x, self.y), self.radius)

player = Player()
enemies = [Enemy(200, 200, (255,0,0)), Enemy(600, 400, (0,255,0))]

# --- Networking Thread ---
def listen():
    global running
    while running:
        try:
            data, _ = sock.recvfrom(1024)
            msg = data.decode()
            messages.append(msg)
        except Exception:
            pass
listener = threading.Thread(target=listen, daemon=True)
listener.start()

# --- Main Loop ---
while running:
    dt = clock.tick(FPS)
    screen.fill(ZONE_COLORS[unlocked_zones-1])
    player.draw(screen)
    for e in enemies:
        e.draw(screen)
    pygame.draw.rect(screen, BLACK, (0, HEIGHT-CHAT_HEIGHT, WIDTH, CHAT_HEIGHT))
    for i, msg in enumerate(messages[-8:]):
        txt = chat_font.render(msg, True, WHITE)
        screen.blit(txt, (5, HEIGHT-CHAT_HEIGHT + 5 + i*22))
    pygame.draw.rect(screen, WHITE, (0, HEIGHT-30, WIDTH, 30))
    in_txt = input_font.render(chat_input, True, BLACK)
    screen.blit(in_txt, (5, HEIGHT-28))
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                msg = f"You: {chat_input}"
                messages.append(msg)
                try:
                    sock.sendto(msg.encode(), (BROADCAST_IP, PORT))
                except Exception:
                    pass
                if chat_input.startswith('friend_request '):
                    dev = chat_input.split(' ',1)[1]
                    friend_requests.add(dev)
                    messages.append(f"Friend request sent to {dev}")
                    if len(friend_requests) >= ZONE_UNLOCK_THRESHOLD and unlocked_zones < len(ZONE_COLORS):
                        unlocked_zones += 1
                        messages.append(f"Zone {unlocked_zones} unlocked!")
                chat_input = ''
            elif event.key == pygame.K_BACKSPACE:
                chat_input = chat_input[:-1]
            elif event.key == pygame.K_SPACE:
                player.rhythm_battle()
            elif event.key < 256:
                chat_input += event.unicode

running = False
pygame.quit()
sys.exit()

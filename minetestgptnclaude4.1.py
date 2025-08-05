import pygame
import math
import random
from enum import Enum
import numpy as np

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# World settings
WORLD_SIZE = 32
CHUNK_HEIGHT = 16
RENDER_DISTANCE = 20

# Block types
class BlockType(Enum):
    AIR = 0
    GRASS = 1
    DIRT = 2
    STONE = 3
    WOOD = 4
    LEAVES = 5
    SAND = 6
    WATER = 7
    BEDROCK = 8
    COAL = 9
    IRON = 10
    DIAMOND = 11

# Block colors
BLOCK_COLORS = {
    BlockType.AIR: None,
    BlockType.GRASS: [(34, 139, 34), (46, 125, 50), (60, 110, 40)],
    BlockType.DIRT: [(139, 69, 19), (120, 60, 15), (100, 50, 10)],
    BlockType.STONE: [(128, 128, 128), (105, 105, 105), (80, 80, 80)],
    BlockType.WOOD: [(101, 67, 33), (83, 53, 25), (65, 40, 15)],
    BlockType.LEAVES: [(0, 128, 0), (0, 100, 0), (0, 80, 0)],
    BlockType.SAND: [(238, 203, 173), (220, 185, 155), (200, 165, 135)],
    BlockType.WATER: [(64, 164, 223), (54, 144, 203), (44, 124, 183)],
    BlockType.BEDROCK: [(50, 50, 50), (30, 30, 30), (20, 20, 20)],
    BlockType.COAL: [(40, 40, 40), (25, 25, 25), (15, 15, 15)],
    BlockType.IRON: [(176, 176, 176), (156, 156, 156), (136, 136, 136)],
    BlockType.DIAMOND: [(185, 242, 255), (165, 222, 235), (145, 202, 215)]
}

class World:
    def __init__(self):
        self.blocks = {}
        self.generate_terrain()
        
    def generate_terrain(self):
        # Generate basic terrain with Perlin-like noise
        for x in range(-WORLD_SIZE, WORLD_SIZE):
            for z in range(-WORLD_SIZE, WORLD_SIZE):
                # Simple height generation
                height = int(8 + 4 * math.sin(x * 0.1) * math.cos(z * 0.1) + random.randint(-1, 1))
                
                # Place bedrock at bottom
                self.blocks[(x, 0, z)] = BlockType.BEDROCK
                
                # Fill with stone and dirt
                for y in range(1, height - 2):
                    if y < 4 and random.random() < 0.1:
                        self.blocks[(x, y, z)] = BlockType.DIAMOND
                    elif y < 6 and random.random() < 0.2:
                        self.blocks[(x, y, z)] = BlockType.IRON
                    elif random.random() < 0.15:
                        self.blocks[(x, y, z)] = BlockType.COAL
                    else:
                        self.blocks[(x, y, z)] = BlockType.STONE
                
                # Top layers
                if height > 2:
                    self.blocks[(x, height - 2, z)] = BlockType.DIRT
                    self.blocks[(x, height - 1, z)] = BlockType.GRASS
                
                # Add trees randomly
                if random.random() < 0.02 and height > 8:
                    self.generate_tree(x, height, z)
    
    def generate_tree(self, x, y, z):
        # Tree trunk
        for h in range(4):
            self.blocks[(x, y + h, z)] = BlockType.WOOD
        
        # Leaves
        for dx in range(-2, 3):
            for dy in range(2, 5):
                for dz in range(-2, 3):
                    if abs(dx) + abs(dz) <= 3:
                        pos = (x + dx, y + dy, z + dz)
                        if pos not in self.blocks or self.blocks[pos] == BlockType.AIR:
                            self.blocks[pos] = BlockType.LEAVES
    
    def get_block(self, x, y, z):
        return self.blocks.get((x, y, z), BlockType.AIR)
    
    def set_block(self, x, y, z, block_type):
        if block_type == BlockType.AIR:
            if (x, y, z) in self.blocks:
                del self.blocks[(x, y, z)]
        else:
            self.blocks[(x, y, z)] = block_type
    
    def break_block(self, x, y, z):
        if (x, y, z) in self.blocks and self.blocks[(x, y, z)] != BlockType.BEDROCK:
            del self.blocks[(x, y, z)]
            return True
        return False

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 15
        self.z = 0
        self.yaw = 45  # Isometric angle
        self.pitch = 30
        self.zoom = 20
        
    def move(self, dx, dy, dz):
        self.x += dx
        self.y += dy
        self.z += dz
        
    def rotate(self, dyaw, dpitch):
        self.yaw += dyaw
        self.pitch = max(-60, min(60, self.pitch + dpitch))
    
    def project(self, x, y, z):
        # Relative position to camera
        rx = x - self.x
        ry = y - self.y
        rz = z - self.z
        
        # Rotate around Y axis (yaw)
        yaw_rad = math.radians(self.yaw)
        x_rot = rx * math.cos(yaw_rad) - rz * math.sin(yaw_rad)
        z_rot = rx * math.sin(yaw_rad) + rz * math.cos(yaw_rad)
        
        # Rotate around X axis (pitch)
        pitch_rad = math.radians(self.pitch)
        y_rot = ry * math.cos(pitch_rad) - z_rot * math.sin(pitch_rad)
        z_final = ry * math.sin(pitch_rad) + z_rot * math.cos(pitch_rad)
        
        # Project to 2D
        if z_final < 1:
            return None
            
        screen_x = SCREEN_WIDTH // 2 + (x_rot * self.zoom)
        screen_y = SCREEN_HEIGHT // 2 - (y_rot * self.zoom)
        
        return (int(screen_x), int(screen_y), z_final)

class Player:
    def __init__(self, world):
        self.world = world
        self.x = 0
        self.y = 20
        self.z = 0
        self.vx = 0
        self.vy = 0
        self.vz = 0
        self.on_ground = False
        self.selected_block = BlockType.STONE
        self.inventory = {
            BlockType.GRASS: 999,
            BlockType.DIRT: 999,
            BlockType.STONE: 999,
            BlockType.WOOD: 999,
            BlockType.LEAVES: 999,
            BlockType.SAND: 999,
            BlockType.COAL: 999,
            BlockType.IRON: 999,
            BlockType.DIAMOND: 999
        }
        
    def update(self, dt):
        # Apply gravity
        if not self.on_ground:
            self.vy -= 20 * dt
        
        # Move with collision detection
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        
        # Ground collision
        ground_y = self.find_ground(int(self.x), int(self.z))
        if self.y <= ground_y + 1:
            self.y = ground_y + 1
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False
        
        # Friction
        self.vx *= 0.8
        self.vz *= 0.8
    
    def find_ground(self, x, z):
        for y in range(CHUNK_HEIGHT, -1, -1):
            if self.world.get_block(x, y, z) != BlockType.AIR:
                return y + 1
        return 0
    
    def jump(self):
        if self.on_ground:
            self.vy = 8
            self.on_ground = False
    
    def move(self, dx, dz):
        speed = 5
        self.vx += dx * speed
        self.vz += dz * speed

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Minecraft Bedrock - Pygame Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 36)
        
        self.world = World()
        self.camera = Camera()
        self.player = Player(self.world)
        self.running = True
        self.show_help = True
        self.block_preview = None
        self.creative_mode = True
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.player.jump()
                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_1:
                    self.player.selected_block = BlockType.GRASS
                elif event.key == pygame.K_2:
                    self.player.selected_block = BlockType.DIRT
                elif event.key == pygame.K_3:
                    self.player.selected_block = BlockType.STONE
                elif event.key == pygame.K_4:
                    self.player.selected_block = BlockType.WOOD
                elif event.key == pygame.K_5:
                    self.player.selected_block = BlockType.LEAVES
                elif event.key == pygame.K_6:
                    self.player.selected_block = BlockType.SAND
                elif event.key == pygame.K_7:
                    self.player.selected_block = BlockType.COAL
                elif event.key == pygame.K_8:
                    self.player.selected_block = BlockType.IRON
                elif event.key == pygame.K_9:
                    self.player.selected_block = BlockType.DIAMOND
                elif event.key == pygame.K_c:
                    self.creative_mode = not self.creative_mode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click - break block
                    self.break_block_at_cursor()
                elif event.button == 3:  # Right click - place block
                    self.place_block_at_cursor()
                elif event.button == 4:  # Scroll up
                    self.camera.zoom = min(50, self.camera.zoom + 2)
                elif event.button == 5:  # Scroll down
                    self.camera.zoom = max(10, self.camera.zoom - 2)
        
        # Handle continuous key presses
        keys = pygame.key.get_pressed()
        
        # Player movement
        dx, dz = 0, 0
        if keys[pygame.K_w]:
            dz = -1
        if keys[pygame.K_s]:
            dz = 1
        if keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_d]:
            dx = 1
        
        if dx != 0 or dz != 0:
            # Rotate movement based on camera angle
            angle = math.radians(self.camera.yaw)
            new_dx = dx * math.cos(angle) - dz * math.sin(angle)
            new_dz = dx * math.sin(angle) + dz * math.cos(angle)
            self.player.move(new_dx, new_dz)
        
        # Camera rotation
        if keys[pygame.K_q]:
            self.camera.rotate(-2, 0)
        if keys[pygame.K_e]:
            self.camera.rotate(2, 0)
        if keys[pygame.K_r]:
            self.camera.rotate(0, 2)
        if keys[pygame.K_f]:
            self.camera.rotate(0, -2)
        
        # Flying in creative mode
        if self.creative_mode:
            if keys[pygame.K_LSHIFT]:
                self.player.y -= 0.3
            if keys[pygame.K_LCTRL]:
                self.player.y += 0.3
    
    def get_block_at_cursor(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Ray casting to find block
        best_block = None
        best_dist = float('inf')
        
        for pos, block_type in self.world.blocks.items():
            if block_type == BlockType.AIR:
                continue
                
            proj = self.camera.project(pos[0], pos[1], pos[2])
            if proj:
                screen_x, screen_y, depth = proj
                dist = math.sqrt((screen_x - mouse_x)**2 + (screen_y - mouse_y)**2)
                
                if dist < 30 and depth < best_dist:  # Within selection radius
                    best_dist = depth
                    best_block = pos
        
        return best_block
    
    def break_block_at_cursor(self):
        block_pos = self.get_block_at_cursor()
        if block_pos:
            self.world.break_block(*block_pos)
    
    def place_block_at_cursor(self):
        # Find empty position near cursor
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Calculate world position from screen
        # Simplified placement - find nearest empty spot
        base_block = self.get_block_at_cursor()
        if base_block:
            # Try to place on top of selected block
            x, y, z = base_block
            if self.world.get_block(x, y + 1, z) == BlockType.AIR:
                self.world.set_block(x, y + 1, z, self.player.selected_block)
    
    def render_block(self, x, y, z, block_type):
        if block_type == BlockType.AIR:
            return
            
        colors = BLOCK_COLORS[block_type]
        if not colors:
            return
        
        # Project block vertices
        size = 0.5
        vertices = [
            (x - size, y - size, z - size),
            (x + size, y - size, z - size),
            (x + size, y + size, z - size),
            (x - size, y + size, z - size),
            (x - size, y - size, z + size),
            (x + size, y - size, z + size),
            (x + size, y + size, z + size),
            (x - size, y + size, z + size),
        ]
        
        projected = []
        for v in vertices:
            p = self.camera.project(v[0], v[1], v[2])
            if p:
                projected.append(p)
        
        if len(projected) < 8:
            return
        
        # Draw faces (simplified - only visible faces)
        faces = [
            (0, 1, 2, 3, colors[0]),  # Front
            (5, 4, 7, 6, colors[1]),  # Back
            (3, 2, 6, 7, colors[2]),  # Top
        ]
        
        for face in faces:
            points = []
            for i in range(4):
                if face[i] < len(projected):
                    points.append((projected[face[i]][0], projected[face[i]][1]))
            
            if len(points) == 4:
                # Clamp color values to [0,255]
                color = tuple(max(0, min(255, c)) for c in face[4])
                border_color = tuple(max(0, min(255, c - 20)) for c in face[4])
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, border_color, points, 2)
    
    def render(self):
        # Clear screen with sky color
        sky_color = (135, 206, 235)
        self.screen.fill(sky_color)
        
        # Update camera to follow player
        self.camera.x = self.player.x
        self.camera.y = self.player.y + 5
        self.camera.z = self.player.z + 10
        
        # Render blocks (sorted by distance for proper depth)
        blocks_to_render = []
        for pos, block_type in self.world.blocks.items():
            dist = math.sqrt((pos[0] - self.camera.x)**2 + 
                           (pos[1] - self.camera.y)**2 + 
                           (pos[2] - self.camera.z)**2)
            if dist < RENDER_DISTANCE:
                blocks_to_render.append((dist, pos, block_type))
        
        # Sort by distance (far to near)
        blocks_to_render.sort(reverse=True)
        
        # Render blocks
        for _, pos, block_type in blocks_to_render:
            self.render_block(pos[0], pos[1], pos[2], block_type)
        
        # Render player
        player_proj = self.camera.project(self.player.x, self.player.y, self.player.z)
        if player_proj:
            pygame.draw.circle(self.screen, (255, 0, 0), (player_proj[0], player_proj[1]), 8)
            pygame.draw.circle(self.screen, (200, 0, 0), (player_proj[0], player_proj[1]), 8, 2)
        
        # Highlight block under cursor
        highlighted = self.get_block_at_cursor()
        if highlighted:
            proj = self.camera.project(highlighted[0], highlighted[1], highlighted[2])
            if proj:
                pygame.draw.circle(self.screen, (255, 255, 0), (proj[0], proj[1]), 5)
        
        # Draw crosshair
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        pygame.draw.line(self.screen, (255, 255, 255), (cx - 10, cy), (cx + 10, cy), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (cx, cy - 10), (cx, cy + 10), 2)
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        # Draw hotbar
        hotbar_y = SCREEN_HEIGHT - 80
        hotbar_blocks = [
            (BlockType.GRASS, "1"),
            (BlockType.DIRT, "2"),
            (BlockType.STONE, "3"),
            (BlockType.WOOD, "4"),
            (BlockType.LEAVES, "5"),
            (BlockType.SAND, "6"),
            (BlockType.COAL, "7"),
            (BlockType.IRON, "8"),
            (BlockType.DIAMOND, "9"),
        ]
        
        for i, (block_type, key) in enumerate(hotbar_blocks):
            x = SCREEN_WIDTH // 2 - 225 + i * 50
            
            # Draw slot
            color = (100, 100, 100)
            if block_type == self.player.selected_block:
                color = (255, 255, 255)
            pygame.draw.rect(self.screen, color, (x, hotbar_y, 45, 45), 3)
            
            # Draw block color
            if BLOCK_COLORS[block_type]:
                pygame.draw.rect(self.screen, BLOCK_COLORS[block_type][0], 
                               (x + 5, hotbar_y + 5, 35, 35))
            
            # Draw key
            text = self.font.render(key, True, (255, 255, 255))
            self.screen.blit(text, (x + 5, hotbar_y - 20))
        
        # Draw info
        info_texts = [
            f"Pos: ({int(self.player.x)}, {int(self.player.y)}, {int(self.player.z)})",
            f"Mode: {'Creative' if self.creative_mode else 'Survival'}",
            f"Selected: {self.player.selected_block.name}",
            f"FPS: {int(self.clock.get_fps())}"
        ]
        
        for i, text in enumerate(info_texts):
            surface = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (10, 10 + i * 25))
        
        # Draw help
        if self.show_help:
            help_texts = [
                "MINECRAFT BEDROCK - PYGAME EDITION",
                "",
                "Controls:",
                "WASD - Move",
                "Space - Jump",
                "Mouse - Look around",
                "Left Click - Break block",
                "Right Click - Place block",
                "Q/E - Rotate camera",
                "R/F - Tilt camera",
                "Scroll - Zoom",
                "1-9 - Select block",
                "C - Toggle Creative mode",
                "H - Toggle this help",
                "ESC - Quit"
            ]
            
            # Draw semi-transparent background
            overlay = pygame.Surface((400, len(help_texts) * 25 + 20))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (SCREEN_WIDTH // 2 - 200, 100))
            
            for i, text in enumerate(help_texts):
                if i == 0:
                    surface = self.large_font.render(text, True, (255, 255, 0))
                    self.screen.blit(surface, (SCREEN_WIDTH // 2 - 180, 110 + i * 25))
                else:
                    surface = self.font.render(text, True, (255, 255, 255))
                    self.screen.blit(surface, (SCREEN_WIDTH // 2 - 180, 110 + i * 25))
    
    def run(self):
        dt = 0
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.player.update(dt)
            self.render()
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()

import pygame
import random
import math
import heapq # Added for A* priority queue

# --- Constants ---
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
PINK = (255, 182, 193)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128) # For ghost house door

# Screen dimensions
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 30
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE  # 600
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE + 70 # 600 for game + 70 for UI

# Entity properties
PACMAN_RADIUS = CELL_SIZE // 2 - 2
PACMAN_SPEED = 2.5 # Cells per second
GHOST_RADIUS = CELL_SIZE // 2 - 2
GHOST_SPEED = 2.0 # Cells per second
GHOST_FRIGHTENED_SPEED = 1.5
GHOST_EATEN_SPEED = 4.0
PELLET_RADIUS = 3
POWER_PELLET_RADIUS = 6

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
STOP = (0,0)

# Ghost modes
SCATTER = 0
CHASE = 1
FRIGHTENED = 2
EATEN = 3

# Ghost Types (for easier indexing and color mapping)
BLINKY = 0 # Red
PINKY = 1  # Pink
INKY = 2   # Cyan
CLYDE = 3  # Orange

GHOST_COLORS = {
    BLINKY: RED,
    PINKY: PINK,
    INKY: CYAN,
    CLYDE: ORANGE
}

DEFAULT_MAZE = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,3,1],
    [1,2,1,1,1,2,1,1,1,2,1,1,2,1,1,2,1,1,2,1,1,1,2,1,1,1,1,1,2,1],
    [1,3,1,1,1,2,1,1,1,2,1,1,2,1,1,2,1,1,2,1,1,1,2,1,1,1,1,1,3,1],
    [1,2,1,1,1,2,1,1,1,2,1,1,2,1,1,2,1,1,2,1,1,1,2,1,1,1,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,2,1],
    [1,2,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,1,1,2,2,1,1,2,2,1,1,2,2,2,2,2,2,2,2,2,2,1],
    [1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1],
    [1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1], # Row 10
    [1,1,1,1,1,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,1,1,1,1,1,1,1],
    [1,1,1,1,1,2,1,1,2,1,1,1,4,4,4,4,1,1,2,1,1,2,1,1,1,1,1,1,1,1], # Ghost house top boundary (4 is wall to pacman)
    [1,0,0,0,0,2,2,2,2,1,4,0,0,0,0,0,0,4,1,2,2,2,2,0,0,0,0,0,0,1], # Tunnel row, ghost house main area (0 is path, 4 is ghost only)
    [1,1,1,1,1,2,1,1,2,1,4,0,0,0,0,0,0,4,1,2,1,1,2,1,1,1,1,1,1,1], # Ghost house bottom boundary
    [1,1,1,1,1,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,1,1,1,1,1,1,1], # Row 15 (mirror of 11)
    [1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1], # (mirror of 10)
    [1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1], # (mirror of 9)
    [1,2,2,2,2,2,2,2,2,1,1,2,2,1,1,2,2,1,1,2,2,2,2,2,2,2,2,2,2,1], # (mirror of 8)
    [1,2,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,2,1], # (mirror of 7)
    [1,2,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,1,1,2,1], # Row 20 (mirror of 6)
    [1,2,2,2,2,2,2,2,2,2,2,2,2,5,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1], # Pacman Start (5), (mirror of 5 with P)
    [1,2,1,1,1,2,1,1,1,2,1,1,2,1,1,2,1,1,2,1,1,1,2,1,1,1,1,1,2,1], # (mirror of 4)
    [1,3,1,1,1,2,1,1,1,2,1,1,2,1,1,2,1,1,2,1,1,1,2,1,1,1,1,1,3,1], # (mirror of 3)
    [1,2,1,1,1,2,1,1,1,2,1,1,2,1,1,2,1,1,2,1,1,1,2,1,1,1,1,1,2,1], # (mirror of 2)
    [1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,3,1], # Row 25 (mirror of 1)
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]
MAZE_ARRAY_HEIGHT = len(DEFAULT_MAZE)
MAZE_ARRAY_WIDTH = len(DEFAULT_MAZE[0])


# --- Helper Functions ---
def to_pixel(grid_pos):
    return (grid_pos[0] * CELL_SIZE + CELL_SIZE // 2, grid_pos[1] * CELL_SIZE + CELL_SIZE // 2)

def to_grid(pixel_pos):
    return (int(pixel_pos[0] / CELL_SIZE), int(pixel_pos[1] / CELL_SIZE))

def manhattan_distance(pos1, pos2):
    if pos1 is None or pos2 is None: return float('inf')
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

# --- Entity Classes ---
class Entity:
    def __init__(self, game, grid_pos, color, radius, speed):
        self.game = game
        self.grid_pos = list(grid_pos) # Current grid cell (col, row)
        self.pixel_pos = list(to_pixel(grid_pos)) # Center pixel position
        self.color = color
        self.radius = radius
        self.speed_val = speed # Grid cells per second
        self.direction = STOP
        self.next_direction = STOP # For Pacman queued movement

    def get_rect(self):
        return pygame.Rect(self.pixel_pos[0] - self.radius, self.pixel_pos[1] - self.radius,
                           self.radius * 2, self.radius * 2)

    def is_wall(self, grid_pos, for_ghost=False):
        col, row = int(grid_pos[0]), int(grid_pos[1])
        if not (0 <= col < MAZE_ARRAY_WIDTH and 0 <= row < MAZE_ARRAY_HEIGHT):
            return True

        cell_type = self.game.maze[row][col]
        if cell_type == 1: return True
        if not for_ghost and cell_type == 4: return True
        return False

    def is_at_grid_center(self, tolerance=1.0):
        target_pixel_center = to_pixel(self.grid_pos)
        dist_to_center = math.hypot(self.pixel_pos[0] - target_pixel_center[0],
                                    self.pixel_pos[1] - target_pixel_center[1])
        return dist_to_center < tolerance

    def move(self, dt):
        move_dist = self.current_speed() * CELL_SIZE * dt

        if self.is_at_grid_center():
            # Snap to center before making decision for new cell
            self.pixel_pos = list(to_pixel(self.grid_pos))

            current_intended_direction = self.direction
            if hasattr(self, 'next_direction') and self.next_direction != STOP: # Pacman specific
                next_tile_for_queued_dir = (self.grid_pos[0] + self.next_direction[0], self.grid_pos[1] + self.next_direction[1])
                if not self.is_wall(next_tile_for_queued_dir, isinstance(self, Ghost)):
                    self.direction = self.next_direction
                    self.next_direction = STOP
                # If queued is not valid, try current direction (persists if current is valid)
                # else: self.direction might become STOP if current is also blocked

            # Check if current direction (or newly set direction for Pacman) is valid from current grid_pos
            potential_next_grid_pos = (self.grid_pos[0] + self.direction[0], self.grid_pos[1] + self.direction[1])

            if self.direction == STOP or self.is_wall(potential_next_grid_pos, isinstance(self, Ghost)):
                # If chosen direction is STOP or leads to a wall, try to revert to original direction if that was valid
                # This helps ghosts not get stuck if their AI briefly chose a wall due to target alignment
                if hasattr(self, 'next_direction') and self.direction != current_intended_direction and current_intended_direction != STOP:
                    original_potential_next_grid_pos = (self.grid_pos[0] + current_intended_direction[0], self.grid_pos[1] + current_intended_direction[1])
                    if not self.is_wall(original_potential_next_grid_pos, isinstance(self, Ghost)):
                        self.direction = current_intended_direction
                        potential_next_grid_pos = original_potential_next_grid_pos # re-evaluate
                    else:
                        self.direction = STOP # Cannot move
                else:
                     self.direction = STOP # Cannot move

            # Update grid_pos if successfully chose a new cell to move into
            if self.direction != STOP: # and not self.is_wall(potential_next_grid_pos...): # Already checked
                 self.grid_pos[0] = int(round(self.grid_pos[0] + self.direction[0]))
                 self.grid_pos[1] = int(round(self.grid_pos[1] + self.direction[1]))
                 self.handle_tunnels()

        # Actual pixel movement towards the center of the *new* self.grid_pos
        if self.direction != STOP:
            target_pixel_pos = to_pixel(self.grid_pos)
            angle = math.atan2(target_pixel_pos[1] - self.pixel_pos[1], target_pixel_pos[0] - self.pixel_pos[0])

            self.pixel_pos[0] += math.cos(angle) * move_dist
            self.pixel_pos[1] += math.sin(angle) * move_dist

            # Snap if overshot or very close to the target center
            new_target_pixel_pos = to_pixel(self.grid_pos)
            dist_to_new_target = math.hypot(new_target_pixel_pos[0] - self.pixel_pos[0], new_target_pixel_pos[1] - self.pixel_pos[1])

            if dist_to_new_target < move_dist * 0.6 : # Heuristic for snapping or if passed
                # Check if moved past target
                dot_product_x = self.direction[0] * (new_target_pixel_pos[0] - self.pixel_pos[0])
                dot_product_y = self.direction[1] * (new_target_pixel_pos[1] - self.pixel_pos[1])

                if (self.direction[0] != 0 and dot_product_x < 0) or \
                   (self.direction[1] != 0 and dot_product_y < 0) or \
                   dist_to_new_target < 1.0 : # Very close
                    self.pixel_pos = list(new_target_pixel_pos)

    def handle_tunnels(self):
        if self.grid_pos[1] == 13:
            if self.grid_pos[0] < 0 and self.direction == LEFT:
                self.grid_pos[0] = MAZE_ARRAY_WIDTH -1
                self.pixel_pos[0] = to_pixel(self.grid_pos)[0] + CELL_SIZE # Emerge from other side fully
            elif self.grid_pos[0] >= MAZE_ARRAY_WIDTH and self.direction == RIGHT:
                self.grid_pos[0] = 0
                self.pixel_pos[0] = to_pixel(self.grid_pos)[0] - CELL_SIZE # Emerge from other side fully

    def current_speed(self):
        return self.speed_val

class Pacman(Entity):
    def __init__(self, game, grid_pos):
        super().__init__(game, grid_pos, YELLOW, PACMAN_RADIUS, PACMAN_SPEED)
        self.lives = 3
        self.score = 0
        self.mouth_angle = 0
        self.mouth_open = True
        self.mouth_timer = 0
        self.start_pos = list(grid_pos)
        self.ai_controlled = False # MEOW! Set False for player control

    def handle_input(self, event):
        if self.ai_controlled: return # AI is driving, nya~
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a: self.next_direction = LEFT      # Changed K_LEFT to K_a
            elif event.key == pygame.K_d: self.next_direction = RIGHT   # Changed K_RIGHT to K_d
            elif event.key == pygame.K_w: self.next_direction = UP      # Changed K_UP to K_w
            elif event.key == pygame.K_s: self.next_direction = DOWN    # Changed K_DOWN to K_s

    def update(self, dt):
        if self.ai_controlled:
            if self.is_at_grid_center(): # Make decision only at center of cell
                ai_decision = self.game.pacman_ai_decide_next_move()
                if ai_decision != STOP:
                    self.next_direction = ai_decision

        self.move(dt)
        self.mouth_timer += dt
        if self.mouth_timer > 0.1:
            self.mouth_open = not self.mouth_open
            self.mouth_timer = 0
        self.mouth_angle = 30 if self.mouth_open and self.direction != STOP else 0

        if self.is_at_grid_center(tolerance=CELL_SIZE*0.4): # Check for pellets when reasonably centered
             self.check_pellet_collision()


    def check_pellet_collision(self):
        center_grid_x, center_grid_y = int(round(self.grid_pos[0])), int(round(self.grid_pos[1]))

        for i, pellet_pos in enumerate(self.game.pellets):
            if pellet_pos == (center_grid_x, center_grid_y):
                self.game.pellets.pop(i)
                self.score += 10
                self.game.eaten_pellets_count +=1
                break

        for i, pp_pos in enumerate(self.game.power_pellets):
            if pp_pos == (center_grid_x, center_grid_y):
                self.game.power_pellets.pop(i)
                self.score += 50
                self.game.eaten_pellets_count +=1
                self.game.start_fright_mode()
                break

    def draw(self, screen):
        if self.lives < 0: return

        angle_rad = 0
        if self.direction == RIGHT: angle_rad = 0
        elif self.direction == LEFT: angle_rad = math.pi
        elif self.direction == UP: angle_rad = math.pi / 2
        elif self.direction == DOWN: angle_rad = -math.pi / 2

        pygame.draw.circle(screen, self.color, (int(self.pixel_pos[0]), int(self.pixel_pos[1])), self.radius)

        if self.direction != STOP and self.mouth_angle > 0:
            p1 = self.pixel_pos
            p2_offset_x = self.radius * math.cos(angle_rad + math.radians(self.mouth_angle))
            p2_offset_y = self.radius * math.sin(angle_rad + math.radians(self.mouth_angle))
            p2 = (self.pixel_pos[0] + p2_offset_x, self.pixel_pos[1] + p2_offset_y)

            p3_offset_x = self.radius * math.cos(angle_rad - math.radians(self.mouth_angle))
            p3_offset_y = self.radius * math.sin(angle_rad - math.radians(self.mouth_angle))
            p3 = (self.pixel_pos[0] + p3_offset_x, self.pixel_pos[1] + p3_offset_y)

            pygame.draw.polygon(screen, BLACK, [p1, p2, p3])

    def reset(self):
        self.grid_pos = list(self.start_pos)
        self.pixel_pos = list(to_pixel(self.start_pos))
        self.direction = STOP
        self.next_direction = STOP


class Ghost(Entity):
    def __init__(self, game, grid_pos, ghost_type):
        super().__init__(game, grid_pos, GHOST_COLORS[ghost_type], GHOST_RADIUS, GHOST_SPEED)
        self.type = ghost_type
        self.state = SCATTER
        self.target_pos = None
        self.scatter_target = self.get_scatter_target()
        self.start_pos = list(grid_pos)
        self.is_in_house = True
        self.exit_house_pos = (14, 11) # Grid position outside ghost house door (col, row)
        self.released_from_house = False
        self.is_forced_out = False # For Blinky or early release
        self.release_pellet_count = 0 # Set by Game class
        self.is_aiming_for_spawn_in_house = False # For EATEN state return trip

    def get_scatter_target(self):
        if self.type == BLINKY: return (MAZE_ARRAY_WIDTH - 2, 1)
        if self.type == PINKY: return (1, 1)
        if self.type == INKY: return (MAZE_ARRAY_WIDTH - 2, MAZE_ARRAY_HEIGHT - 2)
        if self.type == CLYDE: return (1, MAZE_ARRAY_HEIGHT - 2)
        return (self.grid_pos[0], self.grid_pos[1])

    def current_speed(self):
        if self.state == FRIGHTENED: return GHOST_FRIGHTENED_SPEED
        if self.state == EATEN: return GHOST_EATEN_SPEED
        if self.is_in_house and self.target_pos == self.exit_house_pos: # Slower when navigating house exit
            return self.speed_val * 0.8
        return self.speed_val

    def update_release_status(self):
        if self.is_in_house and not self.released_from_house:
            if self.is_forced_out or self.game.eaten_pellets_count >= self.release_pellet_count:
                self.target_pos = self.exit_house_pos

                if self.grid_pos[0] == self.exit_house_pos[0] and self.grid_pos[1] == self.exit_house_pos[1]:
                    self.is_in_house = False
                    self.released_from_house = True
                    self.is_aiming_for_spawn_in_house = False # Ensure this is reset
                    self.pixel_pos = list(to_pixel(self.exit_house_pos)) # Snap to exit pos center
                    # Try to move out immediately if possible
                    if self.target_pos == self.exit_house_pos: # No longer targeting exit, find new target
                        self.target_pos = None
                    if self.state not in [FRIGHTENED, EATEN]: # Ensure correct mode upon exiting
                        self.state = self.game.current_ghost_mode

    def update(self, dt, pacman, blinky_ref=None):
        if self.is_in_house:
            self.update_release_status()
            if self.is_in_house: # Still in house (or re-entering when eaten)
                if self.state == EATEN: # Logic for re-entering house when eaten
                    if self.is_aiming_for_spawn_in_house:
                        self.target_pos = self.start_pos
                        if self.grid_pos[0] == self.start_pos[0] and self.grid_pos[1] == self.start_pos[1]:
                            # Reached spawn point
                            self.state = self.game.current_ghost_mode # Or SCATTER
                            self.released_from_house = False # Must earn exit again
                            if self.type != BLINKY: self.is_forced_out = False
                            self.is_aiming_for_spawn_in_house = False
                            # Speed reset by current_speed based on new state
                    else: # Just reached door, now aim for spawn
                        self.target_pos = self.start_pos
                        self.is_aiming_for_spawn_in_house = True
                else: # Not eaten, trying to exit
                     self.target_pos = self.exit_house_pos
            # If update_release_status set is_in_house to False, normal AI targetting will kick in below

        if not self.is_in_house: # Normal operations or just exited
            self.update_target(pacman, blinky_ref)

        if self.is_at_grid_center(): # Make move decision only at grid center
            self.make_move_decision()
        self.move(dt)

    def update_target(self, pacman, blinky_ref=None):
        if self.state == EATEN:
            # If outside, target house entrance. If at entrance, target spawn.
            if not self.is_aiming_for_spawn_in_house:
                 self.target_pos = self.exit_house_pos # Aim for the tile just outside the house door
                 if self.grid_pos[0] == self.exit_house_pos[0] and self.grid_pos[1] == self.exit_house_pos[1]:
                     self.is_in_house = True # Considered "in house" logic once at door to re-enter
                     self.is_aiming_for_spawn_in_house = True
                     self.target_pos = self.start_pos # Now aim for actual spawn point
            # If is_aiming_for_spawn_in_house is true, target is already start_pos (handled in main update)
            return # Eaten state target logic is mostly handled in the main update's is_in_house block

        elif self.state == FRIGHTENED:
            self.target_pos = None # Random movement handled in make_move_decision
        elif self.state == SCATTER:
            self.target_pos = self.scatter_target
        elif self.state == CHASE:
            pacman_gx, pacman_gy = int(round(pacman.grid_pos[0])), int(round(pacman.grid_pos[1]))
            pacman_dx, pacman_dy = pacman.direction

            if self.type == BLINKY:
                self.target_pos = (pacman_gx, pacman_gy)
            elif self.type == PINKY:
                target_x, target_y = pacman_gx + pacman_dx * 4, pacman_gy + pacman_dy * 4
                if pacman_dx == 0 and pacman_dy == UP[1]: # Pacman moving UP (original arcade bug)
                    target_x, target_y = pacman_gx - 4, pacman_gy - 4
                self.target_pos = (target_x, target_y)
            elif self.type == INKY:
                if blinky_ref and not blinky_ref.is_in_house: # Inky needs Blinky on the field
                    blinky_gx, blinky_gy = int(round(blinky_ref.grid_pos[0])), int(round(blinky_ref.grid_pos[1]))

                    offset_x, offset_y = pacman_gx + pacman_dx * 2, pacman_gy + pacman_dy * 2
                    if pacman_dx == 0 and pacman_dy == UP[1]: # Pacman moving UP (Inky's offset bug)
                         offset_x, offset_y = pacman_gx - 2, pacman_gy - 2

                    # Vector from Blinky to offset, then double it from offset
                    # Target = Offset + (Offset - BlinkyPos) = 2 * Offset - BlinkyPos
                    self.target_pos = (2 * offset_x - blinky_gx, 2 * offset_y - blinky_gy)
                else: # Fallback if Blinky is eaten or not available
                    self.target_pos = (pacman_gx, pacman_gy) # Behave like Blinky
            elif self.type == CLYDE:
                dist_to_pacman = manhattan_distance(self.grid_pos, pacman.grid_pos)
                if dist_to_pacman > 8:
                    self.target_pos = (pacman_gx, pacman_gy)
                else:
                    self.target_pos = self.scatter_target

    def make_move_decision(self):
        # This should only be called if self.is_at_grid_center() is true
        possible_directions = []
        for d_candidate in [UP, DOWN, LEFT, RIGHT]:
            # Ghosts cannot reverse direction unless forced (e.g. dead end or mode change)
            if self.direction != STOP and (d_candidate[0] == -self.direction[0] and d_candidate[1] == -self.direction[1]):
                continue

            next_pos = (self.grid_pos[0] + d_candidate[0], self.grid_pos[1] + d_candidate[1])
            if not self.is_wall(next_pos, for_ghost=True):
                possible_directions.append(d_candidate)

        if not possible_directions: # Should only happen if only option is to reverse
            if self.direction != STOP: # Check if there is a direction to reverse
                reversed_dir = (-self.direction[0], -self.direction[1])
                next_pos_reversed = (self.grid_pos[0] + reversed_dir[0], self.grid_pos[1] + reversed_dir[1])
                if not self.is_wall(next_pos_reversed, for_ghost=True):
                     self.direction = reversed_dir
                else: # Truly stuck (shouldn't happen in standard mazes)
                     self.direction = STOP
            else: # No current direction and no possible moves (e.g. spawned in a wall)
                self.direction = STOP
            return

        if self.state == FRIGHTENED:
            self.direction = random.choice(possible_directions)
        else:
            best_direction = self.direction
            min_dist = float('inf')

            if len(possible_directions) == 1:
                 best_direction = possible_directions[0]
            elif self.target_pos: # Ensure there is a target
                # Tie-breaking order: UP, LEFT, DOWN, RIGHT (classic Pac-Man behavior)
                ordered_choices = []
                for d_choice in [UP, LEFT, DOWN, RIGHT]:
                    if d_choice in possible_directions:
                        next_node = (self.grid_pos[0] + d_choice[0], self.grid_pos[1] + d_choice[1])
                        dist = manhattan_distance(next_node, self.target_pos)
                        ordered_choices.append({'dir': d_choice, 'dist': dist})

                if ordered_choices:
                    ordered_choices.sort(key=lambda x: x['dist'])
                    best_direction = ordered_choices[0]['dir']
            elif not possible_directions: # Should be caught earlier
                self.direction = STOP # Should not happen if logic above is correct
            else: # No target_pos, but possible directions (e.g. scatter target not set yet)
                self.direction = random.choice(possible_directions) # Default to random valid move

            self.direction = best_direction


    def draw(self, screen):
        body_color = self.color
        eye_color = WHITE
        pupil_color = BLACK

        if self.state == FRIGHTENED:
            body_color = BLUE
            if self.game.fright_timer < 2000 and int(self.game.fright_timer / 250) % 2 == 0:
                body_color = WHITE
        elif self.state == EATEN:
            body_color = None
            eye_color = WHITE
            pupil_color = BLUE

        if body_color:
            pygame.draw.circle(screen, body_color, (int(self.pixel_pos[0]), int(self.pixel_pos[1])), self.radius)

        eye_offset_x = self.radius * 0.3
        eye_offset_y = -self.radius * 0.2
        eye_radius = self.radius * 0.25
        pupil_radius = eye_radius * 0.5

        pupil_shift_x = 0
        pupil_shift_y = 0
        if self.direction == LEFT: pupil_shift_x = -pupil_radius * 0.5
        if self.direction == RIGHT: pupil_shift_x = pupil_radius * 0.5
        if self.direction == UP: pupil_shift_y = -pupil_radius * 0.5
        if self.direction == DOWN: pupil_shift_y = pupil_radius * 0.5

        left_eye_pos = (int(self.pixel_pos[0] - eye_offset_x), int(self.pixel_pos[1] + eye_offset_y))
        pygame.draw.circle(screen, eye_color, left_eye_pos, eye_radius)
        pygame.draw.circle(screen, pupil_color, (int(left_eye_pos[0] + pupil_shift_x), int(left_eye_pos[1] + pupil_shift_y)), pupil_radius)

        right_eye_pos = (int(self.pixel_pos[0] + eye_offset_x), int(self.pixel_pos[1] + eye_offset_y))
        pygame.draw.circle(screen, eye_color, right_eye_pos, eye_radius)
        pygame.draw.circle(screen, pupil_color, (int(right_eye_pos[0] + pupil_shift_x), int(right_eye_pos[1] + pupil_shift_y)), pupil_radius)

    def reverse_direction(self):
        if self.direction != STOP:
            reversed_dir = (-self.direction[0], -self.direction[1])
            # Check if reversing is valid (not into a wall)
            # This check is important if called when not at a dead end
            next_pos_if_reversed = (self.grid_pos[0] + reversed_dir[0], self.grid_pos[1] + reversed_dir[1])
            if not self.is_wall(next_pos_if_reversed, for_ghost=True):
                self.direction = reversed_dir
            # If reversing is into a wall, make_move_decision will handle finding a new path next frame.
            # Snapping pixel_pos isn't strictly necessary here as move() will handle it.

    def reset(self):
        self.grid_pos = list(self.start_pos)
        self.pixel_pos = list(to_pixel(self.start_pos))
        self.state = SCATTER
        self.direction = STOP
        self.is_in_house = True
        self.released_from_house = False
        self.is_aiming_for_spawn_in_house = False
        if self.type == BLINKY: # Blinky specific reset for release
            self.is_forced_out = True
            # self.released_from_house = True # Or let update_release_status handle it
            # self.is_in_house = False # If Blinky starts outside house
        else:
            self.is_forced_out = False
        self.target_pos = self.exit_house_pos # Initial aim for exit when in house

# --- A* Pathfinding ---
def a_star_pathfind(start_pos_tuple, end_pos_tuple, game, entity_for_wall_check):
    start_pos = tuple(map(int, start_pos_tuple))
    end_pos = tuple(map(int, end_pos_tuple))

    open_set = []
    heapq.heappush(open_set, (0, start_pos))

    came_from = {}
    g_score = {start_pos: 0}
    f_score = {start_pos: manhattan_distance(start_pos, end_pos)}

    # Keep track of items in open_set for faster "is in open_set" check
    open_set_tracker = {start_pos}


    while open_set:
        _, current = heapq.heappop(open_set)
        open_set_tracker.remove(current)

        if current == end_pos:
            return reconstruct_path(came_from, current)

        for dx, dy in [UP, DOWN, LEFT, RIGHT]: # Order can matter for tie-breaking in some A* visualisations
            neighbor = (current[0] + dx, current[1] + dy)

            if not (0 <= neighbor[0] < MAZE_ARRAY_WIDTH and 0 <= neighbor[1] < MAZE_ARRAY_HEIGHT):
                continue

            is_ghost = isinstance(entity_for_wall_check, Ghost)
            if entity_for_wall_check.is_wall(neighbor, for_ghost=is_ghost):
                continue

            tentative_g_score = g_score[current] + 1

            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + manhattan_distance(neighbor, end_pos)
                if neighbor not in open_set_tracker:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    open_set_tracker.add(neighbor)
    return None

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]

# --- Game Class ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-Man AI Adventure, Meow!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.maze = DEFAULT_MAZE
        self.pellets = []
        self.power_pellets = []
        self.pacman_start_pos = None
        self.ghost_start_positions = {}

        self.total_pellets_in_level = 0
        self.eaten_pellets_count = 0

        self.populate_maze_elements()

        self.pacman = Pacman(self, self.pacman_start_pos)
        self.ghosts = self.create_ghosts()
        self.blinky_ref = self.ghosts[BLINKY] # Store ref for Inky

        self.game_state = "START"
        self.fright_timer = 0
        self.fright_duration = 7000

        self.scatter_chase_timer = 0
        self.scatter_chase_pattern = [
            (7000, SCATTER), (20000, CHASE),
            (7000, SCATTER), (20000, CHASE),
            (5000, SCATTER), (20000, CHASE),
            (5000, SCATTER), (-1, CHASE)
        ]
        self.current_scatter_chase_index = 0
        self.current_ghost_mode = SCATTER

        self.death_timer = 0
        self.death_duration = 2000

    def populate_maze_elements(self):
        base_ghost_positions = [(13,13), (14,13), (15,13), (16,13)]

        for r, row_data in enumerate(self.maze):
            for c, cell_type in enumerate(row_data):
                if cell_type == 2:
                    self.pellets.append((c, r))
                    self.total_pellets_in_level += 1
                elif cell_type == 3:
                    self.power_pellets.append((c, r))
                    self.total_pellets_in_level += 1
                elif cell_type == 5:
                    self.pacman_start_pos = (c, r)

        self.ghost_start_positions[BLINKY] = base_ghost_positions[0]
        self.ghost_start_positions[PINKY]  = base_ghost_positions[1]
        self.ghost_start_positions[INKY]   = base_ghost_positions[2]
        self.ghost_start_positions[CLYDE]  = base_ghost_positions[3]


    def create_ghosts(self):
        ghost_list = [None] * 4 # Ensure order for BLINKY, PINKY, etc.
        total_dots = self.total_pellets_in_level

        for ghost_type_val in range(4): # BLINKY, PINKY, INKY, CLYDE
             actual_start_pos = self.ghost_start_positions[ghost_type_val]
             ghost = Ghost(self, actual_start_pos, ghost_type_val)

             if ghost_type_val == BLINKY:
                 ghost.is_forced_out = True
                 ghost.release_pellet_count = 0
                 # Blinky might even start outside the house in some versions.
                 # For this, we make him exit immediately.
                 # ghost.is_in_house = False
                 # ghost.released_from_house = True
             elif ghost_type_val == PINKY:
                 ghost.release_pellet_count = 1
             elif ghost_type_val == INKY:
                 ghost.release_pellet_count = max(1, min(30, total_dots // 8 if total_dots > 0 else 30))
             elif ghost_type_val == CLYDE:
                 ghost.release_pellet_count = max(1, min(60, total_dots // 3 if total_dots > 0 else 60))

             ghost_list[ghost_type_val] = ghost
        return ghost_list

    def reset_level(self):
        self.pacman.reset()
        for ghost in self.ghosts:
            ghost.reset()

        self.fright_timer = 0
        self.scatter_chase_timer = 0
        self.current_scatter_chase_index = 0
        self.current_ghost_mode = self.scatter_chase_pattern[0][1]
        for ghost in self.ghosts:
            if ghost.state not in [FRIGHTENED, EATEN]: # Avoid overriding eaten state if reset mid-return
                 ghost.state = self.current_ghost_mode
            # Ensure reset() correctly puts them in house and targeting exit
        self.game_state = "START"

    def full_game_reset(self):
        self.pacman.lives = 3
        self.pacman.score = 0
        self.pellets = []
        self.power_pellets = []
        self.total_pellets_in_level = 0
        self.eaten_pellets_count = 0
        self.populate_maze_elements()
        # Re-create ghosts to reset their release counts relative to new total_pellets
        self.ghosts = self.create_ghosts()
        self.blinky_ref = self.ghosts[BLINKY]
        self.reset_level() # This will call pacman.reset() and ghost.reset()
        self.game_state = "START"


    def run(self):
        running = True
        while running:
            dt_ms = self.clock.tick(60)
            dt_s = dt_ms / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_input(event)

            self.update(dt_s, dt_ms)
            self.render()

        pygame.quit()

    def handle_input(self, event):
        if self.game_state == "START":
            if event.type == pygame.KEYDOWN:
                self.game_state = "PLAYING"
                # Initial ghost mode already set by reset_level or init
        elif self.game_state == "PLAYING":
            self.pacman.handle_input(event) # Pacman input is now handled here
        elif self.game_state == "GAME_OVER" or self.game_state == "WIN":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.full_game_reset()


    def update(self, dt_s, dt_ms):
        if self.game_state == "PLAYING":
            self.pacman.update(dt_s) # Pacman updates based on its internal state (AI or player)

            self.scatter_chase_timer += dt_ms
            duration, mode = self.scatter_chase_pattern[self.current_scatter_chase_index]

            if duration != -1 and self.scatter_chase_timer >= duration:
                self.scatter_chase_timer = 0
                self.current_scatter_chase_index = min(self.current_scatter_chase_index + 1, len(self.scatter_chase_pattern) - 1)
                _, new_mode = self.scatter_chase_pattern[self.current_scatter_chase_index]

                if self.current_ghost_mode != new_mode: # Mode changed
                    self.current_ghost_mode = new_mode
                    for ghost in self.ghosts:
                        if ghost.state not in [FRIGHTENED, EATEN] and not ghost.is_in_house: # Don't reverse if in house
                            ghost.state = self.current_ghost_mode
                            if not ghost.is_in_house: # Reverse only if outside house
                                ghost.reverse_direction()


            for ghost in self.ghosts:
                ghost.update(dt_s, self.pacman, self.blinky_ref)

            self.check_collisions()

            if self.fright_timer > 0:
                self.fright_timer -= dt_ms
                if self.fright_timer <= 0:
                    self.end_fright_mode()

            if self.eaten_pellets_count >= self.total_pellets_in_level and self.total_pellets_in_level > 0:
                self.game_state = "WIN"

        elif self.game_state == "PACMAN_DEATH":
            self.death_timer += dt_ms
            if self.death_timer >= self.death_duration:
                self.death_timer = 0
                self.pacman.lives -= 1
                if self.pacman.lives < 0:
                    self.game_state = "GAME_OVER"
                else:
                    self.reset_level()
                    self.game_state = "START"


    def check_collisions(self):
        pacman_rect = self.pacman.get_rect()
        for ghost in self.ghosts:
            if ghost.is_in_house and ghost.state != EATEN : continue # Ghosts in house (not eaten) don't collide until they exit

            if pacman_rect.colliderect(ghost.get_rect()):
                if ghost.state == FRIGHTENED:
                    ghost.state = EATEN
                    ghost.is_in_house = False # Ensure it knows it's "outside" to path back to door
                    ghost.is_aiming_for_spawn_in_house = False # Start process of returning
                    ghost.target_pos = ghost.exit_house_pos # Head for the door
                    self.pacman.score += 200
                elif ghost.state != EATEN:
                    self.game_state = "PACMAN_DEATH"
                    break

    def start_fright_mode(self):
        self.fright_timer = self.fright_duration
        for ghost in self.ghosts:
            if ghost.state != EATEN and not ghost.is_in_house : # Don't affect eaten ghosts or those still in house
                ghost.state = FRIGHTENED
                ghost.reverse_direction()

    def end_fright_mode(self):
        self.fright_timer = 0
        for ghost in self.ghosts:
            if ghost.state == FRIGHTENED:
                ghost.state = self.current_ghost_mode
                if not ghost.is_in_house: # Reverse only if outside house
                    ghost.reverse_direction()


    def render(self):
        self.screen.fill(BLACK)
        self.draw_maze()
        self.draw_pellets()

        self.pacman.draw(self.screen)
        for ghost in self.ghosts:
            ghost.draw(self.screen)

        self.draw_ui()

        if self.game_state == "START":
            self.draw_text("READY?", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        elif self.game_state == "GAME_OVER":
            self.draw_text("GAME OVER", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
            self.draw_text("Press ENTER to Restart", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, self.small_font)
        elif self.game_state == "WIN":
            self.draw_text("YOU WIN!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
            self.draw_text("Press ENTER to Restart", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, self.small_font)
        elif self.game_state == "PACMAN_DEATH":
             self.draw_text("CAUGHT!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, color=RED)

        pygame.display.flip()

    def draw_maze(self):
        for r, row_data in enumerate(self.maze):
            for c, cell_type in enumerate(row_data):
                rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if cell_type == 1:
                    pygame.draw.rect(self.screen, BLUE, rect)
                elif cell_type == 4:
                    # Draw solid for Pacman's view, or just outline for ghost pathing visibility
                    # pygame.draw.rect(self.screen, BLUE, rect) # Makes it look like a wall
                    pygame.draw.rect(self.screen, GREY, rect, 1) # Outline


    def draw_pellets(self):
        for c, r in self.pellets:
            pixel_pos = to_pixel((c,r))
            pygame.draw.circle(self.screen, YELLOW, pixel_pos, PELLET_RADIUS)
        for c, r in self.power_pellets:
            pixel_pos = to_pixel((c,r))
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            current_radius = int(POWER_PELLET_RADIUS * (0.8 + 0.2 * pulse))
            pygame.draw.circle(self.screen, ORANGE, pixel_pos, current_radius)

    def draw_ui(self):
        score_text = self.font.render(f"SCORE: {self.pacman.score}", True, WHITE)
        self.screen.blit(score_text, (20, GRID_HEIGHT * CELL_SIZE + 15))
        lives_text = self.font.render(f"LIVES: {self.pacman.lives if self.pacman.lives >= 0 else 0}", True, WHITE)
        self.screen.blit(lives_text, (SCREEN_WIDTH - 150, GRID_HEIGHT * CELL_SIZE + 15))
        # Debug: Display current ghost mode
        # mode_str = ["SCATTER", "CHASE", "FRIGHT", "EATEN"][self.current_ghost_mode]
        # if self.fright_timer > 0: mode_str = "FRIGHTENED"
        # mode_txt = self.small_font.render(mode_str, True, WHITE)
        # self.screen.blit(mode_txt, (SCREEN_WIDTH // 2 - 50, GRID_HEIGHT * CELL_SIZE + 40))


    def draw_text(self, text, x, y, font=None, color=YELLOW, center=True):
        if font is None: font = self.font
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x,y)
        self.screen.blit(text_surface, text_rect)

    # --- Pac-Man AI Decision Logic ---
    def pacman_ai_decide_next_move(self):
        pacman = self.pacman

        active_ghosts = [g for g in self.ghosts if g.state not in [EATEN] and not g.is_in_house]
        frightened_ghosts = [g for g in self.ghosts if g.state == FRIGHTENED and not g.is_in_house]

        # --- Strategy 1: Hunt Frightened Ghosts ---
        if self.fright_timer > 0 and frightened_ghosts:
            closest_fright_ghost = self.find_closest_entity_ai(pacman, frightened_ghosts)
            if closest_fright_ghost:
                path = a_star_pathfind(pacman.grid_pos, closest_fright_ghost.grid_pos, self, pacman)
                if path and len(path) > 1:
                    return self.direction_to_next_step_ai(pacman.grid_pos, path[1])

        # --- Strategy 2: Evade Dangerous Ghosts ---
        # More sensitive evasion: check distance to ALL active ghosts.
        # If any ghost is "too close", prioritize evasion or getting a power pellet.
        EVASION_DISTANCE_THRESHOLD = 6
        GHOST_TOO_CLOSE_FOR_NORMAL_PELLET_HUNTING = 4 # If ghost is this close, only go for PP or pure evasion.

        min_dist_to_active_ghost = float('inf')
        nearest_active_ghost = None
        potential_threat = False

        for g in active_ghosts:
            dist = manhattan_distance(pacman.grid_pos, g.grid_pos)
            if g.state != FRIGHTENED: # Only consider non-frightened ghosts as threats for this calc
                if dist < min_dist_to_active_ghost:
                    min_dist_to_active_ghost = dist
                    nearest_active_ghost = g
                if dist < EVASION_DISTANCE_THRESHOLD:
                    potential_threat = True

        if potential_threat:
            # Try to get a Power Pellet if it's a good option
            if self.power_pellets:
                closest_pp = self.find_closest_target_pos_ai(pacman.grid_pos, self.power_pellets)
                if closest_pp:
                    # Is path to PP safer than current situation or other options?
                    # Consider distance to PP vs distance to ghost
                    dist_to_pp = manhattan_distance(pacman.grid_pos, closest_pp)
                    if dist_to_pp < min_dist_to_active_ghost + 2 or dist_to_pp < 5 : # If PP is close or closer than ghost threat + buffer
                        path_to_pp = a_star_pathfind(pacman.grid_pos, closest_pp, self, pacman)
                        if path_to_pp and len(path_to_pp) > 1:
                             # Simple safety check: next step doesn't lead directly to ghost
                            next_step_pos = path_to_pp[1]
                            if nearest_active_ghost:
                                if manhattan_distance(next_step_pos, nearest_active_ghost.grid_pos) > 1 : # or check if ghost can reach it
                                    return self.direction_to_next_step_ai(pacman.grid_pos, path_to_pp[1])
                            else: # No specific nearest ghost, path to PP seems fine
                                return self.direction_to_next_step_ai(pacman.grid_pos, path_to_pp[1])


            # If no good PP option or it's too risky, try to evade directly
            if nearest_active_ghost : # Ensure there is a ghost to evade from
                # Find a safe tile: a pellet far from the nearest ghost
                # For simplicity, just try to move away from the nearest_active_ghost
                # A better method would pathfind to a "safe zone"
                best_evade_dir = self.find_best_evade_direction_ai(pacman, nearest_active_ghost)
                if best_evade_dir != STOP:
                    return best_evade_dir

        # --- Strategy 3: Eat Pellets (Default) ---
        # Only go for normal pellets if not under immediate threat or if that threat is manageable
        if not potential_threat or min_dist_to_active_ghost > GHOST_TOO_CLOSE_FOR_NORMAL_PELLET_HUNTING:
            if self.pellets:
                closest_pellet = self.find_closest_target_pos_ai(pacman.grid_pos, self.pellets)
                if closest_pellet:
                    path = a_star_pathfind(pacman.grid_pos, closest_pellet, self, pacman)
                    if path and len(path) > 1:
                        return self.direction_to_next_step_ai(pacman.grid_pos, path[1])

        # --- Strategy 4: Eat remaining Power Pellets if no normal pellets and no immediate threat ---
        if not self.pellets and self.power_pellets:
            closest_pp = self.find_closest_target_pos_ai(pacman.grid_pos, self.power_pellets)
            if closest_pp:
                path = a_star_pathfind(pacman.grid_pos, closest_pp, self, pacman)
                if path and len(path) > 1:
                    return self.direction_to_next_step_ai(pacman.grid_pos, path[1])

        return STOP # No clear action / stuck (should try to find *any* valid move if truly stuck)

    # --- Pac-Man AI Helper Methods (prefix with _ai to avoid name clashes if put in Pacman class) ---
    def find_closest_target_pos_ai(self, start_pos, target_list_tuples):
        if not target_list_tuples: return None
        closest_target = None
        min_dist = float('inf')
        for target_pos_tuple in target_list_tuples:
            dist = manhattan_distance(start_pos, target_pos_tuple)
            if dist < min_dist:
                min_dist = dist
                closest_target = target_pos_tuple
        return closest_target

    def find_closest_entity_ai(self, start_entity, entity_list):
        if not entity_list: return None
        closest_e = None
        min_dist = float('inf')
        for e in entity_list:
            dist = manhattan_distance(start_entity.grid_pos, e.grid_pos)
            if dist < min_dist:
                min_dist = dist
                closest_e = e
        return closest_e

    def direction_to_next_step_ai(self, current_pos_tuple, next_pos_tuple):
        cur_x, cur_y = int(round(current_pos_tuple[0])), int(round(current_pos_tuple[1]))
        next_x, next_y = int(round(next_pos_tuple[0])), int(round(next_pos_tuple[1]))

        dx = next_x - cur_x
        dy = next_y - cur_y

        # Normalize, though A* should give adjacent cells
        if dx > 0: dx = 1
        elif dx < 0: dx = -1
        else: dx = 0

        if dy > 0: dy = 1
        elif dy < 0: dy = -1
        else: dy = 0

        return (dx, dy)

    def find_best_evade_direction_ai(self, pacman_obj, ghost_to_evade):
        best_dir = STOP
        max_safety_score = -float('inf')

        possible_directions = []
        for d_candidate in [UP, DOWN, LEFT, RIGHT]:
            next_pos = (pacman_obj.grid_pos[0] + d_candidate[0], pacman_obj.grid_pos[1] + d_candidate[1])
            if not pacman_obj.is_wall(next_pos, for_ghost=False):
                possible_directions.append(d_candidate)

        if not possible_directions: return STOP

        current_dist_to_ghost = manhattan_distance(pacman_obj.grid_pos, ghost_to_evade.grid_pos)

        for d in possible_directions:
            next_pacman_pos = (pacman_obj.grid_pos[0] + d[0], pacman_obj.grid_pos[1] + d[1])
            new_dist_to_ghost = manhattan_distance(next_pacman_pos, ghost_to_evade.grid_pos)

            # Basic safety score: prioritize increasing distance.
            # More advanced: consider if ghost can cut off, distance to escape routes (pellets/PPs)
            safety_score = new_dist_to_ghost - current_dist_to_ghost

            # Penalize moving towards the ghost if it's very close
            if new_dist_to_ghost < current_dist_to_ghost and current_dist_to_ghost <= 2:
                safety_score -= 10 # Heavy penalty

            if safety_score > max_safety_score:
                max_safety_score = safety_score
                best_dir = d
            elif safety_score == max_safety_score: # Tie-break, prefer not reversing Pacman's current dir unless necessary
                if pacman_obj.direction != STOP and d != (-pacman_obj.direction[0], -pacman_obj.direction[1]):
                    best_dir = d # Prefer non-reversing if scores are equal

        if best_dir == STOP and possible_directions: # If all options seem equally bad or neutral, pick one
            return random.choice(possible_directions)

        return best_dir


# --- Main Execution ---
if __name__ == '__main__':
    game = Game()
    game.run()

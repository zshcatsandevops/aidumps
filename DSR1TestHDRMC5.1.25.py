from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from random import random, randint
import noise  # Using the C-based noise library

# Initialize Ursina application
app = Ursina(title="Minecraft Clone", fullscreen=False)
window.fps_counter.enabled = True  # Show FPS counter
window.exit_button.visible = False  # Hide exit button

# Game settings
CHUNK_SIZE = 16  # Size of each chunk (16x16 blocks)
VIEW_DISTANCE = 4  # How many chunks to render around the player
WORLD_HEIGHT = 64  # Maximum height of the world

# World storage
world_blocks = {}  # Dictionary to store block positions and colors
chunks = {}  # Dictionary to store loaded chunks
seed = int(random() * 100)  # Random seed for the noise
directions = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]  # Neighbor directions for face culling

# Chunk class to handle terrain generation and rendering
class Chunk(Entity):
    def __init__(self, x, z):
        super().__init__(
            parent=scene,
            model=Mesh(),
            texture='white_cube',  # Use a plain cube with colors
            collider=None
        )
        self.x, self.z = x, z
        self.position = Vec3(x * CHUNK_SIZE, 0, z * CHUNK_SIZE)
        self.generate_terrain()
        self.build_mesh()

    def generate_terrain(self):
        """Generate terrain for this chunk using Perlin noise."""
        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                wx = x + self.x * CHUNK_SIZE  # World x-coordinate
                wz = z + self.z * CHUNK_SIZE  # World z-coordinate
                # Use proper noise.snoise2 function with better scaling
                height_value = noise.snoise2(
                    wx / 30.0, 
                    wz / 30.0, 
                    octaves=4,
                    persistence=0.5,
                    lacunarity=2.0,
                    base=seed
                )
                # Convert noise from [-1,1] to a proper height
                height = int((height_value + 1) * 8) + WORLD_HEIGHT // 2
                
                for y in range(height):
                    pos = (wx, y, wz)
                    if y == height - 1:
                        world_blocks[pos] = color.green  # Grass on top
                    elif y >= height - 3:
                        world_blocks[pos] = color.brown  # Dirt layer
                    else:
                        world_blocks[pos] = color.gray   # Stone below
                # Add trees with a small chance
                if random() < 0.01 and height < WORLD_HEIGHT - 5:
                    tree_height = randint(3, 5)
                    for dy in range(tree_height):
                        world_blocks[(wx, height + dy, wz)] = color.rgb(139, 69, 19)  # Log (brown)
                    top_y = height + tree_height
                    for dx in [-1, 0, 1]:
                        for dz in [-1, 0, 1]:
                            if dx != 0 or dz != 0:
                                world_blocks[(wx + dx, top_y, wz + dz)] = color.lime  # Leaves

    def build_mesh(self):
        """Build an optimized mesh for this chunk with face culling."""
        vertices = []
        triangles = []
        colors = []
        uvs = []

        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                wx = x + self.x * CHUNK_SIZE
                wz = z + self.z * CHUNK_SIZE
                for y in range(WORLD_HEIGHT):
                    pos = (wx, y, wz)
                    if pos in world_blocks:
                        block_color = world_blocks[pos]
                        # Check each face for culling
                        for dx, dy, dz in directions:
                            neighbor_pos = (wx + dx, y + dy, wz + dz)
                            if neighbor_pos not in world_blocks:
                                if dx == 1:  # Right face
                                    v0 = (wx + 1, y, wz)
                                    v1 = (wx + 1, y + 1, wz)
                                    v2 = (wx + 1, y + 1, wz + 1)
                                    v3 = (wx + 1, y, wz + 1)
                                elif dx == -1:  # Left face
                                    v0 = (wx, y, wz)
                                    v1 = (wx, y + 1, wz)
                                    v2 = (wx, y + 1, wz + 1)
                                    v3 = (wx, y, wz + 1)
                                elif dy == 1:  # Top face
                                    v0 = (wx, y + 1, wz)
                                    v1 = (wx + 1, y + 1, wz)
                                    v2 = (wx + 1, y + 1, wz + 1)
                                    v3 = (wx, y + 1, wz + 1)
                                elif dy == -1:  # Bottom face
                                    v0 = (wx, y, wz)
                                    v1 = (wx + 1, y, wz)
                                    v2 = (wx + 1, y, wz + 1)
                                    v3 = (wx, y, wz + 1)
                                elif dz == 1:  # Front face
                                    v0 = (wx, y, wz + 1)
                                    v1 = (wx + 1, y, wz + 1)
                                    v2 = (wx + 1, y + 1, wz + 1)
                                    v3 = (wx, y + 1, wz + 1)
                                elif dz == -1:  # Back face
                                    v0 = (wx, y, wz)
                                    v1 = (wx + 1, y, wz)
                                    v2 = (wx + 1, y + 1, wz)
                                    v3 = (wx, y + 1, wz)

                                start_idx = len(vertices)
                                vertices.extend([v0, v1, v2, v3])
                                triangles.extend([[start_idx, start_idx + 1, start_idx + 2],
                                                 [start_idx, start_idx + 2, start_idx + 3]])
                                colors.extend([block_color] * 4)
                                uvs.extend([(0, 0)] * 4)

        if vertices:
            self.model = Mesh(vertices=vertices, triangles=triangles, colors=colors, uvs=uvs, mode='triangle')
            self.model.generate()
            self.collider = 'mesh'  # Enable collision with the mesh

# Generate initial chunks around the origin
def generate_initial_chunks():
    for x in range(-VIEW_DISTANCE, VIEW_DISTANCE):
        for z in range(-VIEW_DISTANCE, VIEW_DISTANCE):
            chunks[(x, z)] = Chunk(x, z)

generate_initial_chunks()

# Set up the player
player = FirstPersonController(
    position=(0, WORLD_HEIGHT + 10, 0),  # Spawn above terrain
    speed=8,  # Movement speed
    gravity=1,  # Gravity strength
    jump_height=1.5  # Jump height
)

# Add a skybox
Sky(texture='sky_sunset')

# Add a hand icon for interaction feedback
hand = Entity(
    parent=camera.ui,
    model='cube',
    color=color.white,
    scale=(0.1, 0.2, 0.1),
    rotation=(10, 10, 10),
    position=(0.4, -0.4, 0)
)

# Update chunks based on player position
def update_chunks():
    chunk_pos = (int(player.x // CHUNK_SIZE), int(player.z // CHUNK_SIZE))
    to_remove = []
    # Remove chunks outside view distance
    for (x, z) in chunks:
        if abs(x - chunk_pos[0]) > VIEW_DISTANCE or abs(z - chunk_pos[1]) > VIEW_DISTANCE:
            to_remove.append((x, z))
    for key in to_remove:
        destroy(chunks[key])
        del chunks[key]
    # Load new chunks within view distance
    for x in range(chunk_pos[0] - VIEW_DISTANCE, chunk_pos[0] + VIEW_DISTANCE):
        for z in range(chunk_pos[1] - VIEW_DISTANCE, chunk_pos[1] + VIEW_DISTANCE):
            if (x, z) not in chunks:
                chunks[(x, z)] = Chunk(x, z)

# Main update loop
def update():
    update_chunks()

# Handle player input
def input(key):
    if key == 'escape':
        quit()
    if key in ('left mouse down', 'right mouse down'):
        hit = raycast(player.position, player.forward, distance=10, ignore=(player,))
        if hit.hit:
            normal = hit.normal
            if key == 'left mouse down':  # Place a block
                target_pos = (
                    int(floor(hit.point.x + normal.x * 0.5)),
                    int(floor(hit.point.y + normal.y * 0.5)),
                    int(floor(hit.point.z + normal.z * 0.5))
                )
                if target_pos not in world_blocks:
                    world_blocks[target_pos] = color.random_color()  # Random color for new blocks
            elif key == 'right mouse down':  # Remove a block
                block_pos = (
                    int(floor(hit.point.x - normal.x * 0.01)),
                    int(floor(hit.point.y - normal.y * 0.01)),
                    int(floor(hit.point.z - normal.z * 0.01))
                )
                if block_pos in world_blocks:
                    del world_blocks[block_pos]
                    target_pos = block_pos
                else:
                    return

            # Update affected chunks
            wx, y, wz = target_pos
            chunks_to_update = set()
            chunks_to_update.add((wx // CHUNK_SIZE, wz // CHUNK_SIZE))
            for dx, dy, dz in directions:
                nx, ny, nz = wx + dx, y + dy, wz + dz
                chunks_to_update.add((nx // CHUNK_SIZE, nz // CHUNK_SIZE))
            for cx, cz in chunks_to_update:
                if (cx, cz) in chunks:
                    chunks[(cx, cz)].build_mesh()

# Start the game
app.run()

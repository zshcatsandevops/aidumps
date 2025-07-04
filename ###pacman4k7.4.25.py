###############################################################################
#           PAC‑MAN  –  "FULL 256"  (Special 64 Famicom Edition)             #
#                                                                             #
#  Features implemented                                                       #
#  ──────────────────────────────────────────────────────────────────────────  #
#   • "TEAM SPECIALEMU AGI Division Presents" splash, Ghost Roll‑Call, READY  #
#   • Classic maze rendered entirely from code (28 × 31 layout, 16‑px tiles)  #
#   • Pac‑Man, 4 ghosts with Famicom/NES-style simplified AI                  #
#   • 256 sequential levels (speed & fruit scale with level)                  #
#   • Authentic level‑256 glitch: right half of maze becomes corrupted gfx    #
#   • Famicom-style simple beep sounds for all effects                        #
#   • Score, lives, level HUD; 1‑up at 10 000; three starting lives           #
#   • Clean restart after GAME OVER                                           #
#                                                                             #
#  ░░  Famicom/Midway NES-style AI with simpler, more random ghost behavior  #
###############################################################################

import sys, math, random, itertools, array
import pygame

# ────────────────────────────── CONSTANTS ────────────────────────────────── #
TILE       = 16
MAZE_W     = 28                           # tiles
MAZE_H     = 31                           # Extended to proper Pac-Man height
SCREEN_W   = MAZE_W * TILE
SCREEN_H   = MAZE_H * TILE + 64           # 64‑px HUD bar
FPS        = 60
WALL_CLR   = (0,  0, 255)
DOT_CLR    = (255,255,0)
BG_CLR     = (0,  0,  0)
FRUIT_CLR  = (255,  0,255)
TEXT_CLR   = (255,255,255)
GHOST_COLS = {"Blinky":(255,0,0), "Pinky":(255,184,255),
              "Inky":(0,255,255), "Clyde":(255,184,82)}
START_LIVES=3
ONE_UP     = 10000

# Square‑wave sound helper -------------------------------------------------- #
def make_beep(freq, ms, volume=0.5):
    rate=44100
    n=int(rate*ms/1000)
    buf=array.array("h")
    amp=int(32767*volume)
    per=rate//freq
    half=per//2
    for i in range(n):
        buf.append(amp if (i%per)<half else -amp)
    return pygame.mixer.Sound(buffer=buf.tobytes())

# Simple assets (generated once) ------------------------------------------- #
def gen_assets():
    assets={}
    # Famicom-style simpler sounds
    assets["waka"]=make_beep(440,25,0.3)      # Lower pitch, shorter
    assets["power"]=make_beep(220,150,0.5)    # Lower pitch power pellet
    assets["eatghost"]=make_beep(880,100,0.6) # Higher pitch for eating ghost
    assets["extra"]=make_beep(1000,200,0.4)   # Extra life sound
    font_big = pygame.font.SysFont("arial",24,True)
    font_med = pygame.font.SysFont("arial",18,True)
    font_sml = pygame.font.SysFont("arial",14,True)
    assets["f_big"],assets["f_med"],assets["f_sml"]=font_big,font_med,font_sml
    return assets

# Maze layout: 28×31 strings (# wall, . dot, o power pellet, ' ' empty) ----- #
# Extended maze with proper ghost house and Pac-Man spawn area
MAZE = [
"############################",
"#............##............#",
"#.####.#####.##.#####.####.#",
"#o####.#####.##.#####.####o#",
"#.####.#####.##.#####.####.#",
"#..........................#",
"#.####.##.########.##.####.#",
"#.####.##.########.##.####.#",
"#......##....##....##......#",
"######.##### ## #####.######",
"     #.##### ## #####.#     ",
"     #.##          ##.#     ",
"     #.## ###--### ##.#     ",
"######.## #      # ##.######",
"      .   #      #   .      ",
"######.## #      # ##.######",
"     #.## ######## ##.#     ",
"     #.##          ##.#     ",
"     #.## ######## ##.#     ",
"######.## ######## ##.######",
"#............##............#",
"#.####.#####.##.#####.####.#",
"#.####.#####.##.#####.####.#",
"#o..##.......  .......##..o#",
"###.##.##.########.##.##.###",
"###.##.##.########.##.##.###",
"#......##....##....##......#",
"#.##########.##.##########.#",
"#.##########.##.##########.#",
"#..........................#",
"############################"
]

# Tile utilities ----------------------------------------------------------- #
def px(x,tile=True): return x*TILE if tile else x
def tile_at(pos): return (int(pos[0]//TILE), int((pos[1]-64)//TILE))

def maze_char(tx,ty): 
    if 0<=ty<MAZE_H and 0<=tx<MAZE_W: return MAZE[ty][tx]
    return '#'

def walkable(tx,ty,is_ghost=False): 
    ch = maze_char(tx,ty)
    if is_ghost:
        return ch not in ['#']  # Ghosts can pass through gate
    return ch not in ['#', '-']  # Can't walk through walls or ghost house gate

# Directions --------------------------------------------------------------- #
DIRS = {"L":(-1,0),"R":(1,0),"U":(0,-1),"D":(0,1)}
OPP  = {"L":"R","R":"L","U":"D","D":"U"}
DIR_VEC = list(DIRS.values())

# Pac‑Man & Ghost classes --------------------------------------------------- #
class Entity:
    def __init__(self,x,y,speed,color):
        self.x,self.y = x*TILE+TILE//2, y*TILE+TILE//2+64
        self.start_x, self.start_y = self.x, self.y  # Store spawn position
        self.dir = "L"
        self.speed = speed
        self.color = color
    def pos(self): return (self.x,self.y)
    def tile(self): return tile_at(self.pos())
    def move(self):
        vx,vy = DIRS[self.dir]
        self.x += vx*self.speed
        self.y += vy*self.speed
    def draw_circle(self,screen,radius):
        pygame.draw.circle(screen,self.color,(int(self.x),int(self.y)),radius)
    def reset_position(self):
        self.x, self.y = self.start_x, self.start_y
        self.dir = "L"

class Pacman(Entity):
    def __init__(self,x,y):
        super().__init__(x,y,1.8,(255,255,0))  # Slower speed like Famicom
        self.mouth=0
    def update(self,keys,maze,assets):
        desired=self.dir
        # handle input to change desired dir
        if keys[pygame.K_LEFT]: desired="L"
        elif keys[pygame.K_RIGHT]: desired="R"
        elif keys[pygame.K_UP]: desired="U"
        elif keys[pygame.K_DOWN]: desired="D"
        # turn if possible
        if desired!=self.dir and self.can_move(desired):
            self.dir = desired
        if not self.can_move(self.dir): return False # blocked
        old_tile=self.tile()
        self.move()
        # Tunnel wrap
        if self.x < 0: self.x = SCREEN_W
        if self.x > SCREEN_W: self.x = 0
        # Famicom style - less frequent waka sound
        if self.tile()!=old_tile and random.random() < 0.5: 
            assets["waka"].play()
        return True
    def can_move(self,dirn):
        vx,vy=DIRS[dirn]
        nx,ny = (self.x+vx*self.speed*2)//TILE, (self.y+vy*self.speed*2-64)//TILE
        return walkable(int(nx),int(ny),is_ghost=True)
    def draw(self,screen):
        self.draw_circle(screen,7)

class Ghost(Entity):
    def __init__(self,x,y,name,color):
        super().__init__(x,y,1.5,color)  # Slower initial speed like Famicom
        self.name=name
        self.mode="scatter"
        self.frightened=False
        self.last_decision_tile = None
        self.random_turns = 0
        self.exit_house_timer = {"Blinky":0, "Pinky":60, "Inky":120, "Clyde":180}[name]
        # Famicom/NES style - ghosts behave more similarly
    def update(self,pac_tile,level,tick_count):
        # Handle ghost house exit
        if self.exit_house_timer > 0:
            self.exit_house_timer -= 1
            if self.exit_house_timer == 0:
                # Move ghost to exit position above the gate
                self.x = 13 * TILE + TILE//2
                self.y = 11 * TILE + TILE//2 + 64
                self.dir = "L"
            return
            
        # Famicom style - more uniform speed progression
        self.speed = 1.5 + (level-1)*0.03
        
        # Check if at intersection for decision making
        tx, ty = self.tile()
        at_intersection = self.is_at_intersection(tx, ty)
        
        if self.frightened:
            # Frightened mode - pure random movement
            if at_intersection and (tx, ty) != self.last_decision_tile:
                self.choose_random_direction()
                self.last_decision_tile = (tx, ty)
        else:
            # Famicom AI - simpler chase with more randomness
            if at_intersection and (tx, ty) != self.last_decision_tile:
                self.last_decision_tile = (tx, ty)
                
                # 60% chance to chase, 40% random (Famicom style)
                if random.random() < 0.6:
                    # Simple chase - just head toward Pac-Man
                    self.chase_pacman(pac_tile)
                else:
                    # Random movement
                    self.choose_random_direction()
        
        # Move if possible
        if self.can_move(self.dir):
            self.move()
        else:
            # Hit a wall, choose new direction
            self.choose_random_direction()
            
        # tunnel wrap
        if self.x< -TILE: self.x=SCREEN_W+TILE
        if self.x> SCREEN_W+TILE: self.x=-TILE
    
    def is_at_intersection(self, tx, ty):
        # Check if ghost is at a decision point (intersection)
        available_dirs = 0
        for d in DIRS:
            vx, vy = DIRS[d]
            if walkable(tx+vx, ty+vy, is_ghost=True):
                available_dirs += 1
        return available_dirs > 2  # More than 2 means intersection
    
    def chase_pacman(self, pac_tile):
        # Simple Famicom-style chase - just pick direction that gets closer
        best = self.dir
        best_d = 1e9
        
        tx, ty = self.tile()
        for d, (vx, vy) in DIRS.items():
            if d == OPP[self.dir]: continue  # Don't reverse
            nx, ny = tx+vx, ty+vy
            if not walkable(nx, ny, is_ghost=True): continue
            
            # Simple distance calculation
            dist = abs(nx - pac_tile[0]) + abs(ny - pac_tile[1])
            if dist < best_d:
                best_d = dist
                best = d
        
        self.dir = best
    
    def choose_random_direction(self):
        # Random direction choice (Famicom style)
        tx, ty = self.tile()
        valid_dirs = []
        
        for d, (vx, vy) in DIRS.items():
            if d == OPP[self.dir]: continue  # Don't reverse
            nx, ny = tx+vx, ty+vy
            if walkable(nx, ny, is_ghost=True):
                valid_dirs.append(d)
        
        if valid_dirs:
            self.dir = random.choice(valid_dirs)
    
    def can_move(self,dirn):
        vx,vy=DIRS[dirn]
        nx,ny = (self.x+vx*self.speed*2)//TILE, (self.y+vy*self.speed*2-64)//TILE
        return walkable(int(nx),int(ny))  # Pac-Man can't go through gate
    def draw(self,screen):
        if self.frightened:
            # Famicom style - flash between blue and white
            if (pygame.time.get_ticks() // 200) % 2:
                pygame.draw.circle(screen,(0,0,255),(int(self.x),int(self.y)),7)
            else:
                pygame.draw.circle(screen,(200,200,255),(int(self.x),int(self.y)),7)
        else:
            self.draw_circle(screen,7)

# Game ---------------------------------------------------------------------- #
class Game:
    def __init__(self,screen,assets):
        self.screen=screen
        self.assets=assets
        self.reset(full=True)
    def reset(self,full=False):
        self.level=1 if full else self.level+1
        self.score=0 if full else self.score
        self.lives=START_LIVES if full else self.lives
        self.extra_given=False if full else self.extra_given
        self.state="splash"
        self.state_t=0
        self.build_level()
    def build_level(self):
        # build dot set
        self.dots=set()
        self.power=set()
        for y,row in enumerate(MAZE):
            for x,ch in enumerate(row):
                if ch=='.': self.dots.add((x,y))
                elif ch=='o': self.power.add((x,y))
        # entities - Fixed spawn positions
        self.pac=Pacman(13,23)  # Proper Pac-Man spawn position
        self.ghosts=[
            Ghost(13,14,"Blinky",GHOST_COLS["Blinky"]),  # In ghost house
            Ghost(14,14,"Pinky", GHOST_COLS["Pinky"]),
            Ghost(13,15,"Inky",  GHOST_COLS["Inky"]),
            Ghost(14,15,"Clyde", GHOST_COLS["Clyde"])
        ]
        # Set initial directions for ghosts in house
        for g in self.ghosts:
            if g.name != "Blinky":
                g.dir = "U"  # Start facing up to exit
        self.fright_timer=0
        self.tick=0
    # ------------------- STATE MACHINE flows --------------------------------
    def update(self,keys):
        self.tick+=1
        if self.state=="splash":
            if self.tick>3*FPS: self.to_rollcall()
        elif self.state=="roll":
            if self.tick>3*FPS+len(self.ghosts)*FPS: self.to_ready()
        elif self.state=="ready":
            if self.tick>self.ready_end: self.state="play"
        elif self.state=="play":
            self.update_play(keys)
        elif self.state=="levelup":
            if self.tick-self.state_t>2*FPS: self.reset(full=False)
        elif self.state=="gameover":
            if keys[pygame.K_RETURN]: self.reset(full=True)
    def to_rollcall(self):
        self.state="roll"
        self.tick=0
    def to_ready(self):
        self.state="ready"
        self.tick=0
        self.ready_end=self.tick+FPS*4
        # Reset positions when ready state starts
        self.pac.reset_position()
        for g in self.ghosts:
            g.reset_position()
    def update_play(self,keys):
        # timers
        if self.fright_timer>0:
            self.fright_timer-=1
            if self.fright_timer==0:
                for g in self.ghosts: g.frightened=False
        
        # pacman
        self.pac.update(keys,MAZE,self.assets)
        ptile=self.pac.tile()
        # eat dots
        if ptile in self.dots:
            self.dots.remove(ptile)
            self.score+=10
            self.check_extra()
        if ptile in self.power:
            self.power.remove(ptile)
            self.score+=50
            self.fright_timer=5*FPS  # Shorter frightened time like Famicom
            self.assets["power"].play()
            for g in self.ghosts: g.frightened=True
            self.check_extra()
        # fruit every level *30 dots, simply give points
        if not hasattr(self,"fruit_spawned") and len(self.dots)<80:
            self.fruit_spawned=True
            self.fruit_tile=(13,17)
        if hasattr(self,"fruit_tile") and ptile==self.fruit_tile:
            self.score+=100+ (self.level-1)*10
            delattr(self,"fruit_tile")
        # ghosts
        for g in self.ghosts:
            g.update(ptile,self.level,self.tick)
            if int(g.x//TILE)==ptile[0] and int((g.y-64)//TILE)==ptile[1]:
                if g.frightened:
                    g.frightened=False
                    self.score+=200
                    self.assets["eatghost"].play()
                    self.check_extra()
                    # Famicom style - ghost takes time to respawn
                    g.x,g.y = 13*TILE+TILE//2,14*TILE+TILE//2+64
                    g.exit_house_timer = 120  # 2 seconds to respawn
                else:
                    self.lives-=1
                    if self.lives<=0:
                        self.state="gameover"
                        self.tick=0
                    else:
                        self.to_ready()
                    return
        if not self.dots and not self.power:
            self.state="levelup"
            self.state_t=self.tick
            if self.level==255: self.state="glitch"
    def check_extra(self):
        if not self.extra_given and self.score>=ONE_UP:
            self.lives+=1
            self.extra_given=True
            self.assets["extra"].play()
    # --------------------------- RENDER ------------------------------------
    def draw(self):
        self.screen.fill(BG_CLR)
        # HUD
        f_sml=self.assets["f_sml"]
        self.screen.blit(f_sml.render(f"SCORE  {self.score}",True,TEXT_CLR),(8,8))
        self.screen.blit(f_sml.render(f"LEVEL  {self.level}",True,TEXT_CLR),(180,8))
        self.screen.blit(f_sml.render(f"LIVES  {self.lives}",True,TEXT_CLR),(320,8))
        # Maze & dots
        self.draw_maze()
        # entities
        self.pac.draw(self.screen)
        for g in self.ghosts: g.draw(self.screen)
        # fruit
        if hasattr(self,"fruit_tile"):
            x,y=self.fruit_tile
            pygame.draw.circle(self.screen,FRUIT_CLR,(px(x)+TILE//2,px(y)+TILE//2+64),6)
        # overlay messages
        if self.state in ("splash","roll","ready","gameover","levelup","glitch"):
            self.draw_overlay()
        pygame.display.flip()
    def draw_maze(self):
        # walls
        for y,row in enumerate(MAZE):
            for x,ch in enumerate(row):
                rx,ry=px(x),px(y)+64
                if ch=='#':
                    pygame.draw.rect(self.screen,WALL_CLR,(rx,ry,TILE,TILE),1)
                elif ch=='-':  # Ghost house gate
                    pygame.draw.line(self.screen,(255,192,203),(rx,ry+TILE//2),(rx+TILE,ry+TILE//2),2)
                elif ch=='.' and (x,y) in self.dots:
                    pygame.draw.circle(self.screen,DOT_CLR,(rx+TILE//2,ry+TILE//2),2)
                elif ch=='o' and (x,y) in self.power:
                    pygame.draw.circle(self.screen,DOT_CLR,(rx+TILE//2,ry+TILE//2),4)
        # level‑256 glitch effect
        if self.state=="glitch":
            for _ in range(100):
                cx=random.randint(SCREEN_W//2,SCREEN_W-1)
                cy=random.randint(64,SCREEN_H-1)
                w=random.randint(4,32)
                h=random.randint(4,32)
                col=(random.randint(0,255),random.randint(0,255),random.randint(0,255))
                pygame.draw.rect(self.screen,col,(cx,cy,w,h))
    def draw_overlay(self):
        f_big,f_med=self.assets["f_big"],self.assets["f_med"]
        if self.state=="splash":
            # Special 64 Edition splash
            txt1=f_big.render("TEAM SPECIALEMU AGI Division",True,(255,0,0))
            txt2=f_med.render("Presents",True,TEXT_CLR)
            self.screen.blit(txt1,(SCREEN_W//2-txt1.get_width()//2,SCREEN_H//2-40))
            self.screen.blit(txt2,(SCREEN_W//2-txt2.get_width()//2,SCREEN_H//2+10))
        elif self.state=="roll":
            idx=min((self.tick//FPS),len(self.ghosts)-1)
            ghost=self.ghosts[idx]
            name=ghost.name.upper()
            nick={"BLINKY":"Shadow","PINKY":"Speedy",
                  "INKY":"Bashful","CLYDE":"Pokey"}[name]
            txt1=f_big.render(name,True,ghost.color)
            txt2=f_med.render(f'"{nick}"',True,TEXT_CLR)
            self.screen.blit(txt1,(SCREEN_W//2-txt1.get_width()//2,SCREEN_H//2-40))
            self.screen.blit(txt2,(SCREEN_W//2-txt2.get_width()//2,SCREEN_H//2+10))
        elif self.state=="ready":
            if self.tick<FPS*1:
                msg="READY!"
            else:
                cnt=3-int((self.tick-FPS)//FPS)
                msg=f"{cnt}"
            txt=f_big.render(msg,True,TEXT_CLR)
            self.screen.blit(txt,(SCREEN_W//2-txt.get_width()//2,SCREEN_H//2-txt.get_height()//2))
        elif self.state=="levelup":
            txt=f_big.render("LEVEL CLEARED!",True,TEXT_CLR)
            self.screen.blit(txt,(SCREEN_W//2-txt.get_width()//2,SCREEN_H//2-txt.get_height()//2))
        elif self.state=="gameover":
            txt=f_big.render("GAME OVER",True,TEXT_CLR)
            ins=f_med.render("Press <ENTER> to play again",True,TEXT_CLR)
            self.screen.blit(txt,(SCREEN_W//2-txt.get_width()//2,SCREEN_H//2-40))
            self.screen.blit(ins,(SCREEN_W//2-ins.get_width()//2,SCREEN_H//2+10))
        elif self.state=="glitch":
            txt=f_big.render("LEVEL 256 !!!",True,TEXT_CLR)
            self.screen.blit(txt,(SCREEN_W//2-txt.get_width()//2,80))

# ──────────────────────────── MAIN ROUTINE ──────────────────────────────── #
def main():
    pygame.init()
    pygame.mixer.init()
    screen=pygame.display.set_mode((SCREEN_W,SCREEN_H))
    pygame.display.set_caption("Pac‑Man Special 64 Famicom Edition")
    clock=pygame.time.Clock()
    assets=gen_assets()
    g=Game(screen,assets)
    running=True
    while running:
        keys=pygame.key.get_pressed()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: running=False
        g.update(keys)
        g.draw()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()

if __name__=="__main__":
    main()

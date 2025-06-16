import pygame, sys, random, numpy as np
pygame.init(); pygame.mixer.init()

# --- CONFIG -------------------------------------------------------
FPS = 60
WIDTH, HEIGHT = 800, 600
TILE   = 32
GRAVITY    = 0.6
JUMP_VEL   = -12
PLAYER_ACC = 0.8
FRICTION   = 0.7

# --- WINDOW -------------------------------------------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("New Super Mario Bros. U DX – PyGame")
clock  = pygame.time.Clock()

# --- COLOURS ------------------------------------------------------
BLACK=(0,0,0); WHITE=(255,255,255); RED=(255,0,0); BLUE=(0,0,255)
BROWN=(139,69,19); YELLOW=(255,255,0); GREEN=(0,255,0); ORANGE=(255,165,0)

# --- QUICK SFX ----------------------------------------------------
def gen_sfx(freq, dur):
    sr=44100
    t = np.linspace(0,dur,int(sr*dur),False)
    wave = 0.5*np.sin(2*np.pi*freq*t)
    stereo = np.column_stack((wave,wave))
    return pygame.sndarray.make_sound((stereo*32767).astype(np.int16))

JUMP_SFX  = gen_sfx(440,0.12)
COIN_SFX  = gen_sfx(880,0.10)
PWR_SFX   = gen_sfx(660,0.20)
STOMP_SFX = gen_sfx(220,0.10)

# --- SIMPLE ENTITIES ---------------------------------------------
class Coin:
    def __init__(self,x,y): self.rect=pygame.Rect(x,y,16,16)
    def draw(self): pygame.draw.circle(screen,YELLOW,self.rect.center,8)

class PowerUp:
    def __init__(self,x,y): self.rect=pygame.Rect(x,y,20,20)
    def draw(self): pygame.draw.rect(screen,ORANGE,self.rect)

class Goomba:
    def __init__(self,x,y): self.rect=pygame.Rect(x,y,28,28); self.vx=-1
    def update(self):
        self.rect.x+=self.vx
    def draw(self): pygame.draw.rect(screen,BROWN,self.rect)

class Fireball:
    def __init__(self,x,y,dir): self.rect=pygame.Rect(x,y,8,8); self.vx=6*dir; self.vy=-4
    def update(self):
        self.rect.x+=self.vx; self.vy+=GRAVITY; self.rect.y+=self.vy
        if self.rect.bottom>HEIGHT-64: self.rect.bottom=HEIGHT-64; self.vy=-self.vy*0.5
    def draw(self): pygame.draw.rect(screen,ORANGE,self.rect)

# --- SCENE SYSTEM ------------------------------------------------
class Scene:                 # base class
    def __init__(self,app): self.app=app
    def handle_event(self,e):pass
    def update(self):pass
    def draw(self):pass

class LevelSelectScene(Scene):
    def __init__(self,app):
        super().__init__(app)
        self.buttons=[]
        self.sel=0
        self.mk_buttons()

    def mk_buttons(self):
        lvls=[(w,l) for w in range(1,3) for l in range(1,3)]
        btn_w,btn_h, pad=80,40,20
        total_w=len(lvls)*btn_w+(len(lvls)-1)*pad
        start_x=(WIDTH-total_w)//2
        y=HEIGHT//2
        for i,(w,l) in enumerate(lvls):
            x=start_x+i*(btn_w+pad)
            self.buttons.append((pygame.Rect(x,y,btn_w,btn_h),f"{w}-{l}"))

    def handle_event(self,e):
        if e.type==pygame.QUIT or (e.type==pygame.KEYDOWN and e.key in (pygame.K_q,pygame.K_ESCAPE)):
            pygame.quit(); sys.exit()
        elif e.type==pygame.KEYDOWN:
            if e.key==pygame.K_RIGHT: self.sel=(self.sel+1)%len(self.buttons)
            if e.key==pygame.K_LEFT:  self.sel=(self.sel-1)%len(self.buttons)
            if e.key in (pygame.K_RETURN,pygame.K_SPACE):
                _,lvl=self.buttons[self.sel]
                self.app.switch(GameplayScene(self.app,lvl))
        elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            for i,(r,lvl) in enumerate(self.buttons):
                if r.collidepoint(e.pos):
                    self.sel=i; self.app.switch(GameplayScene(self.app,lvl))

    def draw(self):
        screen.fill(BLACK)
        title=pygame.font.Font(None,60).render("Select Level",True,WHITE)
        screen.blit(title,(WIDTH//2-title.get_width()//2,100))
        fnt=pygame.font.Font(None,36)
        for i,(r,label) in enumerate(self.buttons):
            pygame.draw.rect(screen,WHITE if i==self.sel else BLUE,r,border_radius=6)
            txt=fnt.render(label,True,BLACK if i==self.sel else WHITE)
            screen.blit(txt,txt.get_rect(center=r.center))

class GameplayScene(Scene):
    def __init__(self,app,lvl_id):
        super().__init__(app)
        # --- level data ---------------------------------------------------
        self.level = self.build_level(lvl_id)
        # --- player -------------------------------------------------------
        self.player_w,self.player_h=26,32
        self.player=pygame.Rect(100,HEIGHT-128,self.player_w,self.player_h)
        self.vx=self.vy=0
        self.on_ground=False
        self.has_fire=False
        # --- groups -------------------------------------------------------
        self.coins  =[Coin(300,HEIGHT-128-16)]
        self.powers =[PowerUp(500,HEIGHT-128-20)]
        self.enemies=[Goomba(600,HEIGHT-128-28)]
        self.fireballs=[]
        self.score=0; self.lives=3
        # input state
        self.move_left=self.move_right=self.want_jump=False

    # --------------------------------------------------------------------
    def build_level(self,lvl):
        """Returns a list of dicts like {'type':'ground','x':0,'y':18,'width':25}"""
        ground_line={'type':'ground','x':0,'y':(HEIGHT//TILE)-2,'width':25}
        brick1     ={'type':'block','x':8,'y':10,'width':2}
        pipe       ={'type':'pipe','x':15,'y':13,'width':2,'height':3}
        return [ground_line,brick1,pipe]

    # --------------------------------------------------------------------
    def handle_event(self,e):
        if e.type==pygame.QUIT or (e.type==pygame.KEYDOWN and e.key in (pygame.K_q,pygame.K_ESCAPE)):
            pygame.quit(); sys.exit()
        if e.type==pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT,pygame.K_a):  self.move_left=True
            if e.key in (pygame.K_RIGHT,pygame.K_d): self.move_right=True
            if e.key in (pygame.K_SPACE,pygame.K_UP,pygame.K_w): self.want_jump=True
            if e.key==pygame.K_f and self.has_fire:
                dir = -1 if self.move_left and not self.move_right else 1
                self.fireballs.append(Fireball(self.player.centerx,self.player.centery,dir))
        if e.type==pygame.KEYUP:
            if e.key in (pygame.K_LEFT,pygame.K_a):  self.move_left=False
            if e.key in (pygame.K_RIGHT,pygame.K_d): self.move_right=False

    # --------------------------------------------------------------------
    def on_ground_check(self):
        test=pygame.Rect(self.player.x,self.player.y+1,self.player_w,self.player_h)
        for obj in self.level:
            if obj['type'] in ('ground','block','pipe'):
                r=self.tile_rect(obj)
                if test.colliderect(r): return True
        return False

    def tile_rect(self,obj):
        x,y=obj['x']*TILE, obj['y']*TILE
        w=obj.get('width',1)*TILE
        h=obj.get('height',1)*TILE
        return pygame.Rect(x,y,w,h)

    # --------------------------------------------------------------------
    def update(self):
        # --- physics -----------------------------------------------------
        if self.move_left:  self.vx -= PLAYER_ACC
        if self.move_right: self.vx += PLAYER_ACC
        self.vx *= FRICTION
        self.vy += GRAVITY

        # jump
        self.on_ground=self.on_ground_check()
        if self.want_jump and self.on_ground:
            self.vy = JUMP_VEL
            JUMP_SFX.play()
        self.want_jump=False

        # apply
        self.player.x += self.vx
        # horizontal collisions
        for obj in self.level:
            if obj['type'] in ('ground','block','pipe'):
                r=self.tile_rect(obj)
                if self.player.colliderect(r):
                    if self.vx>0: self.player.right=r.left
                    if self.vx<0: self.player.left=r.right
                    self.vx=0
        self.player.y += self.vy
        # vertical collisions
        for obj in self.level:
            if obj['type'] in ('ground','block','pipe'):
                r=self.tile_rect(obj)
                if self.player.colliderect(r):
                    if self.vy>0:  self.player.bottom=r.top; self.vy=0
                    if self.vy<0:  self.player.top=r.bottom; self.vy=0

        # --- collectibles -----------------------------------------------
        for c in self.coins[:]:
            if self.player.colliderect(c.rect):
                self.coins.remove(c); self.score+=100; COIN_SFX.play()

        for p in self.powers[:]:
            if self.player.colliderect(p.rect):
                self.powers.remove(p); self.has_fire=True; PWR_SFX.play()

        # --- enemies -----------------------------------------------------
        for g in self.enemies[:]:
            g.update()
            if self.player.colliderect(g.rect):
                if self.vy>0 and self.player.bottom-g.rect.top<10:
                    self.enemies.remove(g); self.score+=200; self.vy=-8; STOMP_SFX.play()
                else:
                    self.lives-=1; self.player.topleft=(100,HEIGHT-128)

        # --- fireballs ---------------------------------------------------
        for fb in self.fireballs[:]:
            fb.update()
            if fb.rect.right<0 or fb.rect.left>WIDTH: self.fireballs.remove(fb)
            for g in self.enemies[:]:
                if fb.rect.colliderect(g.rect):
                    self.enemies.remove(g); self.fireballs.remove(fb); self.score+=200

    # --------------------------------------------------------------------
    def draw(self):
        screen.fill((92,148,252))                      # sky
        # level tiles
        for obj in self.level:
            r=self.tile_rect(obj)
            if obj['type']=='ground': pygame.draw.rect(screen,GREEN,r)
            elif obj['type']=='block': pygame.draw.rect(screen,BROWN,r)
            elif obj['type']=='pipe': pygame.draw.rect(screen,BLUE,r)
        # entities
        for c in self.coins:   c.draw()
        for p in self.powers:  p.draw()
        for g in self.enemies: g.draw()
        for fb in self.fireballs: fb.draw()
        # player
        pygame.draw.rect(screen,RED if self.has_fire else WHITE,self.player)
        # HUD
        hud=pygame.font.Font(None,24).render(f"Score {self.score}   Lives {self.lives}",True,WHITE)
        screen.blit(hud,(10,10))

# --- APP WRAPPER --------------------------------------------------
class App:
    def __init__(self): self.scene=LevelSelectScene(self)
    def switch(self,scene):  self.scene=scene
    def run(self):
        while True:
            for e in pygame.event.get(): self.scene.handle_event(e)
            self.scene.update(); self.scene.draw()
            pygame.display.flip(); clock.tick(FPS)

# --- ENTRY --------------------------------------------------------
if __name__=="__main__": App().run()

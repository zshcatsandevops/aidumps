import pygame, random, sys, math

# ---------- CONSTANTS ----------
SCREEN_W, SCREEN_H = 640, 480
BATTLE_BOX = pygame.Rect(120, 136, 400, 200)  # shifted 16 px down
SOUL_SIZE  = 8
FPS        = 60
IFRAMES    = 15            # invincibility frames after hit

WHITE, BLACK = (255,255,255), (0,0,0)
RED, YELLOW  = (255,0,0), (255,255,0)
GRAY, DGRAY  = (128,128,128), (64,64,64)
PURPLE, PINK = (128,0,128), (255,192,203)

# ---------- INITIALISATION ----------
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Kris vs Cat‑sama — Deltarune‑style battle")
clock = pygame.time.Clock()
font_big   = pygame.font.SysFont("monospace", 24, bold=True)
font_small = pygame.font.SysFont("monospace", 16, bold=True)

# ---------- CLASSES ----------
class Kris:
    LV, MAX_HP, ATK, DEF = 1, 92, 10, 2

    def __init__(self):
        self.hp   = self.MAX_HP
        self.tp   = 0
        self.state = "MENU"  # MENU | SUB_MENU | TARGET | DODGE
        self.menu_idx = 0
        self.act_idx  = 0
        # SOUL kinematics
        self.sx = BATTLE_BOX.centerx
        self.sy = BATTLE_BOX.centery
        self.vx = self.vy = 0
        self.base_spd = 4
        # fight‑bar vars
        self.timer = 0.0
        self.critical = False
        self.iframes = 0  # remaining invulnerability frames

    # ------------ drawing ------------
    def _draw_soul(self):
        pts = [
            [(self.sx, self.sy-4), (self.sx-4, self.sy), (self.sx, self.sy+4)],
            [(self.sx, self.sy-4), (self.sx+4, self.sy), (self.sx, self.sy+4)]
        ]
        for tri in pts:
            pygame.draw.polygon(screen, RED, tri)
        pygame.draw.circle(screen, RED, (self.sx-2, self.sy-1), 2)
        pygame.draw.circle(screen, RED, (self.sx+2, self.sy-1), 2)

    def _draw_kris_sprite(self):
        x, y = 20, 330
        pygame.draw.rect(screen, (30,30,150), (x+4, y,     8, 8))  # hair
        pygame.draw.rect(screen, (0,170,0),  (x+2, y+8,  12, 6))  # torso stripe
        pygame.draw.rect(screen, (80,40,20), (x+4, y+14,  8, 8))  # legs

    def draw(self):
        if self.state == "DODGE":
            self._draw_soul()
        if self.state == "TARGET":
            self._draw_target_bar()
        self._draw_hud()
        if self.state == "MENU":
            self._draw_kris_sprite()

    def _draw_target_bar(self):
        bar_w, bar_h = 180, 16
        bx = BATTLE_BOX.centerx - bar_w//2
        by = BATTLE_BOX.centery
        pygame.draw.rect(screen, WHITE, (bx, by, bar_w, bar_h), 2)
        prog = (self.timer % 0.8) / 0.8
        cx = bx + int(bar_w * prog)
        pygame.draw.line(screen, YELLOW, (cx, by), (cx, by+bar_h), 3)
        # perfect flash
        if self.critical:
            pygame.draw.rect(screen, YELLOW, (bx, by, bar_w, bar_h), 0, 3)

    def _draw_hud(self):
        # Panel
        pygame.draw.rect(screen, BLACK, (0, 320, 640, 160))
        pygame.draw.rect(screen, WHITE, (0, 320, 640, 160), 2)
        party = [("KRIS", self.hp, self.MAX_HP, self.LV),
                 ("SUSIE",110,110,1), ("RALSEI",70,70,1)]
        for i,(nm,hp,maxhp,lv) in enumerate(party):
            ox = 40 + i*200
            screen.blit(font_small.render(f"{nm} LV {lv}", True, WHITE), (ox, 330))
            screen.blit(font_small.render(f"HP {hp}/{maxhp}", True, WHITE), (ox, 350))
            pygame.draw.rect(screen, RED, (ox+60, 350, int(hp*1.5), 8))
            pygame.draw.rect(screen, DGRAY,(ox+60, 350, int(maxhp*1.5), 8), 1)
        # TP
        screen.blit(font_small.render(f"TP {self.tp:>3d}%", True, WHITE), (40, 370))
        pygame.draw.rect(screen, YELLOW, (100, 370, self.tp*2, 8))
        pygame.draw.rect(screen, DGRAY,  (100, 370, 200, 8), 1)
        # Main menu
        opts = ["FIGHT","ACT","ITEM","MERCY"]
        for i,opt in enumerate(opts):
            col = YELLOW if i==self.menu_idx else WHITE
            screen.blit(font_big.render(opt, True, col), (80+i*140, 400))
        # ACT sub menu
        if self.state == "SUB_MENU":
            acts = ["Check","Hiss","Pet","AIChat"]
            for i,ac in enumerate(acts):
                col = YELLOW if i==self.act_idx else WHITE
                screen.blit(font_small.render(ac, True, col), (200, 340+i*20))

    # ------------ movement & stats ------------
    def move_heart(self, keys):
        if self.state != "DODGE":
            return
        ax = ay = 0
        if keys[pygame.K_LEFT]:  ax -= 1
        if keys[pygame.K_RIGHT]: ax += 1
        if keys[pygame.K_UP]:    ay -= 1
        if keys[pygame.K_DOWN]:  ay += 1
        # simple acceleration --> velocity
        self.vx += ax * 0.5
        self.vy += ay * 0.5
        # clamp speed
        self.vx = max(-self.base_spd, min(self.base_spd, self.vx))
        self.vy = max(-self.base_spd, min(self.base_spd, self.vy))
        self.sx += int(self.vx)
        self.sy += int(self.vy)
        # box bounds
        self.sx = max(BATTLE_BOX.left+SOUL_SIZE,  min(BATTLE_BOX.right-SOUL_SIZE, self.sx))
        self.sy = max(BATTLE_BOX.top+SOUL_SIZE,   min(BATTLE_BOX.bottom-SOUL_SIZE, self.sy))

    def take_hit(self, enemy_atk):
        if self.iframes:     # still invincible
            return 0
        dmg = max(1, 5*enemy_atk - 3*self.DEF)
        self.hp = max(0, self.hp - dmg)
        self.iframes = IFRAMES
        return dmg

    def tick(self):
        if self.iframes:
            self.iframes -= 1

    def add_tp(self, amt):
        self.tp = min(100, self.tp + amt)

class CatSama:
    MAX_HP, ATK, DEF = 120, 8, 3
    DIALOG = ["* Cat‑sama purrs «Wa‑wa!»",
              "* It meows like ChatGPT!",
              "* Cat‑sama demands pets!"]

    def __init__(self):
        self.hp = self.MAX_HP
        self.mercy = 0
        self.x, self.y = BATTLE_BOX.centerx, BATTLE_BOX.top+40
        self.bullets = []
        self.pattern = 0

    # ------------ drawing ------------
    def draw(self):
        # kitty
        pygame.draw.rect(screen, PURPLE,(self.x-30,self.y,60,40), border_radius=6)
        pygame.draw.rect(screen, PINK,  (self.x-25,self.y+5,50,30), border_radius=4)
        pygame.draw.polygon(screen, PURPLE,[(self.x-30,self.y),(self.x-20,self.y-20),(self.x-10,self.y)])
        pygame.draw.polygon(screen, PURPLE,[(self.x+30,self.y),(self.x+20,self.y-20),(self.x+10,self.y)])
        pygame.draw.circle(screen, YELLOW,(self.x-15,self.y+15),5)
        pygame.draw.circle(screen, YELLOW,(self.x+15,self.y+15),5)
        pygame.draw.arc(screen, WHITE,(self.x-10,self.y+20,20,10),math.pi,1.5*math.pi,2)
        pygame.draw.line(screen, WHITE,(self.x+5,self.y+25),(self.x+10,self.y+25),2)
        # bullets
        for b in self.bullets:
            col = PINK if b[4] else WHITE  # graze flicker
            pygame.draw.circle(screen, col,(int(b[0]),int(b[1])),6)

    # ------------ behaviour ------------
    def fire(self):
        if self.pattern==0:          # radial 8‑way burst
            for ang in range(0,360,45):
                rad = math.radians(ang)
                self.bullets.append([self.x,self.y+40,
                                     math.cos(rad)*3, math.sin(rad)*3, 0])
        else:                        # sine wave row
            for i in range(-3,4):
                self.bullets.append([BATTLE_BOX.left-10, self.y+80+i*8,
                                     2, math.sin(i)*1.5, 0])
        self.pattern ^= 1

    def update_bullets(self):
        for b in self.bullets:
            b[0] += b[2]; b[1] += b[3]
        self.bullets[:] = [b for b in self.bullets
            if (BATTLE_BOX.left-20 < b[0] < BATTLE_BOX.right+20)
            and (BATTLE_BOX.top-20  < b[1] < BATTLE_BOX.bottom+20)]

    def hit(self, dmg):  self.hp = max(0, self.hp-dmg)
    def add_mercy(self,pts):
        self.mercy = min(100, self.mercy+pts)
        return self.mercy==100

# ---------- GAME STATE ----------
kris   = Kris()
enemy  = CatSama()
dialog = "* Cat‑sama blocks the way!"
turn   = "PLAYER"
elapsed = 0.0

# ---------- MAIN LOOP ----------
running = True
while running:
    dt = clock.tick(FPS)/1000
    elapsed += dt
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:  pygame.quit(); sys.exit()
        if ev.type == pygame.KEYDOWN:
            # universal cancel
            if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                pygame.quit(); sys.exit()

            # ------------- PLAYER TURN -------------
            if turn=="PLAYER" and kris.state=="MENU":
                if ev.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    kris.menu_idx = (kris.menu_idx + (1 if ev.key==pygame.K_RIGHT else -1))%4
                if ev.key in (pygame.K_z, pygame.K_RETURN):
                    if kris.menu_idx==0:               # FIGHT
                        kris.state, kris.timer = "TARGET", 0.0
                    elif kris.menu_idx==1:             # ACT
                        kris.state="SUB_MENU"; kris.act_idx=0
                    elif kris.menu_idx==3:             # MERCY
                        spared = enemy.add_mercy(20)
                        kris.add_tp(10)
                        dialog = ("* You SPARE Cat‑sama! It joins Castle Town!"
                                  if spared else "* Cat‑sama’s Mercy increased!")
                        if spared: turn="END"
                        else:      kris.state="DODGE"; turn="ENEMY"

            elif turn=="PLAYER" and kris.state=="SUB_MENU":
                if ev.key in (pygame.K_UP, pygame.K_DOWN):
                    kris.act_idx = (kris.act_idx + (1 if ev.key==pygame.K_DOWN else -1))%4
                if ev.key==pygame.K_x:  # cancel
                    kris.state="MENU"
                if ev.key in (pygame.K_z, pygame.K_RETURN):
                    act = ["Check","Hiss","Pet","AIChat"][kris.act_idx]
                    if act=="Check":
                        dialog="* Cat‑sama AT 8  DF 3 — Loves AI and «wa‑wa!»"
                    elif act=="Hiss":
                        dialog="* You hiss! Cat‑sama hisses louder."
                        enemy.add_mercy(10)
                    elif act=="Pet":
                        dialog="* You pet Cat‑sama! It purrs approvingly."
                        enemy.add_mercy(30)
                    else:
                        dialog="* You debate AI ethics. Cat‑sama listens keenly."
                        enemy.add_mercy(40)
                    kris.add_tp(15)
                    kris.state="DODGE"; turn="ENEMY"

            elif turn=="PLAYER" and kris.state=="TARGET":
                if ev.key in (pygame.K_z, pygame.K_RETURN):
                    prog = (kris.timer%0.8)/0.8
                    mult = 2.0 if abs(prog-0.5)<0.03 else (1.4 if abs(prog-0.5)<0.10 else 1.0)
                    dmg  = int(kris.ATK*mult)
                    enemy.hit(dmg)
                    kris.add_tp(int(mult*10))
                    kris.critical = mult>1.9
                    dialog = f"* {dmg} damage! {'Great hit!' if kris.critical else ''}"
                    kris.state="DODGE"; turn="ENEMY"

    # held keys for SOUL motion
    kris.move_heart(pygame.key.get_pressed())

    # physics ticks
    kris.tick()
    if kris.state=="TARGET": kris.timer += dt

    # ------------- ENEMY TURN -------------
    if turn=="ENEMY":
        if int(elapsed*FPS)%90==0: enemy.fire()
        enemy.update_bullets()
        # collision & graze
        for b in enemy.bullets[:]:
            dx,dy = kris.sx-b[0], kris.sy-b[1]
            dist = math.hypot(dx,dy)
            if dist < 14:                  # hit
                dmg=kris.take_hit(enemy.ATK)
                if dmg:
                    dialog=f"* Kris took {dmg} damage!"
                    enemy.bullets.remove(b)
                kris.add_tp(10)
            elif dist < 22 and not b[4]:   # graze first frame
                kris.add_tp(4); b[4]=1
        # enemy turn length
        if elapsed % 1.5 < dt:
            dialog=random.choice(enemy.DIALOG)
            turn="PLAYER"; kris.state="MENU"
            enemy.bullets.clear()

    # ------------- DRAW -------------
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, BATTLE_BOX, 4)
    enemy.draw()
    kris.draw()
    # dialogue box
    pygame.draw.rect(screen, BLACK,(40,40,560,60))
    pygame.draw.rect(screen, WHITE,(40,40,560,60),2)
    for i,line in enumerate(dialog.splitlines()):
        screen.blit(font_small.render(line,True,WHITE),(60,60+i*18))
    # Mercy bar
    if enemy.mercy and turn!="END":
        screen.blit(font_small.render(f"MERCY {enemy.mercy}% ", True, WHITE),(450,100))
        pygame.draw.rect(screen, YELLOW,(450,120, enemy.mercy*2,8))
    # end banner
    if turn=="END":
        screen.blit(font_big.render("Recruit acquired! Press ESC.",True,YELLOW),(120,260))

    pygame.display.flip()

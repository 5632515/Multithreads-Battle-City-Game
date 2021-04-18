import random, pygame, sys, threading
import multiprocessing
from pygame.locals import *
import random
import time
import queue
from concurrent.futures import ThreadPoolExecutor

T_LOCK = threading.Lock()
FPSCLOCK = None
FPS = 140
__display = pygame.display
version = '1.0'
SPEED = 2
CHANCES = 10
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
DISPLAYSURF = None
g_walls = None
g_p1_tank = None
g_enemy_tank_count = 5
g_enemy_tank_list = []
g_bullet_list = []
g_enemy_bullet_list = []
g_explode_list = []
g_wall_list = []
pygame.mixer.init()
fire_sound = pygame.mixer.Sound('resources/musics/fire.wav')
fire_sound.set_volume(0.1)
boom_sound = pygame.mixer.Sound('resources/musics/boom.wav')
boom_sound.set_volume(0.1)
MAP = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 0, 0],
       [0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 0, 0],
       [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 0, 0],
       [0, 0, 0, 0, 0, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 0],
       [0, 0, 0, 0, 2, 2, 3, 0, 0, 0, 4, 4, 4, 4, 4, 0],
       [2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 4, 0, 0, 0, 4, 4],
       [0, 0, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
       [0, 0, 3, 3, 3, 3, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0],
       [0, 0, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
       [0, 0, 3, 3, 3, 0, 1, 0, 0, 5, 0, 0, 1, 0, 0, 0],
       [0, 0, 0, 2, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0],
       [0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
       ]
BLACK = pygame.Color(0, 0, 0)
COLOR_RED = pygame.Color(255, 0, 0)
music_path = 'resources/musics/bgm.mp3'

TANK_RUNNING = True


def play_bgm(music_file):
    pygame.mixer.music.load(music_file)
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)


class BaseItem(pygame.sprite.Sprite, threading.Thread):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        threading.Thread.__init__(self)

    pass


class Tank(BaseItem):
    def __init__(self):
        super().__init__()

    def run(self):
        pass


class MyTank(Tank):
    def __init__(self, left, top):
        super().__init__()
        self.images = {
            'U': pygame.image.load('resources/images/hero/U.png'),
            'D': pygame.image.load('resources/images/hero/D.png'),
            'L': pygame.image.load('resources/images/hero/L.png'),
            'R': pygame.image.load('resources/images/hero/R.png')
        }
        self.images_invincible = {
            'U': pygame.image.load('resources/images/hero/U1.png'),
            'D': pygame.image.load('resources/images/hero/D1.png'),
            'L': pygame.image.load('resources/images/hero/L1.png'),
            'R': pygame.image.load('resources/images/hero/R1.png')
        }
        self.direction = 'U'
        self.speed = SPEED
        self.image = self.images_invincible[self.direction]
        self.rect = self.image.get_rect()  # left top width height
        self.rect.left = left
        self.rect.top = top
        self.stop = True
        self.live = True
        self.old_left = 0
        self.old_top = 0
        self.invincible = FPS
        self.fpsclock = pygame.time.Clock()

    def run(self):
        while self.live and TANK_RUNNING:
            if self.live:
                self.now_image()
                if not self.stop:
                    self.move()
                    self.hit_wall()
            # time.sleep(0.01)
            self.fpsclock.tick(FPS)

    def now_image(self):
        if self.invincible > 0:
            with T_LOCK:
                self.image = self.images_invincible[self.direction]
        else:
            # print('mortal')
            with T_LOCK:
                self.image = self.images[self.direction]

    def move(self):
        self.old_top = self.rect.top
        self.old_left = self.rect.left
        if self.direction == 'U':
            if self.rect.top > 0:
                self.rect.top -= self.speed
        elif self.direction == 'D':
            if self.rect.top < SCREEN_HEIGHT - self.rect.width:
                self.rect.top += self.speed
        elif self.direction == 'L':
            if self.rect.left > 0:
                self.rect.left -= self.speed
        elif self.direction == 'R':
            if self.rect.left < SCREEN_WIDTH - self.rect.height:
                self.rect.left += self.speed

    def hit_wall(self):
        for wall in g_wall_list:
            if wall.kind != 3 and wall.kind != 5:
                result = pygame.sprite.collide_rect(wall, self)
                if result:
                    self.stay()

    def stay(self):
        self.rect.left = self.old_left
        self.rect.top = self.old_top

    def fire(self):
        bullet = Bullet(self)
        fire_sound.play()
        return bullet


class EnemyTank(Tank):
    def __init__(self, left, top, speed):
        super().__init__()
        self.images = {
            'U': pygame.image.load('resources/images/enemy/U.png'),
            'D': pygame.image.load('resources/images/enemy/D.png'),
            'L': pygame.image.load('resources/images/enemy/L.png'),
            'R': pygame.image.load('resources/images/enemy/R.png')
        }
        self.direction = random.choice(['U', 'D', 'L', 'R'])
        self.image = self.images[self.direction]
        self.speed = SPEED
        self.rect = self.image.get_rect()  # left top width height
        self.rect.left = left
        self.rect.top = top
        self.step = random.randint(20, 80)
        self.invincible = 1
        self.live = True
        self.stop = False
        self.old_left = 0
        self.old_top = 0
        self.fpsclock = pygame.time.Clock()

    def run(self):
        global g_enemy_bullet_list, g_enemy_tank_list
        while self.live and TANK_RUNNING:
            self.random_move()
            self.hit_wall()
            if len(g_enemy_bullet_list) < len(g_enemy_tank_list) * 3:
                ebullet = self.random_fire()
                if ebullet:
                    with T_LOCK:
                        g_enemy_bullet_list.append(ebullet)
                        ebullet.start()
            # time.sleep(0.01)
            self.fpsclock.tick(FPS)

    def move(self):
        self.old_top = self.rect.top
        self.old_left = self.rect.left
        if self.direction == 'U':
            if self.rect.top > 0:
                self.rect.top -= self.speed
        elif self.direction == 'D':
            if self.rect.top < SCREEN_HEIGHT - self.rect.width:
                self.rect.top += self.speed
        elif self.direction == 'L':
            if self.rect.left > 0:
                self.rect.left -= self.speed
        elif self.direction == 'R':
            if self.rect.left < SCREEN_WIDTH - self.rect.height:
                self.rect.left += self.speed

    def random_direction(self):
        global g_p1_tank
        if g_p1_tank:
            m_l = g_p1_tank.rect.left
            m_t = g_p1_tank.rect.top
        else:
            m_l = random.randint(0, 800)
            m_t = random.randint(0, 600)
        e_l = self.rect.left
        e_t = self.rect.top
        delta_l = e_l - m_l
        delta_t = e_t - m_t
        dire = random.randint(1, 2)
        num = random.randint(1, 4)
        p = random.random()
        if dire == 1:  # L R
            if (delta_l < 0) and (p <= 0.8):
                num = 4
            else:
                num = 3
        elif dire == 2:  # U D
            if (delta_t < 0) and (p <= 0.8):
                num = 2
            else:
                num = 1
        with T_LOCK:
            if num == 1:
                self.direction = 'U'
            elif num == 2:
                self.direction = 'D'
            elif num == 3:
                self.direction = 'L'
            elif num == 4:
                self.direction = 'R'
            self.change_image()  # 转向换图片
        return self.direction

    def random_move(self):
        if self.step <= 0:
            self.random_direction()
            self.step += random.randint(20, 150)
        else:
            self.move()
            self.step -= 1

    def change_image(self):
        self.image = self.images[self.direction]

    def random_fire(self):
        e_l = self.rect.left
        e_t = self.rect.top
        if g_p1_tank:
            m_l = g_p1_tank.rect.left
            m_t = g_p1_tank.rect.top
        else:
            m_l = random.randint(0, 800)
            m_t = random.randint(0, 600)
        delta_l = e_l - m_l
        delta_t = e_t - m_t
        num = random.randint(1, 100)
        if (abs(delta_t) < 10) or (abs(delta_l) < 10):
            num = random.randint(1, 50)
        if (abs(delta_t) < 5) or (abs(delta_l) < 5):
            num = random.randint(1, 30)
        if (abs(delta_t) < 1) or (abs(delta_l) < 1):
            num = random.randint(1, 10)
        if num <= 1:
            print('e fire')
            eBullet = self.fire()
            return eBullet

    def fire(self):
        bullet = Bullet(self)
        fire_sound.play()
        return bullet

    def hit_wall(self):
        for wall in g_wall_list:
            if wall.kind != 3 and wall.kind != 5:
                result = pygame.sprite.collide_rect(wall, self)
                if result:
                    self.stay()
                    a = [self.direction]
                    b = ['U', 'D', 'L', 'R']
                    ret = list(set(a) ^ set(b))
                    choose = random.randint(0, 2)
                    with T_LOCK:
                        self.direction = ret[choose]
                        self.change_image()

    def stay(self):
        self.rect.left = self.old_left
        self.rect.top = self.old_top

    pass


class Bullet(BaseItem):
    images = {
        0: pygame.image.load('resources/images/bullet/bullet_sun.png'),
        1: pygame.image.load('resources/images/bullet/bullet_sun2.png')
    }

    def __init__(self, tank):
        super().__init__()
        if isinstance(tank, MyTank):
            self.belong = 0
        else:
            self.belong = 1
        self.image = Bullet.images[self.belong]
        self.direction = tank.direction
        self.speed = SPEED * 2
        self.rect = self.image.get_rect()
        if self.direction == 'U':
            self.rect.left = tank.rect.left + tank.rect.width / 2 - self.rect.width / 2
            self.rect.top = tank.rect.top - self.rect.width
        elif self.direction == 'D':
            self.rect.left = tank.rect.left + tank.rect.width / 2 - self.rect.width / 2
            self.rect.top = tank.rect.top + tank.rect.height
        elif self.direction == 'L':
            self.rect.left = tank.rect.left - self.rect.width
            self.rect.top = tank.rect.top + tank.rect.height / 2 - self.rect.height / 2
        elif self.direction == 'R':
            self.rect.left = tank.rect.left + tank.rect.width
            self.rect.top = tank.rect.top + tank.rect.height / 2 - self.rect.height / 2
        self.live = True
        self.fpsclock = pygame.time.Clock()

    def run(self):
        global SCREEN_HEIGHT, SCREEN_WIDTH
        if self.belong == 0:  # 分辨敌我
            hit = self.hit_enemy
        else:
            hit = self.hit_mytank
        while self.live and TANK_RUNNING:
            if self.direction == 'U':
                if self.rect.top > 0:
                    self.rect.top -= self.speed
                else:
                    self.live = False
            elif self.direction == 'D':
                if (self.rect.top + self.rect.height) < SCREEN_HEIGHT:
                    self.rect.top += self.speed
                else:
                    self.live = False
                pass
            elif self.direction == 'L':
                if self.rect.left > 0:
                    self.rect.left -= self.speed
                else:
                    self.live = False
                pass
            elif self.direction == 'R':
                if (self.rect.left + self.rect.width) < SCREEN_WIDTH:
                    self.rect.left += self.speed
                else:
                    self.live = False
            hit()
            self.hit_wall()
            # time.sleep(0.005)
            self.fpsclock.tick(FPS)

    def hit_enemy(self):
        global g_enemy_tank_list
        for etank in g_enemy_tank_list:
            result = pygame.sprite.collide_rect(etank, self)
            if result:
                with T_LOCK:
                    self.live = False
                    etank.live = False
                Explode(etank.rect)
                boom_sound.play()
        pass

    def hit_mytank(self):
        global g_p1_tank
        if g_p1_tank and g_p1_tank.live:
            if g_p1_tank.invincible <= 0:
                result = pygame.sprite.collide_rect(self, g_p1_tank)
                if result:
                    Explode(g_p1_tank.rect)
                    boom_sound.play()
                    with T_LOCK:
                        self.live = False
                        g_p1_tank.live = False
        pass

    def hit_wall(self):
        global g_wall_list
        for block in g_wall_list:
            if block.kind == 3 or block.kind == 4:
                continue
            else:
                result = pygame.sprite.collide_rect(block, self)
                if result:
                    Explode(block.rect)
                    boom_sound.play()
                    with T_LOCK:
                        self.live = False
                    if block.kind == 1:
                        with T_LOCK:
                            block.live = False


class Walls(BaseItem):
    def __init__(self, level_map=None):
        super().__init__()
        global g_wall_list, MAP
        if level_map is None:
            level_map = MAP
        for i in range(len(level_map)):
            for j in range(len(level_map[0])):
                if level_map[i][j] != 0:
                    block = Block(50 * j, 50 * i, level_map[i][j])
                    g_wall_list.append(block)
        self.live = True

    def run(self):
        global g_wall_list
        while True and TANK_RUNNING and self.live:
            for block in g_wall_list:
                if not block.live:
                    with T_LOCK:
                        g_wall_list.remove(block)
                        del block


class Block(BaseItem):
    block_images = {
        0: pygame.image.load('resources/images/walls/0.png'),
        1: pygame.image.load('resources/images/walls/1.png'),
        2: pygame.image.load('resources/images/walls/2.png'),
        3: pygame.image.load('resources/images/walls/3.png'),
        4: pygame.image.load('resources/images/walls/4.png'),
        5: pygame.image.load('resources/images/walls/5.png'),
    }

    def __init__(self, left, top, kind):
        super().__init__()
        self.kind = kind
        self.image = Block.block_images[kind]
        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.top = top
        self.live = True


class Explode(BaseItem):  # 因为爆炸的特殊性，所以爆炸直接会刷到画面上，而由View层控制刷新,以及存在
    images = [
        pygame.image.load('resources/images/boom/blast1.gif'),
        pygame.image.load('resources/images/boom/blast1.gif'),
        pygame.image.load('resources/images/boom/blast2.gif'),
        pygame.image.load('resources/images/boom/blast2.gif'),
        pygame.image.load('resources/images/boom/blast3.gif'),
        pygame.image.load('resources/images/boom/blast3.gif'),
        pygame.image.load('resources/images/boom/blast4.gif'),
        pygame.image.load('resources/images/boom/blast4.gif'),
        pygame.image.load('resources/images/boom/blast5.gif'),
        pygame.image.load('resources/images/boom/blast5.gif'),
        pygame.image.load('resources/images/boom/blast6.gif'),
        pygame.image.load('resources/images/boom/blast6.gif'),
        pygame.image.load('resources/images/boom/blast7.gif'),
        pygame.image.load('resources/images/boom/blast7.gif'),
        pygame.image.load('resources/images/boom/blast8.gif'),
        pygame.image.load('resources/images/boom/blast8.gif')
    ]

    def __init__(self, rect):
        global g_explode_list
        super().__init__()
        self.rect = rect
        self.image = Explode.images[0]
        self.live = True
        self.step = 0
        with T_LOCK:
            g_explode_list.append(self)

    def display(self):
        if self.step < len(self.images):
            self.image = self.images[self.step]
            self.step += 1

        else:
            self.live = False
            self.step = 0


def main():
    global FPSCLOCK, DISPLAYSURF, g_p1_tank, g_walls
    pool = ThreadPoolExecutor(max_workers=6)
    # Pygame window set up.
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
    pygame.display.set_caption('Tank War')
    g_walls = Walls()
    g_walls.start()
    g_p1_tank = MyTank(450, 450)
    # pool.submit(g_p1_tank.run)
    g_p1_tank.start()

    create_enemy()

    DISPLAYSURF.fill(pygame.Color(0, 0, 255))
    while True:  # main game loop
        drawScreen()
        pygame.display.update()
        handleEvents()
        FPSCLOCK.tick(FPS)
        if not TANK_RUNNING:
            break
    g_walls.join()
    pygame.quit()
    return


def create_enemy(num=g_enemy_tank_count):
    for i in range(num):
        e_tank = EnemyTank(random.randint(0, 300), 100, SPEED)
        with T_LOCK:
            g_enemy_tank_list.append(e_tank)
        e_tank.start()


def drawText(content, size=16):
    pygame.font.init()
    font = pygame.font.SysFont('dengxian', size)
    text_sf = font.render(content, True, COLOR_RED)
    return text_sf


def handleEvents():
    # The only event we need to handle in this program is when it terminates.
    global TANK_RUNNING, CHANCES, g_p1_tank, g_bullet_list

    for event in pygame.event.get():  # event handling loop
        if event.type == QUIT:
            with T_LOCK:
                TANK_RUNNING = False  # Setting this to False tells the Worm threads to exit.
            print('退出游戏')
        if event.type == pygame.KEYDOWN:
            if g_p1_tank and g_p1_tank.live:
                if event.key == pygame.K_LEFT:
                    print('left')
                    with T_LOCK:  # 修改公共变量状态必须加锁
                        g_p1_tank.direction = 'L'
                        g_p1_tank.stop = False
                elif event.key == pygame.K_RIGHT:
                    print('right')
                    with T_LOCK:  # 修改公共变量状态必须加锁
                        g_p1_tank.direction = 'R'
                        g_p1_tank.stop = False
                elif event.key == pygame.K_UP:
                    print('up')
                    with T_LOCK:  # 修改公共变量状态必须加锁
                        g_p1_tank.direction = 'U'
                        g_p1_tank.stop = False
                elif event.key == pygame.K_DOWN:
                    print('down')
                    with T_LOCK:  # 修改公共变量状态必须加锁
                        g_p1_tank.direction = 'D'
                        g_p1_tank.stop = False
                elif event.key == pygame.K_SPACE:
                    if len(g_bullet_list) < 3:
                        print('fire')
                        bullet = g_p1_tank.fire()
                        with T_LOCK:  # 修改公共变量状态必须加锁
                            g_bullet_list.append(bullet)
                            bullet.start()
            if not g_p1_tank and event.key == pygame.K_RETURN and CHANCES > 0:
                print('轮回天生！')
                CHANCES -= 1
                g_p1_tank = MyTank(450, 450)
                g_p1_tank.start()
            if event.key == pygame.K_r:
                reset()

        if (event.type == pygame.KEYUP) and g_p1_tank:  # and (sum(pygame.key.get_pressed()) == 0):
            if event.key != pygame.K_SPACE:
                with T_LOCK:
                    g_p1_tank.stop = True
            pass


def drawScreen():
    global DISPLAYSURF
    DISPLAYSURF.fill(pygame.Color(0, 0, 255))
    DISPLAYSURF.blit(drawText('剩余坦克%d辆' % len(g_enemy_tank_list)), (5, 5))
    DISPLAYSURF.blit(drawText('剩余机会%d' % CHANCES), (700, 5))

    show_p1()
    show_enemy_tank()
    show_wall()
    show_my_bullet()
    show_enemy_bullet()
    show_explode()
    # print('refresh')
    show_game_result()



def show_p1():
    global g_p1_tank, DISPLAYSURF
    if g_p1_tank:
        if g_p1_tank.live:
            if g_p1_tank.invincible > 0:
                g_p1_tank.invincible -= 1
                if g_p1_tank.invincible % 2 == 0:
                    DISPLAYSURF.blit(g_p1_tank.image, g_p1_tank.rect)
            else:
                DISPLAYSURF.blit(g_p1_tank.image, g_p1_tank.rect)
        else:
            g_p1_tank.join()
            del g_p1_tank
            g_p1_tank = None


def show_enemy_bullet():
    global g_enemy_bullet_list, DISPLAYSURF
    for bullet in g_enemy_bullet_list:
        if bullet.live:
            DISPLAYSURF.blit(bullet.image, bullet.rect)
        else:
            bullet.join()
            with T_LOCK:
                g_enemy_bullet_list.remove(bullet)


def show_my_bullet():
    global g_bullet_list, DISPLAYSURF
    for bullet in g_bullet_list:
        if bullet.live:
            DISPLAYSURF.blit(bullet.image, bullet.rect)
        else:
            bullet.join()
            with T_LOCK:
                g_bullet_list.remove(bullet)


def show_enemy_tank():
    global g_enemy_tank_list, DISPLAYSURF
    for e_tank in g_enemy_tank_list:
        if e_tank.live:
            DISPLAYSURF.blit(e_tank.image, e_tank.rect)
        else:
            e_tank.join()
            with T_LOCK:
                g_enemy_tank_list.remove(e_tank)


def show_wall():
    global g_wall_list, DISPLAYSURF
    for block in g_wall_list:
        if block.live:
            DISPLAYSURF.blit(block.image, block.rect)


def show_explode():
    global g_explode_list
    for explode in g_explode_list:
        if explode.live:
            DISPLAYSURF.blit(explode.image, explode.rect)
            explode.display()

def show_game_result():
    global g_enemy_tank_list, g_p1_tank, CHANCES
    if len(g_enemy_tank_list) == 0:
        win_game()
    elif CHANCES == 0 and not g_p1_tank:
        lose_game()

def win_game():
    global DISPLAYSURF
    DISPLAYSURF.blit(drawText('你赢了！！', 40), (320, 300))

def lose_game():
    global DISPLAYSURF
    DISPLAYSURF.blit(drawText('胜败乃兵家常事', 40), (320, 300))


def reset():
    global CHANCES, g_p1_tank, g_walls, g_wall_list, g_explode_list, g_bullet_list, g_enemy_tank_list, g_enemy_bullet_list
    g_p1_tank.live = False
    g_p1_tank.join()
    g_p1_tank = None
    g_walls.live = False
    g_walls.join()
    g_walls = None
    g_wall_list.clear()
    g_explode_list.clear()
    join_n_remove(g_enemy_tank_list)
    join_n_remove(g_bullet_list)
    join_n_remove(g_enemy_bullet_list)
    print('clear all!')
    g_p1_tank = MyTank(450, 450)
    g_p1_tank.start()
    g_walls = Walls()
    g_walls.start()
    create_enemy()
    CHANCES = 10
    print('return preset')


def join_n_remove(target_list: list):
    for index in target_list:
        index.live = False
        index.join()
    target_list.clear()


if __name__ == '__main__':
    t_bgm = threading.Thread(target=play_bgm, args=(music_path,))
    t_bgm.start()
    main()
    t_bgm.join()

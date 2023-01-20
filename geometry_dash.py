import pygame
import time
import os
import sys
import random

pygame.init()
pygame.mixer.init()

level1_music = pygame.mixer.music.load(os.path.join('data', 'stereo_madness.ogg'))

size = width, height = 500, 500
running = True
jumping = False
pixels_speed = 1
FPS = 60
clock = pygame.time.Clock()
player_size = (25, 25)

screen = pygame.display.set_mode(size)
pygame.display.set_caption('Geometry Dash Python Version')

all_sprites = pygame.sprite.Group()
vertical_borders = pygame.sprite.Group()
horizontal_borders = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
bad_tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
neutral_tiles_group = pygame.sprite.Group()
end_group = pygame.sprite.Group()
tile_width = tile_height = 25
screen_rect = (0, 0, width, height)
GRAVITY = -1


def load_level(filename):
    filename = os.path.join('data', filename)
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Start(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_image('start_button.png')
        self.image = pygame.transform.scale(self.image, (180, 180))
        self.rect = self.image.get_rect().move(170, 180)


class Custom(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_image('custom_character_button.png')
        self.image = pygame.transform.scale(self.image, (160, 160))
        self.rect = self.image.get_rect().move(170, 350)


def terminate():
    pygame.quit()
    sys.exit()


tile_images = {
    'floor': load_image('RegularBlock01.webp'),
}

bad_tile_images = {
    'spike': load_image('RegularSpike01.webp')
}

neutral_tiles_images = {
    'box': load_image('RegularBlock01.webp')
}


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group)
        self.image = tile_images[tile_type]
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.tile_type = tile_type
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.x = pos_x
        self.y = pos_y

    def update(self):
        self.rect.x -= 5


class BadTile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(bad_tiles_group)
        self.image = bad_tile_images[tile_type]
        self.image = pygame.transform.scale(self.image, (24, 24))
        self.tile_type = tile_type
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, (tile_height * pos_y) + 1)
        self.x = pos_x
        self.y = pos_y

    def update(self):
        self.rect.x -= 5


class NeutralTile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(neutral_tiles_group)
        self.image = neutral_tiles_images[tile_type]
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.tile_type = tile_type
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.x = pos_x
        self.y = pos_y

    def update(self):
        self.rect.x -= 5


class End(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(end_group)
        self.image = load_image('bg.png')
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.tile_type = tile_type
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.x = pos_x
        self.y = pos_y

    def update(self):
        self.rect.x -= 5


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = load_image('cube1.jpg')
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.rect = self.image.get_rect().move(50, screen.get_height() - 50)


player = None


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [load_image("square_particle.png")]
    for scale in (8, 9):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))
    fire.pop(0)

    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы)
        self.gravity = GRAVITY

    def update(self):
        # применяем гравитационный эффект:
        # движение с ускорением под действием гравитации
        self.velocity[0] += self.gravity
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        if random.randint(1, 2) == 2:
            self.rect.y += self.velocity[1]
        # убиваем, если частица ушла за экран
        if not self.rect.colliderect(screen_rect):
            self.kill()


particles = []


def create_particles(position):
    global particles
    # количество создаваемых частиц
    particle_count = 1
    # возможные скоростиs
    numbers = range(-4, 1)
    for _ in range(particle_count):
        particles.append(Particle(position, random.choice(numbers), random.choice(range(-4, -1))))


def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                Tile('floor', x, y)
            elif level[y][x] == '/':
                NeutralTile('box', x, y)
            elif level[y][x] == '@':
                new_player = Player(x, y)
            elif level[y][x] == '*':
                BadTile('spike', x, y)
            elif level[y][x] == '%':
                End('end', x, y)
    # вернем игрока, а также размер поля в клетках
    return new_player, x, y


player, level_x, level_y = generate_level(load_level('level1.txt'))

x, y = 0, 0
count_jump_times = 0
on_ground = True
jump_once = True
jump_strength = 7
score = 0
draw_particles = 0
count_of_height = 0
on_platform = False
slide = False
tile_collide = False
flag = True
bg_image = load_image('bg.png')
attempts = 1
def main_game():
    global running, draw_particles, jumping, on_ground, count_jump_times, attempts
    pygame.mixer.music.play()

    while running:
        draw_particles += 1
        screen.fill((0, 0, 0))
        screen.blit(bg_image, (0, 0))
        if pygame.sprite.spritecollide(player, end_group, True):
            print('You Win!')
            pygame.mixer.music.stop()
            return
        if pygame.sprite.spritecollide(player, bad_tiles_group, True):
            player.kill()
            print('Game Over!')
            running = False
            pygame.mixer.music.stop()
            pygame.mixer.music.load(os.path.join('data', 'death_sound.mp3'))
            pygame.mixer.music.play()
            attempts += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
                pygame.mixer.music.stop()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if on_ground:
                    jumping = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if on_ground:
                        jumping = True
                elif event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    return

        for tile in neutral_tiles_group:
            if player.rect.right == tile.rect.left and player.rect.bottom == tile.rect.bottom:
                player.rect.right = tile.rect.left
                print('Game Over!')
                running = False
                pygame.mixer.music.stop()
                pygame.mixer.music.load(os.path.join('data', 'death_sound.mp3'))
                pygame.mixer.music.play()
                attempts += 1
            elif player.rect.colliderect(tile.rect):
                player.rect.bottom = tile.rect.top - 4

        if jumping:
            player.rect.y -= jump_strength
            count_jump_times += 1
            if count_jump_times == 10:
                player.image = pygame.transform.rotate(player.image, -90)
                jumping = False
                count_jump_times = 0
                on_ground = False
        else:
            if not on_ground:
                player.rect.y += 3
                count_jump_times += 1
                if count_jump_times == 12:
                    count_jump_times = 0
                    draw_particles = 0
                    jump_once = True
                    y = screen.get_height() - player_size[1]
                    on_ground = True
        if draw_particles == 2 and on_ground:
            create_particles((player.rect.x, player.rect.y + player_size[1]))
            draw_particles = 0

        if not jumping:
            player.rect.bottom += 5
        if player.rect.bottom > height - 25:
            player.rect.bottom = height - 25

        font = pygame.font.Font(None, 30)
        string_rendered = font.render(f'Attempts: {attempts}', 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        intro_rect.x = 350
        intro_rect.y = 50
        screen.blit(string_rendered, intro_rect)
        tiles_group.update()
        tiles_group.draw(screen)
        bad_tiles_group.update()
        bad_tiles_group.draw(screen)
        neutral_tiles_group.update()
        neutral_tiles_group.draw(screen)
        player_group.update()
        player_group.draw(screen)
        end_group.update()
        end_group.draw(screen)
        all_sprites.update()
        all_sprites.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()


def start_screen():
    fon = pygame.transform.scale(load_image('main_menu_bg.png'), (500, 500))
    start = Start()
    pygame.mixer.music.load(os.path.join('data', 'main_menu_music.mp3'))
    pygame.mixer.music.play()
    menu = True
    while menu:
        screen.fill((0, 0, 0))
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if start.rect.collidepoint(mouse_pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pygame.mixer.music.load(os.path.join('data', 'stereo_madness.ogg'))
                    main_game()
                    menu = False
        screen.blit(fon, (0, 0))
        screen.blit(start.image, (170, 180))
        pygame.display.flip()
        clock.tick(FPS)


def custom_screen():
    fon = pygame.transform.scale(load_image('main_menu_bg.png'), (500, 500))
    start = Custom()
    menu = True
    while menu:
        screen.fill((0, 0, 0))
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if start.rect.collidepoint(mouse_pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    menu = False
        screen.blit(fon, (0, 0))
        screen.blit(start.image, (170, 350))
        pygame.display.flip()
        clock.tick(FPS)


start_screen()
while True:
    if not running:
        pygame.mixer.music.load(os.path.join('data', 'stereo_madness.ogg'))
        running = True
        screen.fill((0, 0, 0))
        size = width, height = 500, 500
        running = True
        jumping = False
        pixels_speed = 1
        FPS = 60
        clock = pygame.time.Clock()
        player_size = (25, 25)

        screen = pygame.display.set_mode(size)
        pygame.display.set_caption('Geometry Dash Python Version')

        all_sprites = pygame.sprite.Group()
        vertical_borders = pygame.sprite.Group()
        horizontal_borders = pygame.sprite.Group()
        tiles_group = pygame.sprite.Group()
        bad_tiles_group = pygame.sprite.Group()
        player_group = pygame.sprite.Group()
        neutral_tiles_group = pygame.sprite.Group()
        end_group = pygame.sprite.Group()
        tile_width = tile_height = 25
        screen_rect = (0, 0, width, height)
        GRAVITY = -1
        player, level_x, level_y = generate_level(load_level('level1.txt'))
        x, y = 0, 0
        count_jump_times = 0
        on_ground = True
        jump_once = True
        jump_strength = 7
        score = 0
        draw_particles = 0
        count_of_height = 0
        on_platform = False
        slide = False
        tile_collide = False
        flag = True
        bg_image = load_image('bg.png')
        main_game()
    else:
        pygame.mixer.music.load(os.path.join('data', 'stereo_madness.ogg'))
        running = True
        screen.fill((0, 0, 0))
        size = width, height = 500, 500
        running = True
        jumping = False
        pixels_speed = 1
        FPS = 60
        clock = pygame.time.Clock()
        player_size = (25, 25)

        screen = pygame.display.set_mode(size)
        pygame.display.set_caption('Geometry Dash Python Version')

        all_sprites = pygame.sprite.Group()
        vertical_borders = pygame.sprite.Group()
        horizontal_borders = pygame.sprite.Group()
        tiles_group = pygame.sprite.Group()
        bad_tiles_group = pygame.sprite.Group()
        player_group = pygame.sprite.Group()
        neutral_tiles_group = pygame.sprite.Group()
        end_group = pygame.sprite.Group()
        tile_width = tile_height = 25
        screen_rect = (0, 0, width, height)
        GRAVITY = -1
        player, level_x, level_y = generate_level(load_level('level1.txt'))
        x, y = 0, 0
        count_jump_times = 0
        on_ground = True
        jump_once = True
        jump_strength = 7
        score = 0
        draw_particles = 0
        count_of_height = 0
        on_platform = False
        slide = False
        tile_collide = False
        flag = True
        bg_image = load_image('bg.png')
        attempts = 1
        start_screen()

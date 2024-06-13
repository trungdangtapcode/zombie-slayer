import pygame
from settings import *
from tile import Tile
from player import Player
import system
from os import walk
import file
from math import sqrt, exp2, pi, cos, sin
phi = ( 1 + sqrt(5) ) / 2
from weapon import Weapon, Gun, FlameThrower
from bullet import Bullet, FlameBullet, Missile
from enemy import Zombie, Bat, FlyingSword, Skeleton
from ui import UI, Button, Text, Font
from particle import Blood, FlamePariticle
from random import uniform
from sound import Playlist

#render layers:
# - background tile
# - tile1
# - particle1
# - object1
# - player -> ob -> pa -> ti -> GUI
render_layers = {
    'bg': 0, 't1': 1, 'p1': 2, 'o1': 3, 'pl': 4,
    'o2': 5, 'p2': 6, 't2': 7, 'UI': 8
}

class Level():
    """
    Represents a game level with various entities including the player, enemies, 
    visible and obstacle sprites, and other elements necessary for gameplay.

    Attributes:
        screen: The main display surface from the system.
        visible_sprites: A YSortCameraGroup instance managing sprites to be rendered.
        obstacle_sprites: A Pygame sprite group for obstacles in the level.
        ui: The user interface associated with the level.
        light_image: The light effect image used for rendering lighting effects.
        is_end: Boolean indicating if the level has ended.
        sprite_sheet: The sprite sheet containing level tiles.
        player: The player character in the level.
        enemies: A list of enemy instances in the level.
        darkness_value: An integer representing the current level of darkness.
    
    Methods:
        create_map(): Sets up the level by loading the map, obstacles, and enemies.
        update(): Updates and renders the level, handles input, and manages the game state.
        loss(): Placeholder method for handling level loss conditions.
        victory(): Placeholder method for handling level victory conditions.
        check_win(): Checks if all enemies are defeated.
        create_weapon(player, name, type=''): Creates a weapon for the player.
        destroy_weapon(player): Destroys the player's current weapon.
        create_bullet(weapon, type='bullet'): Creates a bullet or projectile.
        create_blood(pos, zindex=2): Creates a blood effect at a given position.
        create_flame_particle(pos, zindex=2): Creates a flame particle effect at a given position.
    """
    def __init__(self, level='xx', music_file = 'level.wav'):
        self.screen = system.screen
        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()
        self.level = level
        self.create_map()
        self.ui = UI(self.player)

        light_path = PATH + 'graphics/light/light.png'
        self.light_image = pygame.image.load(light_path)

        system.level = self
        self.is_end = False

        BGM_PATH = PATH + 'sound/' + music_file
        pygame.mixer.music.load(BGM_PATH)
        pygame.mixer.music.play(-1)
        self.loss_sound = pygame.mixer.Sound(PATH + 'sound/death.wav')
        self.victory_sound = pygame.mixer.Sound(PATH + 'sound/victory.wav')

        self.transition_time = 1.5
        self.current_transition_in = self.transition_time
        self.current_transition_out = self.transition_time
        self.is_loss = False
        self.current_transition_loss = self.transition_time
        self.loss_screen_time = self.transition_time + 4
        self.loss_screen_current_time = self.loss_screen_time
        self.is_victory = False
        self.victory_time = 5
        self.victory_current_time = self.victory_time

    def create_map(self, player_pos = (400,400)):
        level = self.level
        room_id = 0 #wolrd, level, map, scene, room
        level_path = PATH + 'level/' + level + '/' + str(room_id) + '/'
        visible_path = level_path + 'visible/'
        obstacle_path = level_path + 'obstacle/'
        enemy_path = level_path + 'enemy/'

        #this is level tile sheet
        self.sprite_sheet = file.SpriteSheet(level_path+'sheet.png',TILESIZE,TILESIZE)

        for _,__,csv_files in walk(visible_path):
            for zindex, filename in enumerate(csv_files):
                layout = file.import_csv_layout(visible_path+filename)
                for row_index,row in enumerate(layout):
                    for col_index, col in enumerate(row):
                        idx = int(col) #tile index frame
                        if (idx==-1):
                            continue
                        x = col_index*TILESIZE
                        y = row_index*TILESIZE
                        Tile((x,y),[self.visible_sprites],self.sprite_sheet.get_image(idx),zindex)

        for _,__,csv_files in walk(obstacle_path):
            for zindex, filename in enumerate(csv_files):
                layout = file.import_csv_layout(obstacle_path+filename)
                for row_index,row in enumerate(layout):
                    for col_index, col in enumerate(row):
                        idx = int(col) #tile index frame
                        if (idx==-1):
                            continue
                        x = col_index*TILESIZE
                        y = row_index*TILESIZE
                        Tile((x,y),[self.obstacle_sprites],self.sprite_sheet.get_image(idx),zindex)

        self.player = Player(player_pos,[self.visible_sprites], self.obstacle_sprites, 1)
        self.enemies = []

        enemy_lst = [Zombie, Bat, Skeleton]
        for _,__,csv_files in walk(enemy_path):
            for zindex, filename in enumerate(csv_files):
                layout = file.import_csv_layout(enemy_path+filename)
                for row_index,row in enumerate(layout):
                    for col_index, col in enumerate(row):
                        idx = int(col) #tile index frame
                        if (idx==-1):
                            continue
                        x = col_index*TILESIZE
                        y = row_index*TILESIZE
                        enemy = enemy_lst[idx]((x,y),[self.visible_sprites], self.obstacle_sprites, self.player)
                        self.enemies.append(enemy)

        # self.visible_sprites.box = Tile((0,0),[self.visible_sprites],pygame.image.load('oop/image/test/rock.png').convert_alpha(),100)

        # self.enemies = []
        # self.enemies = [Skeleton((700,600),[self.visible_sprites], self.obstacle_sprites, self.player)]
        # self.enemies = [FlyingSword((1700,1600),[self.visible_sprites], self.obstacle_sprites, self.player)]
        # self.enemies = [Bat((500,500),[self.visible_sprites], self.obstacle_sprites, self.player)]
        # self.enemies = [Zombie((900,800),[self.visible_sprites], self.obstacle_sprites, self.player)]
        # Zombie((600,500),[self.visible_sprites], self.obstacle_sprites, self.player)
        # self.enemies = [Zombie((xpos,500),self.visible_sprites, self.obstacle_sprites, self.player)
        #                 for xpos in [500,600,700, 800, 900]]
        
        self.darkness_value = 120

    def update(self):
        self.visible_sprites.custom_draw(self.player)
        if (not self.is_end): self.visible_sprites.update()

        filter = pygame.surface.Surface(self.screen.get_size())
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFTBRACKET]: 
            self.darkness_value -= 10
            self.darkness_value = max(self.darkness_value,0)
        if keys[pygame.K_RIGHTBRACKET]:
            self.darkness_value += 10
            self.darkness_value = min(self.darkness_value,255)
        # self.darkness_value = 0
        if (self.darkness_value>0):
            color = (self.darkness_value,self.darkness_value,self.darkness_value,255)
            filter.fill(color)
            obj = pygame.sprite.Sprite()
            obj.image = self.light_image
            obj.rect = pygame.rect.Rect((0,0), (1000,1000))
            obj.rect.center = self.player.hitbox.center
            self.visible_sprites.draw_sprite(obj, filter)
            self.screen.blit(filter, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        if system.mouse_scroll == 1:
            if (self.visible_sprites.zoom_out_scale>0.2*2): self.visible_sprites.zoom_out_scale -= 0.1
        if system.mouse_scroll == -1:
            if (self.visible_sprites.zoom_out_scale<4): self.visible_sprites.zoom_out_scale += 0.1
        self.ui.display()
        self.update_transition_in()
        self.update_loss_screen()
        self.update_victory()

        if (keys[pygame.K_ESCAPE]):
            system.go_to_level()

        if (self.check_win()):
            self.victory()
    
    def update_transition_in(self):
        if (self.current_transition_in<=0):
            return
        self.current_transition_in -= system.delta_time

        ratio = 1-self.current_transition_in/self.transition_time
        radius = pygame.math.Vector2(self.screen.get_size()).magnitude()/2*(1.5)*ratio
        transition_surf = pygame.Surface(self.screen.get_size())
        pygame.draw.circle(transition_surf, (255, 255, 255), 
            pygame.math.Vector2(self.screen.get_size())/2, radius)
        transition_surf.set_colorkey((255, 255, 255))
        self.screen.blit(transition_surf, (0,0))

    def loss(self):
        self.is_loss = True
        self.is_end = True
        pygame.mixer.music.stop()
        self.loss_sound.play()

    def update_loss_screen(self):
        if (not self.is_loss): return
        if (self.loss_screen_current_time<=0):
            system.go_to_level('restart')
            return
        self.loss_screen_current_time -= system.delta_time
        self.current_transition_loss -= system.delta_time
        self.current_transition_loss = max(self.current_transition_loss,0)
        ratio = 1-self.current_transition_loss/self.transition_time
        radius = pygame.math.Vector2(self.screen.get_size()).magnitude()/2*1.5*ratio
        transition_surf = pygame.Surface(self.screen.get_size()).convert_alpha()
        pygame.draw.circle(transition_surf, (255, 0, 0, 255), 
            pygame.math.Vector2(self.screen.get_size())/2, radius)
        transition_surf.set_colorkey((0,0,0))
        self.screen.blit(transition_surf, (0,0))
    
    def update_transition_out(self):
        if (self.current_transition_out<=0):
            system.go_to_level('next')
        self.current_transition_out -= system.delta_time
        self.current_transition_out = max(self.current_transition_out, 0)

        ratio = self.current_transition_out/self.transition_time
        radius = pygame.math.Vector2(self.screen.get_size()).magnitude()/2*(1.5)*ratio
        transition_surf = pygame.Surface(self.screen.get_size())
        pygame.draw.circle(transition_surf, (255, 255, 255), 
            pygame.math.Vector2(self.screen.get_size())/2, radius)
        transition_surf.set_colorkey((255, 255, 255))
        self.screen.blit(transition_surf, (0,0))

    def update_victory(self):
        if (not self.is_victory): return
        if (self.victory_current_time<=0):
            self.update_transition_out()
            return
        self.victory_current_time -= system.delta_time


    def victory(self):
        if (self.is_victory): return
        self.is_victory = True
        pygame.mixer.music.stop()
        self.victory_sound.play()

    def check_win(self):
        for target in self.enemies:
            if (not target.is_dead): return False
        return True

    def create_weapon(self,player,name, type=''):
        if (player.current_weapon): return
        if (type=='gun'):
            player.current_weapon = Gun(player,[self.visible_sprites],self.create_bullet, name, player.zindex)
        else: player.current_weapon = FlameThrower(player,[self.visible_sprites],self.create_bullet, name, player.zindex)

    def destroy_weapon(self,player):
        if player.current_weapon:
            player.current_weapon.kill()
        player.current_weapon = None

    def create_bullet(self,weapon,type='bullet'):
        if (type=='bullet'):
            Bullet([self.visible_sprites],weapon, self.obstacle_sprites, weapon.zindex)
        elif (type=='flamebullet'): 
            FlameBullet([self.visible_sprites],weapon, self.obstacle_sprites, weapon.zindex)
        else:
            Missile([self.visible_sprites],weapon, self.obstacle_sprites, weapon.zindex)
    def create_blood(self, pos, zindex = 2):
        Blood([self.visible_sprites],pos)

    def create_flame_particle(self, pos, zindex = 2):
        FlamePariticle([self.visible_sprites], pos)

class YSortCameraGroup(pygame.sprite.Group):
    """
    Dynamic top-down camera with rendering priority based on z-index and y-coordinate.

    Methods:
        mouse_world_position(): Gets the current mouse position in the world's coordinate system.
        custom_draw(player): Draws sprites and updates the camera position based on the player.
        draw_sprite(sprite, screen=None): Transforms the sprite's image and blits it to the screen.
        screen_shake(swing): Shakes the screen by a specified magnitude.
    """
    def __init__(self): 
        super().__init__()
        self.screen = system.screen
        self.half_width = self.screen.get_size()[0] // 2
        self.half_height = self.screen.get_size()[1] // 2
        self.offset = pygame.math.Vector2()
        self.zoom_out_scale = 1
        self.pos = pygame.math.Vector2(0,0)
        self.velocity = pygame.math.Vector2(0,0)
        self.force_to_dest = 15
        self.decay_fiction_halflife = 0.3

        self.current_shake = 0
        self.shake_recover = 20

        system.camera = self

    def mouse_wolrd_position(self):
        mouse = pygame.math.Vector2(pygame.mouse.get_pos())
        mouse = mouse*self.zoom_out_scale + pygame.math.Vector2(self.offset)
        return mouse

    def custom_draw(self,player):
        #update camera position
        player_pos = pygame.math.Vector2(player.rect.centerx,player.rect.centery)
        mouse = self.mouse_wolrd_position()
        dest_pos = mouse-(mouse - player_pos)/1.2 #not aiming
        if (pygame.mouse.get_pressed()[2]): #aiming
            dest_pos = mouse-(mouse - player_pos)/phi
        force = self.force_to_dest*(dest_pos-self.pos)
        self.velocity += system.delta_time*force
        self.velocity *= exp2(-system.delta_time/self.decay_fiction_halflife)
        self.pos += system.delta_time*self.velocity
        
        #offset = topleft start rendering
        self.offset.x = self.pos.x - self.half_width*self.zoom_out_scale
        self.offset.y = self.pos.y - self.half_height*self.zoom_out_scale
        
        for sprite in sorted(self.sprites(),key = lambda sprite: sprite.zindex*10**9+sprite.rect.centery):
            self.draw_sprite(sprite)

        #shake
        angle = uniform(-pi, pi)
        vec_shake = pygame.math.Vector2(cos(angle),sin(angle))
        self.pos += vec_shake*self.current_shake
        self.current_shake -= system.delta_time*self.shake_recover
        self.current_shake = max(self.current_shake, 0)
        
    def draw_hit_box(self,player):
        self.box.rect = player.hitbox
        self.box.image = pygame.transform.scale(self.box.image,player.hitbox.size)
        self.draw_sprite(self.box)

    def draw_box(self, rect: pygame.Rect):
        x = pygame.sprite.Sprite()
        x.rect = rect
        x.image = pygame.surface.Surface(rect.size)
        x.image.fill((255,0,0))
        self.draw_sprite(x)

    def draw_sprite(self,sprite, screen = None):
        if hasattr(sprite, 'is_disable') and sprite.is_disable:
            return
        offset_pos = sprite.rect.topleft - self.offset
        offset_pos = (offset_pos[0]/self.zoom_out_scale,offset_pos[1]/self.zoom_out_scale)
        new_size = sprite.rect.size # sprite.image.get_size()
        new_size = (new_size[0]/self.zoom_out_scale,new_size[1]/self.zoom_out_scale)

        #check before render because lag when zoom, screen_relative_rect
        if (not self.screen.get_rect().colliderect(pygame.Rect(offset_pos, new_size))): return
        scaled_image = pygame.transform.scale(sprite.image,new_size)
        if (screen == None): screen = self.screen
        screen.blit(scaled_image,offset_pos)


    def screen_shake(self, swing):
        self.current_shake = max(self.current_shake, swing)

class Level00(Level):
    def __init__(self, level='testing_level', music_file = 'level.wav'):
        super().__init__(level, music_file)

class Level01(Level):
    def __init__(self, level='grass_level', music_file = 'level_high.wav'):
        super().__init__(level, music_file)
        self.player.health = 100

class MenuScreen:
    """
    A class to represent the menu screen of the game.

    Attributes
    ----------
    screen : Surface
        The display surface where the menu elements are drawn.
    PLAY_TEXT : Text
        A text object displaying the game title.
    LEVEL0_BUTTON : Button
        A button object for selecting Level 00.
    LEVEL1_BUTTON : Button
        A button object for selecting Level 01.
    LEVEL2_BUTTON : Button
        A button object for selecting Level 02.

    Methods
    -------
    __init__():
        Initializes the menu screen with the title text and level selection buttons.
    update(display=True):
        Updates the display with the current state of the menu screen.
    draw_prite(sprite):
        Draws a sprite (text) on the screen.
    draw_button(button):
        Draws a button on the screen and handles its updates.
    """
    def __init__(self):
        self.screen = system.screen
        half_w = SCREEN_WIDTH/2

        self.PLAY_TEXT = Text("ZOMBIE SLAYER", 60, "White", center = (half_w, 100))
        self.LEVEL0_BUTTON = Button(margin = 10, bg_color = (100,100,100), center = (half_w, 200), 
                            text_input="LEVEL 01", font=Font.get_font(30), base_color="#d7fcd4", hovering_color="#801010")
        self.LEVEL1_BUTTON = Button(margin = 10, bg_color = (100,100,100), center = (half_w, 300), 
                            text_input="LEVEL 02", font=Font.get_font(30), base_color="#d7fcd4", hovering_color="#801010")
        self.LEVEL2_BUTTON = Button(margin = 10, bg_color = (100,100,100), center = (half_w, 400), 
                            text_input="EXIT", font=Font.get_font(30), base_color="#d7fcd4", hovering_color="#801010")
        
        THEME_PATH = PATH + 'sound/main_theme_cutted.wav'
        pygame.mixer.music.load(THEME_PATH)
        pygame.mixer.music.play(-1)

        self.bg = pygame.image.load(PATH + 'graphics/main_background.png')
        self.bg = pygame.transform.scale(self.bg, self.screen.get_size())

    def update(self, display = True):
        self.screen.blit(self.bg, (0,0))
        PLAY_TEXT = self.PLAY_TEXT
        LEVEL0_BUTTON = self.LEVEL0_BUTTON
        LEVEL1_BUTTON = self.LEVEL1_BUTTON
        LEVEL2_BUTTON = self.LEVEL2_BUTTON

        self.draw_prite(PLAY_TEXT)
        self.draw_button(LEVEL0_BUTTON)
        self.draw_button(LEVEL1_BUTTON)
        self.draw_button(LEVEL2_BUTTON)

        mouse = pygame.mouse.get_pos()
        if (pygame.mouse.get_pressed()[0]):
            if LEVEL0_BUTTON.checkForInput(mouse):
                pygame.mixer.music.stop()
                system.go_to_level(0)
                LEVEL0_BUTTON.disable()
            if LEVEL1_BUTTON.checkForInput(mouse):
                pygame.mixer.music.stop()
                system.go_to_level(1)
                LEVEL1_BUTTON.disable()
            if LEVEL2_BUTTON.checkForInput(mouse):
                pygame.mixer.music.stop()
                system.go_to_level('exit')
                LEVEL2_BUTTON.disable()

    def draw_prite(self, sprite):
        self.screen.blit(sprite.image, sprite.rect)

    def draw_button(self, button):
        button.update(self.screen)
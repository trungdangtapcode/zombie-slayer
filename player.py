import pygame
from settings import *
import system
import file
from math import atan2
from math import pi
from item import GunItemInventory, FlameThrowerItemInventory, MissileLaucherItemInventory, FoodItemInventory

#Player anim 4 direction (dirname): 0(N), 1(E), 2(S), 3(W)
dirname_to_angle = [pi/2,0,-pi/2,pi]
def angle_distance(a, b):
    return min(abs(a-b),abs(a-b+2*pi),abs(a-b-2*pi))
def vector_to_angle(v): 
    return atan2(v.y,v.x)

class Player(pygame.sprite.Sprite):
    """
    Represents the player character in the game.

    Attributes:
        character_namedir (str): Directory name for the character's assets.
        speed (int): Normal movement speed of the player.
        sprint_speed_ahead (int): Sprinting speed when moving forward.
        sprint_speed (int): Sprinting speed.
        current_speed (int): Current speed of the player.
        animation_speed (float): Speed at which the player's animation progresses.
        max_health (int): Maximum health of the player.
        health (int): Current health of the player.
        frame_index (float): Current frame index for the animation.
        image (Surface): Current image of the player.
        rect (Rect): Rectangular area representing the player's position and size.
        zindex (int): Rendering priority of the player.
        current_weapon (Weapon): The player's current weapon.
        direction (Vector2): Direction the player is moving.
        facing_direction (Vector2): Direction the player is facing.
        pos (tuple): Initial position of the player.
        obstacle_sprites (iterable): Sprites representing obstacles.
        hitbox (Rect): Rectangular hitbox for collision detection.
        hitbox_shift (int): Shift value for the hitbox.
        dirname (int): Direction index for animation.
        anim_state (str): Current animation state.
        is_reloading (bool): Whether the player is reloading a weapon.
        is_eating (bool): Whether the player is eating.
        current_food (Food): The player's current food item.
        inventory (list): List of items in the player's inventory.
        current_primary (int): Index of the current primary item in the inventory.
        process_bar (ProcessBar): Process bar for displaying reloading/eating progress.

    Methods:
        import_player_assets(): Imports player animation assets.
        input(): Handles player input for movement and actions.
        get_heal(hp): Increases the player's health.
        disable_primary(skip_cheat): Disables the current primary item.
        choose_primary(slot, skip_cheat): Chooses a primary item from the inventory.
        move(): Handles player movement and collision.
        collision_check(): Checks for collisions with obstacles.
        animate(): Animates the player based on the current state.
        get_damage(damage, is_direct): Applies damage to the player.
        calculate_taken_damage(damage): Calculates the damage taken by the player.
        kill(): Handles player death.
        update_bar(): Updates the process bar for reloading/eating progress.
        update(): Updates the player's state.
    """
    def __init__(self,pos,groups, obstacle_sprites, zindex = 0):
        super().__init__(groups)
        
        self.character_namedir = 'adam'
        self.speed = 100
        self.sprint_speed_ahead = 300
        self.sprint_speed = 200
        self.current_speed = 0
        self.animation_speed = 7 #0.15
        self.max_health = 200
        self.health = 200
        self.frame_index = 0
        self.image = pygame.image.load('oop/image/test/player2.png').convert_alpha()
        self.import_player_assets()

        self.rect = self.image.get_rect(topleft = pos)
        self.zindex = zindex
        # self.create_weapon = create_weapon
        # self.destroy_weapon = destroy_weapon
        # self.create_bullet = create_bullet
        self.current_weapon = None
        self.direction = pygame.math.Vector2()
        self.facing_direction = pygame.math.Vector2()
        self.pos = pos
        self.obstacle_sprites = obstacle_sprites
        self.hitbox = self.rect.inflate(-75,-75) ###
        self.hitbox_shift = 20
        self.dirname = 1
        self.anim_state = 'idle'
        self.is_reloading = False
        self.is_eating = False
        self.current_food = None

        # self.inventory = [GunItemInventory(groups,self),
        #             FlameThrowerItemInventory(groups,self),
        #             GunItemInventory(groups,self,name='bluetagon')]
        self.inventory = [GunItemInventory(groups,self), 
                    FlameThrowerItemInventory(groups,self),
                    MissileLaucherItemInventory(groups,self),
                    FoodItemInventory(groups, self, 'bread'),
                    GunItemInventory(groups,self,name='bluetagon'),
                    FoodItemInventory(groups, self, 'icescream')]
        self.current_primary = -1

        self.process_bar = ProcessBar(groups, self)

        self.path = PATH + 'graphics/player/' + self.character_namedir + '/'
        self.taking_damage_sound = pygame.mixer.Sound(self.path + 'taking_damage.wav')

    def import_player_assets(self):
        character_path = PATH + 'graphics/player/' + self.character_namedir + '/'
        self.animations = {'idle':[], 'walking':[]}
        for animation in self.animations.keys():
            for dir in range(4):
                full_path = character_path + animation + '/' + str(dir) + '/'
                self.animations[animation].append(file.import_folder(full_path))

    def input(self):
        #direction update
        keys = pygame.key.get_pressed()
        self.direction.x = keys[pygame.K_d]-keys[pygame.K_a]
        self.direction.y = keys[pygame.K_s]-keys[pygame.K_w]
        if (self.direction.magnitude()!=0):
            self.direction = self.direction.normalize()
        
        #facing direction
        mouse = system.camera.mouse_wolrd_position()
        self.facing_direction= mouse-self.rect.center
        if (self.facing_direction.magnitude()!=0):
            self.facing_direction = self.facing_direction.normalize()

        #update dirname, in rad
        angle = -atan2(self.facing_direction.y,self.facing_direction.x) #camera y dimension is reverse with world coor (camera.y ~ -coor.y)
        #make a hard mouse move to turn :D
        if (angle_distance(angle,dirname_to_angle[self.dirname])>=pi/4+pi/12):
            if (min(abs(angle),pi-abs(angle))<=pi/4):
                if (abs(angle)>pi/2):
                    self.dirname = 3
                else: self.dirname = 1
            else:
                if (angle>0):
                    self.dirname = 0
                else: self.dirname = 2

        #weapon update
        for num in range(0,9):
            key = pygame.K_1+num
            if (keys[key]):
                self.choose_primary(num)
                break

        if (keys[pygame.K_BACKQUOTE]):
            self.disable_primary()
                
        # if (keys[pygame.K_l]):
        #     system.level.destroy_weapon(self)
        #     system.level.create_weapon(self,'flamethrower', 'flamethrower')

        if (pygame.mouse.get_pressed()[0]):
            if (self.current_weapon):
                self.current_weapon.shoot()
            if (self.current_food):
                self.current_food.eat()

        if (self.current_food and
            self.current_food.quantity==0 and
            self.current_food.eating_current_time==0):
            self.inventory.pop(self.current_primary)
            self.choose_primary(self.current_primary, skip_cheat=True)
        
        if (keys[pygame.K_r] and self.current_weapon):
            self.current_weapon.reload()

    def get_heal(self, hp):
        self.health += hp
        self.health = min(self.health,self.max_health)

    def disable_primary(self, skip_cheat = False):
        if ((self.is_eating or self.is_reloading) and not skip_cheat): return #avoid cheat
        if (self.current_primary == -1): return
        if (self.current_primary<len(self.inventory)):
            self.inventory[self.current_primary].disable()
        self.current_weapon = None
        self.current_food = None
        self.current_primary = -1

    def choose_primary(self, slot, skip_cheat = False):
        # commented, because if inventorty change choose that slot still necessary for update
        # if (self.current_primary == slot): return
        self.disable_primary(skip_cheat=skip_cheat)
        if ((self.is_eating or self.is_reloading) and not skip_cheat): return #avoid cheat
        if (slot>=len(self.inventory) or slot < 0): 
            self.current_primary = slot
            return
        self.current_primary = slot
        self.inventory[slot].activate()
        if (hasattr(self.inventory[slot], 'weapon')):
            self.current_weapon = self.inventory[slot].weapon
        elif (hasattr(self.inventory[slot], 'food')):
            self.current_food = self.inventory[slot].food

    def move(self):
        keys = pygame.key.get_pressed()

        #movement
        self.is_eating = (self.current_food!=None 
                    and self.current_food.is_eating)
        self.is_reloading = (self.current_weapon!=None 
                    and self.current_weapon.is_reloading)
        is_sprinting = keys[pygame.K_LSHIFT] \
            and not self.is_reloading and not self.is_eating
        is_ahead = angle_distance(vector_to_angle(self.direction),vector_to_angle(self.facing_direction))<=pi/3
        speed = (self.sprint_speed if is_sprinting else self.speed)
        self.current_speed = speed
        if (is_sprinting and is_ahead): speed = self.sprint_speed_ahead
        if (self.direction.magnitude()!=0):
            self.anim_state = 'walking'
            self.direction = self.direction.normalize()
        else: self.anim_state = 'idle'
        self.is_sprinting = keys[pygame.K_LSHIFT]

        #collision
        self.hitbox.x  += self.direction.x*system.delta_time*speed
        if self.collision_check(): self.hitbox.x  -= self.direction.x*system.delta_time*speed
        self.hitbox.y  += self.direction.y*system.delta_time*speed
        if self.collision_check(): self.hitbox.y  -= self.direction.y*system.delta_time*speed
        self.rect.center = self.hitbox.center
        self.rect.centery -= self.hitbox_shift
    
    def collision_check(self):
        # return pygame.sprite.spritecollide(self, self.obstacle_sprites, False, pygame.sprite.collide_mask)
        for sprite in self.obstacle_sprites:
            if not self.hitbox.colliderect(sprite.rect): continue
            return True
        return False
    
    def animate(self):
        
        animation = self.animations[self.anim_state][self.dirname]

        self.frame_index += self.animation_speed*system.delta_time
        if self.frame_index >= len(animation):
            self.frame_index = 0
        
        self.image = animation[int(self.frame_index)]
        # self.rect = self.image.get_rect(center = self.hitbox.center)

    def get_damage(self, damage, is_direct = True):
        dmg = damage if is_direct else self.calculate_taked_damge(damage)
        self.health -= dmg
        self.health = max(self.health, 0)
        if (self.health==0): self.kill()
        system.camera.screen_shake(10)
        self.taking_damage_sound.play()

    def calculate_taken_damge(self, damage):
        return 0

    def kill(self):
        system.level.loss()
        print("YOU DIE BITCH")
        self.health = self.max_health

    def update_bar(self):
        bar = self.process_bar
        if (self.is_reloading):
            bar.is_display = True
            weapon = self.current_weapon
            bar.ratio = 1-weapon.reloading_current_time/weapon.reloading_time
            return
        if (self.is_eating):
            bar.is_display = True
            food = self.current_food
            bar.ratio = 1-food.eating_current_time/food.eating_time
            return
        bar.is_display = False
        
        

    def update(self):
        self.input()
        self.move()
        self.animate()
        self.update_bar()
        # if (self.current_weapon):
        #     self.health = self.current_weapon.stability
        #     self.max_health = self.current_weapon.max_stability

class ProcessBar(pygame.sprite.Sprite):
    '''
    Represents a process bar for displaying progress such as reloading or eating.

    Attributes:
        BAR_BG_COLOR (tuple): Background color of the bar.
        BAR_COLOR (tuple): Foreground color of the bar.
        BAR_WIDTH (int): Width of the bar.
        BAR_HEIGHT (int): Height of the bar.
        bg_image (Surface): Background image of the bar.
        is_display (bool): Whether the bar is currently displayed.
        ratio (float): Progress ratio (0 to 1) displayed by the bar.
        shift_up (int): Vertical shift value for positioning the bar.
        shift (Vector2): Vector for shifting the bar's position.
        image (Surface): Current image of the process bar.
        rect (Rect): Rectangular area representing the bar's position and size.
        zindex (int): Rendering priority of the process bar.
        player (Player): Reference to the player object.

    Methods:
        update_display(): Updates the bar's display based on the current ratio.
        update(): Updates the bar's state.
    '''
    def __init__(self, groups, player: Player):
        super().__init__(groups)
        self.BAR_BG_COLOR = (0,0,0,200)
        self.BAR_COLOR = (255,255,153,255)
        self.BAR_WIDTH = 80
        self.BAR_HEIGHT = 6
        self.bg_image = pygame.surface.Surface((self.BAR_WIDTH,self.BAR_HEIGHT))
        self.is_display = True
        self.ratio = 0.5

        self.shift_up = 80
        self.shift = pygame.math.Vector2(0,-self.shift_up)
        self.image = pygame.surface.Surface((1,1))
        self.image = self.bg_image
        self.rect = self.image.get_rect(center = player.hitbox.center+self.shift)
        self.zindex = 2

        self.player = player

    def update_display(self):
        self.rect.center = self.player.hitbox.center+self.shift
        self.image = self.bg_image.copy()

        current_width = self.ratio*self.BAR_WIDTH
        bar_rect = pygame.rect.Rect((0,0),(current_width,self.BAR_HEIGHT))
        pygame.draw.rect(self.image, self.BAR_COLOR, bar_rect)

    def update(self):
        if (self.is_display):
            self.is_disable = False
            self.update_display()
        else:
            self.is_disable = True

        
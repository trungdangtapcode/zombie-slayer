import pygame
from settings import *
import system
from numpy import random
import file
from sound import Playlist

class BasedZombie(pygame.sprite.Sprite):
    """
    Base class for zombie enemies.

    Attributes:
        pos (pygame.Vector2): Position vector.
        player: Reference to the player object.
        obstacle_sprites: List of obstacle sprites.
        speed_scale (float): Scaling factor for speed.
        speed (int): Base movement speed.
        trigger_speed (int): Speed when triggered.
        current_speed (int): Current movement speed.
        distance_to_follow (int): Distance within which the zombie follows the player.
        target_point (pygame.Vector2): Point towards which the zombie moves.
        direction (pygame.Vector2): Direction vector.
        standing_time (float): Time the zombie stands still.
        current_standing_time (float): Current standing time.
        prob_standing (float): Probability of standing still.
        on_trigger (bool): Flag indicating if the zombie is triggered.
        attack_range (int): Range of attack.
        attack_range_trigger (int): Range for triggering an attack.
        attack_cooldown (float): Cooldown between attacks.
        attack_cooldown_std (float): Standard deviation for attack cooldown.
        attack_current_cooldown (float): Current attack cooldown.
        is_attacking (bool): Flag indicating if the zombie is attacking.
        attack_anim_start (bool): Flag indicating the start of attack animation.
        dealing_damage_yet (bool): Flag indicating if the zombie has dealt damage yet.
        attack_damage_after (float): Delay after which damage is dealt during an attack.
        attack_damage_after_limit (float): Upper limit of damage dealing delay.
        is_getting_damage (bool): Flag indicating if the zombie is receiving damage.
        getting_damage_delay (float): Delay for receiving damage.
        getting_damage_current_delay (float): Current delay for receiving damage.
        max_health (int): Maximum health points.
        current_health (int): Current health points.
        is_dead (bool): Flag indicating if the zombie is dead.
        corpse_despawn_time (float): Time after which the corpse despawns.
        corpse_despawn_current_time (float): Current time for corpse despawn.
        animations (dict): Dictionary containing animation frames.
        damage (int): Damage inflicted by the zombie.
        is_though_wall (bool): Flag indicating if the zombie can walk through walls.
        wandering_distance (int): Distance the zombie wanders randomly.
        image: Surface representing the zombie's image.
        rect: Rectangle representing the zombie's position and size.
        hitbox: Rectangle representing the zombie's hitbox.
        zindex (int): Z-index for rendering.
        shift_y (int): Vertical shift for image.
        shift (pygame.Vector2): Shift vector for image.

    Methods:
        target_sight_check: Check if the target is in sight of the zombie.
        find_2nd_target: Find a secondary target.
        get_random_target_point: Get a random target point for wandering.
        check_collision: Check collision with obstacles.
        cancel_trigger: Cancel the trigger if not chasing something.
        move: Move the zombie.
        attack: Perform an attack.
        dead_animation: Perform death animation.
        update_animation: Update the zombie's animation.
        get_damage: Receive damage.
        die: Execute death sequence.
        update: Update the zombie's behavior.
        bleed: Emit blood particles.
        load_assets: Load zombie assets.
    """
    def __init__(self, pos, groups, obstacle_sprites, player, zindex = 1):
        super().__init__(groups)
        self.pos = pygame.Vector2(pos)
        self.player = player
        self.obstacle_sprites = obstacle_sprites

        self.speed_scale = 1 #traits
        self.speed = 50
        self.trigger_speed = 150
        self.current_speed = self.speed
        self.distance_to_follow = 800
        self.target_point = self.pos
        self.direction = pygame.Vector2(0,0)
        self.standing_time = 1.5
        self.currnet_standing_time = 0 #go to 0 mean zombie can move
        self.prob_standing = 0.5
        self.on_trigger = False
        self.attack_range = 100
        self.attack_range_trigger = 20
        self.attack_cooldown = 2
        self.attack_cooldown_std = .5
        self.attack_current_cooldown = 0
        self.is_attacking = False
        self.attack_anim_start = False
        self.dealing_damage_yet = False
        self.attack_damage_after = 0.5
        #avoid getting damge after 2s (cooldown, anim end so far)
        self.attack_damage_after_limit = 0.6
        self.is_getting_damage = True
        self.getting_damage_delay = 0.05
        self.getting_damage_current_delay = 0
        self.max_health = 69
        self.current_health = self.max_health
        self.is_dead = False
        self.corpse_despawn_time = 2
        self.corpse_despawn_current_time = 0
        self.animations = {}
        self.damage = 0

        self.is_though_wall = False #ability to walk though wall
        self.wandering_distance = 200

        self.scream_cooldown = 3
        self.scream_cooldown_std = 1
        self.scream_current_cooldown = self.scream_cooldown+random.uniform(-1,1)*self.scream_cooldown_std

        self.image = pygame.Surface(size = (80,80))
        self.image.fill((255,0,0))
        self.rect = self.image.get_rect(topleft = self.pos)
        self.rect.size = (64,64)
        self.hitbox = self.rect
        self.zindex = zindex
        #image shift down
        self.shift_y = 0
        self.shift = pygame.math.Vector2(0,self.shift_y)

    def target_sight_check(self, target_pos, self_pos = None, coef = None):
        """the shape is a isosceles trapezoid not collide with any obstacle
        and check if is closed 
        """
        if (self_pos==None):
            self_pos = pygame.math.Vector2(self.hitbox.center)
        direction = (target_pos-self_pos)
        is_close = direction.magnitude() < self.distance_to_follow or self.distance_to_follow == -1
        if (not is_close): return False
        if (self.is_though_wall): return True
        
        x, y = self.hitbox.width/2, self.hitbox.height/2
        if (coef == None): coef = self.coef_wall_hiding
        for sprite in self.obstacle_sprites:
            sprite_collision = False
            for offset in [(x,y), (-x,y), (x,-y), (-x,-y)]:
                offset = pygame.math.Vector2(offset)
                if (not sprite.rect.clipline(self_pos+offset, target_pos+offset*coef)): continue
                return False
            
        return True

    def find_2nd_target(self, target_pos):
        "smarter AI"
        self_pos = pygame.math.Vector2(self.hitbox.center)
        #speed up
        if ((self_pos-target_pos).magnitude()>self.distance_to_follow):
            return None
        x, y = self.hitbox.width, self.hitbox.height
        lstmp = [(x,0), (-x,0), (0,y), (0,-y)]
        ls = []
        if (self_pos.x+x/2>target_pos.x):
            ls.append((-x,0))
        if (self_pos.x-x/2<target_pos.x):
            ls.append((x,0))
        if (self_pos.y-y/2<target_pos.y):
            ls.append((0,y))
        if (self_pos.y+y/2>target_pos.y):
            ls.append((0,-y))
        # print(ls+lstmp)
        for offset in ls+lstmp:
            next_pos = self_pos + offset
            if (not self.target_sight_check(next_pos, coef=1)): continue
            if (not self.target_sight_check(target_pos, next_pos, 1)): continue
            # print(next_pos,offset)
            return next_pos
        return None     
            
    def get_random_target_point(self):
        self_pos = pygame.math.Vector2(self.hitbox.center)
        dpos = pygame.math.Vector2(
            random.randint(-self.wandering_distance,self.wandering_distance),
            random.randint(-self.wandering_distance,self.wandering_distance))
        return self_pos + dpos
    
    def check_collision(self):
        # if (is_though_wall==None): is_though_wall = self.is_though_wall
        if (self.is_though_wall): return False
        for sprite in self.obstacle_sprites:
            if (sprite.rect.colliderect(self.hitbox)):
                return True
        return False
    
    def cancel_trigger(self):
        "when zombie not chase sth it cancels trigger"
        if (self.currnet_standing_time>0): return #if standing then stfu
        if (random.uniform()<self.prob_standing):
            self.current_speed = 0
            self.currnet_standing_time = self.standing_time
            return
        self.target_point = self.get_random_target_point()
        self.current_speed = self.speed

    def move(self):
        target = self.player
        self_pos = pygame.math.Vector2(self.hitbox.center)
        
        #update standing time
        self.currnet_standing_time -= system.delta_time
        self.currnet_standing_time = max(self.currnet_standing_time, 0)
        if (self.currnet_standing_time<=0 and self.current_speed==0 
            and not self.is_attacking): self.current_speed = self.speed
        
        #update target point
        if ((self.target_point-self_pos).magnitude()<=self.attack_range_trigger
            and not self.on_trigger and not self.is_attacking):        
            self.cancel_trigger() #move to point then relize there's no one
        if (target!=None): 
            target_pos = pygame.math.Vector2(target.hitbox.center)
            next_pos = self.find_2nd_target(target_pos)
            if (self.target_sight_check(target_pos) and not self.is_attacking): #trigger
                self.target_point = target_pos
                self.current_speed = self.trigger_speed
                self.on_trigger = True
                # print('first ' , end=' ')
            elif next_pos != None and not self.is_attacking:
                self.target_point = next_pos
                self.current_speed = self.trigger_speed
                self.on_trigger = True
                # print('second ' , end=' ')
            else: self.on_trigger = False

        # print(self.target_point)
        #update direction  
        self.direction = (self.target_point-self_pos)
        if (self.direction.magnitude()!=0): self.direction = self.direction.normalize()
        
        self.hitbox.center += system.delta_time*self.current_speed*self.direction
        #collision, if zombie is on trigger, it can't be hit wall (logic)
        if (self.check_collision()): #wander hit wall
            self.hitbox.center -= system.delta_time*self.current_speed*self.direction
            self.cancel_trigger()
        
        self.rect.center = self.hitbox.center + self.shift

    def attack(self):
        target = self.player
        if (target==None): return

        self.attack_current_cooldown -= system.delta_time
        self.attack_current_cooldown = max(self.attack_current_cooldown, 0)

        #attack
        self_pos = pygame.math.Vector2(self.hitbox.center)
        target_pos = pygame.math.Vector2(target.hitbox.center)
        if ((self_pos-target_pos).magnitude()<=self.attack_range_trigger):
            self.is_attacking = True
            if (self.attack_current_cooldown==0):
                self.attack_anim_start = True
                self.attack_current_cooldown = self.attack_cooldown + random.uniform(-1,1)*self.attack_cooldown_std
                self.current_speed = 0
        elif self.attack_current_cooldown==0: self.is_attacking = False
        #deal damage
        if ((self_pos-target_pos).magnitude()<=self.attack_range and self.is_attacking):
            if (self.attack_current_cooldown<=self.attack_cooldown-self.attack_damage_after 
                and self.attack_current_cooldown>=self.attack_cooldown-self.attack_damage_after_limit
                and not self.dealing_damage_yet):
                
                self.dealing_damage_yet = True
                target.get_damage(self.damage)
    
    def dead_animation(self):
        turn_left = self.direction.x<0
        animation = self.animations['dying'][turn_left]
        if (self.frame_index>=len(animation)):
            self.image = animation[-1]
        else:
            self.image = animation[int(self.frame_index)]

    def update_animation(self):
        self.frame_index += self.animation_speed*system.delta_time
        if (self.is_dead):
            self.dead_animation()
            self.corpse_despawn_current_time += system.delta_time
            if (self.corpse_despawn_current_time>=self.corpse_despawn_time):
                self.kill()
                self.hitbox.size = (0,0)
            return
        
        turn_left = self.direction.x<0
        if (self.is_attacking and self.attack_anim_start):
            self.attack_anim_start = False
            self.anim_state = 'attacking'
            self.frame_index = 0
            self.dealing_damage_yet = False
        if self.anim_state != 'attacking':
            if (self.direction.magnitude()>1e-2 and self.current_speed>0): self.anim_state = 'walking'
            else: self.anim_state = 'idle'

        animation = self.animations[self.anim_state][turn_left]
        if (self.frame_index>= len(animation)):
            self.frame_index = 0
            if self.anim_state == 'attacking': self.anim_state = 'walking'

        current_image = animation[int(self.frame_index)]
        if (self.is_getting_damage):
            self.getting_damage_current_delay = self.getting_damage_delay
            self.is_getting_damage = False
        self.getting_damage_current_delay -= system.delta_time
        self.getting_damage_current_delay = max(self.getting_damage_current_delay,0)
        if (self.getting_damage_current_delay>0):
            color = (255,255,255,0)
            current_image = current_image.copy()
            current_image.fill(color,special_flags=pygame.BLEND_RGBA_MAX)

        self.image = current_image
    
    def get_damage(self, damage = 0):
        if (self.is_dead): return
        self.is_getting_damage = True
        self.current_health -= damage
        if (self.current_health<=0):
            self.die()

    def die(self):
        self.is_dead = True
        self.frame_index = 0 #die animation
    
    def update(self):
        self.move()
 
    def bleed(self, bullet_pos):
        system.level.create_blood(bullet_pos)
        self.bleeding_sounds.play()

    def load_assets(self):
        "import zombie assets"
        zombie_path = PATH + 'graphics/enemy/' + self.namedir + '/'
        self.path = zombie_path
        self.animations = {'idle':[], 'walking':[], 'attacking':[], 'dying': []}
        for animation in self.animations.keys():
            anim_path = zombie_path + animation + '/'
            anim = file.import_folder(anim_path)
            self.animations[animation].append(anim)
            self.animations[animation].append(
                [pygame.transform.flip(img, flip_x = True, flip_y = False) for img in anim])
    
    def import_scream_sounds(self):
        "all sounds too :D"
        self.scream_sounds = Playlist(self.path + 'scream_playlist/')
        self.bleeding_sounds = Playlist(self.path + 'bleeding_playlist/')

    def update_scream(self, ignore_distance = False):
        target = self.player
        if (target==None): return
        target_pos = pygame.math.Vector2(target.hitbox.center)
        self_pos = pygame.math.Vector2(self.hitbox.center)

        self.scream_current_cooldown -= system.delta_time
        if (self.scream_current_cooldown<=0):
            self.scream_current_cooldown = self.scream_cooldown + random.uniform(-1,1)*self.scream_cooldown_std
            if ((target_pos-self_pos).magnitude()<=self.distance_to_follow*1.5 
                or ignore_distance):
                self.scream_sounds.play()

class Zombie(BasedZombie):
    '''
    A class representing a zombie entity in the game.

    Attributes:
        max_health (int): The maximum health points of the zombie.
        current_health (int): The current health points of the zombie.
        corpse_despawn_time (int): The time it takes for the zombie corpse to despawn after death.
        damage (int): The amount of damage the zombie inflicts on the player.
        hitbox (pygame.Rect): The hitbox rectangle of the zombie for collision detection.
        coef_wall_hiding (float): The coefficient determining how the zombie hides near walls.
        zombie_size_scale (float): The scale factor for the size of the zombie.
        attack_range (float): The attack range of the zombie.
        attack_range_trigger (float): The trigger range for initiating an attack.
        speed_scale (float): The scale factor for the speed of the zombie.
        animation_speed (int): The speed of the zombie's animation.
        attack_anim_start (bool): Flag indicating if the attack animation has started.
        frame_index (int): The index of the current frame in the animation.
        anim_state (str): The current state of animation ('idle' or 'attack').
        rect (pygame.Rect): The rectangle representing the position and size of the zombie image.
        groups (pygame.sprite.Group): The group to which the zombie belongs.
        obstacle_sprites (pygame.sprite.Group): The group containing obstacle sprites.
        player (Player): The player object.
        zindex (int): The z-index of the zombie for layering in the game.

    Methods:
        update(self): Updates the state of the zombie including movement, animation, and attack.
    '''
    def __init__(self, pos, groups, obstacle_sprites, player = None, zindex = 1):
        super().__init__(pos, groups, obstacle_sprites, player=player, zindex = 1)
        self.namedir = 'zombie'
        self.load_assets()
        self.animation_speed = 10
        self.attack_anim_start = True
        self.frame_index = 0
        self.anim_state = 'idle'
        self.update_animation()
        self.rect = self.image.get_rect(topleft = pos)

        self.max_health = 100
        self.current_health = self.max_health
        self.corpse_despawn_time = 30
        self.damage = 10

        #customize
        self.hitbox = self.image.get_rect(topleft = pos)
        inflate_x = 30
        inflate_top = 21-9
        inflate_bottom = 0
        self.hitbox.width -= inflate_x
        self.hitbox.height -= inflate_top+inflate_bottom
        self.hitbox.centerx += inflate_x/2
        self.hitbox.bottom += inflate_top
        #when player near wall, zombie cant see
        self.coef_wall_hiding = 0.02
        # print(self.hitbox, self.rect)

        #scale random
        self.zombie_size_scale = random.uniform(0.8,1.5)
        self.attack_range = 150*self.zombie_size_scale #40
        self.attack_range_trigger = 60*self.zombie_size_scale #20
        self.hitbox.size = pygame.math.Vector2(self.hitbox.size)*self.zombie_size_scale
        self.rect.size = pygame.math.Vector2(self.rect.size)*self.zombie_size_scale
        self.speed_scale =  random.uniform(0.8,2.5)
        self.speed *= self.speed_scale
        self.trigger_speed *= self.speed_scale

        self.scream_cooldown = 5
        self.scream_cooldown_std = 1
        # self.scream_current_cooldown = self.scream_cooldown+random.uniform(-1,1)*self.scream_cooldown_std
        self.import_scream_sounds()

    def update(self):
        if (not self.is_dead): self.move()
        self.update_animation()
        if (not self.is_dead): self.attack()
        if (not self.is_dead): self.update_scream()


class Bat(BasedZombie):
    def __init__(self, pos, groups, obstacle_sprites, player = None, zindex = 1):
        super().__init__(pos, groups, obstacle_sprites, player=player, zindex = 1)
        self.namedir = 'bat'
        self.load_assets()
        self.animation_speed = 10
        self.attack_anim_start = True
        self.frame_index = 0
        self.anim_state = 'idle'
        self.update_animation()
        self.rect = self.image.get_rect(topleft = pos)

        self.max_health = 60
        self.current_health = self.max_health
        self.corpse_despawn_time = 30
        self.distance_to_follow = 900
        self.damage = 5

        #customize
        self.hitbox = self.image.get_rect(topleft = pos)
        self.hitbox.size = (17,9)
        #when player near wall, zombie cant see
        self.coef_wall_hiding = 0.02
        # print(self.hitbox, self.rect)

        self.shift_y = 10
        self.shift = pygame.math.Vector2(0,self.shift_y)


        #scale random
        self.zombie_size_scale = 3
        self.attack_range = 50*self.zombie_size_scale #40
        self.attack_range_trigger = 15*self.zombie_size_scale #20
        self.hitbox.size = pygame.math.Vector2(self.hitbox.size)*self.zombie_size_scale
        self.rect.size = pygame.math.Vector2(self.rect.size)*self.zombie_size_scale
        self.speed_scale =  random.uniform(2,2.5)
        self.speed *= self.speed_scale
        self.trigger_speed *= self.speed_scale

        self.scream_cooldown = 6
        self.scream_cooldown_std = 1
        # self.scream_current_cooldown = self.scream_cooldown+random.uniform(-1,1)*self.scream_cooldown_std

        self.import_scream_sounds()

    def update(self):
        if (not self.is_dead): self.move()
        self.update_animation()
        if (not self.is_dead): self.attack() 
        if (not self.is_dead): self.update_scream()

class FlyingSword(BasedZombie):
    """
    Represents a flying sword object in the game.

    Attributes:
        namedir (str): The directory name of the flying sword.
        animation_speed (int): The speed of flying sword animation.
        max_health (int): The maximum health of the flying sword.
        current_health (int): The current health of the flying sword.
        corpse_despawn_time (float): The time it takes for the flying sword's corpse to despawn.
        distance_to_follow (int): The distance at which the flying sword follows the player.
        damage (int): The damage dealt by the flying sword.
        is_though_wall (bool): Indicates if the flying sword can pass through walls.
        attack_damage_after (int): The time after which the attack deals damage.
        coef_wall_hiding (float): The coefficient for hiding behind walls when the player is nearby.
        hitbox (pygame.Rect): The hitbox rectangle of the flying sword.
    
    Methods:
        bleed(pos): Not implemented. Makes the flying sword bleed at a given position.
        attack(): Initiates the attack behavior of the flying sword.
        update(): Updates the state of the flying sword.
    """
    def __init__(self, pos, groups, obstacle_sprites, player = None, zindex = 1):
        super().__init__(pos, groups, obstacle_sprites, player=player, zindex = 1)
        self.namedir = 'flying_sword'
        self.load_assets()
        self.animation_speed = 16
        self.frame_index = 0
        self.anim_state = 'idle'
        self.update_animation()
        self.rect = self.image.get_rect(topleft = pos)

        self.max_health = 20
        self.current_health = self.max_health
        self.corpse_despawn_time = 0.1
        self.distance_to_follow = -1
        self.damage = 5
        self.is_though_wall = True
        self.attack_damage_after = -10

        #customize
        self.hitbox = self.image.get_rect(topleft = pos)
        self.hitbox.size = (27,27)
        #when player near wall, zombie cant see
        self.coef_wall_hiding = 0.02

        #scale random
        self.zombie_size_scale = 2
        self.attack_range = 15*self.zombie_size_scale #40
        self.attack_range_trigger = 15*self.zombie_size_scale #20
        self.hitbox.size = pygame.math.Vector2(self.hitbox.size)*self.zombie_size_scale
        self.rect.size = pygame.math.Vector2(self.rect.size)*self.zombie_size_scale
        self.speed_scale =  random.uniform(3,3.5)
        self.speed *= self.speed_scale
        self.trigger_speed *= self.speed_scale

        system.level.enemies.append(self)

        self.import_scream_sounds()
        self.scream_cooldown = 1
        self.scream_cooldown_std = 0
        self.scream_current_cooldown = 0

    def bleed(self, pos):
        self.bleeding_sounds.play()
        pass
    
    def attack(self):
        super().attack()
        if self.is_attacking:
            self.kill()
            system.level.enemies.remove(self)

    def update(self):
        if (not self.is_dead): self.move()
        self.update_animation()
        if (not self.is_dead): self.attack()
        if (not self.is_dead): self.update_scream(ignore_distance=True)

class Skeleton(BasedZombie):
    '''
    Represents a skeleton enemy in the game. 
    Skeleton can throw FlyingSword to player

    Attributes:
        namedir (str): The directory name of the skeleton.
        animation_speed (int): The speed of skeleton animation.
        max_health (int): The maximum health of the skeleton.
        current_health (int): The current health of the skeleton.
        corpse_despawn_time (int): The time it takes for the skeleton's corpse to despawn.
        distance_to_follow (int): The distance at which the skeleton follows the player.
        damage (int): The damage dealt by the skeleton.
        attack_cooldown (int): The cooldown time for the skeleton's attack.
        attack_damage_after (float): The time after which the attack deals damage.
        coef_wall_hiding (float): The coefficient for hiding behind walls when the player is nearby.
        shift_y (int): The y-shift value.
        zombie_size_scale (float): The scale of the zombie size.
        attack_range_trigger (int): The trigger range for the attack.
        speed_scale (float): The scale factor for speed.
        shift (pygame.math.Vector2): The shift vector.
        hitbox (pygame.Rect): The hitbox rectangle of the skeleton.
        rect (pygame.Rect): The rectangle representing the skeleton.
    Methods:
        attack(self): Handles the skeleton's attack behavior.update(self):
        update(self): Updates the skeleton's behavior (movement, animation, attack).
    '''
    def __init__(self, pos, groups, obstacle_sprites, player = None, zindex = 1):
        super().__init__(pos, groups, obstacle_sprites, player=player, zindex = 1)
        self.namedir = 'skeleton'
        self.load_assets()
        self.animation_speed = 10
        self.attack_anim_start = True
        self.frame_index = 0
        self.anim_state = 'idle'
        self.update_animation()
        self.rect = self.image.get_rect(topleft = pos)

        self.max_health = 100
        self.current_health = self.max_health
        self.corpse_despawn_time = 30
        self.distance_to_follow = 900
        self.damage = 5
        self.attack_cooldown = 3
        self.attack_damage_after = 0.3

        #customize
        self.hitbox = self.image.get_rect(topleft = pos)
        self.hitbox.size = (31,52)
        #when player near wall, zombie cant see
        self.coef_wall_hiding = 0.02
        # print(self.hitbox, self.rect)

        self.shift_y = 10
        self.shift = pygame.math.Vector2(0,self.shift_y)


        #scale random
        self.zombie_size_scale = random.uniform(2,2.5)
        self.attack_range_trigger = 500 
        self.hitbox.size = pygame.math.Vector2(self.hitbox.size)*self.zombie_size_scale
        self.rect.size = pygame.math.Vector2(self.rect.size)*self.zombie_size_scale
        self.speed_scale =  random.uniform(2,2.5)
        self.speed *= self.speed_scale
        self.trigger_speed *= self.speed_scale

        self.import_scream_sounds()

    def attack(self):
        target = self.player #
        if (target==None): return

        self.attack_current_cooldown -= system.delta_time
        self.attack_current_cooldown = max(self.attack_current_cooldown, 0)

        #attack
        self_pos = pygame.math.Vector2(self.hitbox.center)
        target_pos = pygame.math.Vector2(target.hitbox.center)
        if ((self_pos-target_pos).magnitude()<=self.attack_range_trigger):
            self.is_attacking = True
            if (self.attack_current_cooldown==0):
                self.attack_anim_start = True
                self.attack_current_cooldown = self.attack_cooldown + random.uniform(-1,1)*self.attack_cooldown_std
                self.current_speed = 0
        elif self.attack_current_cooldown==0: self.is_attacking = False
        #deal damage
        if (self.is_attacking):
            if (self.attack_current_cooldown<=self.attack_cooldown-self.attack_damage_after 
                and self.attack_current_cooldown>=self.attack_cooldown-self.attack_damage_after_limit
                and not self.dealing_damage_yet):
                self.dealing_damage_yet = True
                FlyingSword(self.hitbox.center,self.groups(),self.obstacle_sprites,self.player, zindex=2)

    def update(self):
        if (not self.is_dead): self.move()
        self.update_animation()
        if (not self.is_dead): self.attack() 
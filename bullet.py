import pygame
from settings import *
from math import atan2, pi, exp2
import system
from random import uniform
import file
from particle import Particle

class BulletLine(pygame.sprite.Sprite):
    """
    Represents a line showing the trajectory of a bullet.

    Attributes:
        fade_time: The time it takes for the line to fade away.
        default_alpha: The default alpha value of the line.
        min_alpha: The minimum alpha value of the line.
        current_alpha: The current alpha value of the line.
        bullet: The bullet associated with the line.
        zindex: The z-index of the line.
        original_image: The original image of the line.
        image: The image of the line.
        rect: The rectangle representing the line.
        barrel_pos: The position of the bullet's barrel.
        time_self_destroy: The time until the line self-destructs.

    Methods:
        update(): Updates the trajectory line.
    """
    def __init__(self, groups, bullet, zindex = 0):
        super().__init__(groups)
        
        self.fade_time = 2
        self.default_alpha = 100
        self.min_alpha = 40
        self.current_alpha = self.default_alpha
        self.bullet = bullet
        self.zindex = 1
        self.original_image = pygame.Surface((1,8), pygame.SRCALPHA)
        self.original_image.fill(self.bullet.weapon.bullet_line_color)
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.barrel_pos = pygame.math.Vector2(bullet.rect.center) #bullet init state
        self.time_self_destroy = 1.2

    def update(self):
        #rotate and scale
        length_line = (self.bullet.rect.center-self.barrel_pos).magnitude()
        self.image = pygame.transform.scale(self.original_image,(length_line,self.original_image.get_size()[1]))
        self.image = pygame.transform.rotate(self.image,-self.bullet.angle)
        
        #calc alpha
        self.current_alpha -= system.delta_time/self.fade_time*(self.default_alpha-self.min_alpha)
        if (self.current_alpha<self.min_alpha): self.current_alpha = self.min_alpha
        self.image.set_alpha(self.current_alpha)
        
        #update position
        self.rect = self.image.get_rect()
        self.rect.center = (self.barrel_pos+self.bullet.rect.center)/2

        self.time_self_destroy -= system.delta_time
        if (self.time_self_destroy<=0):
            self.kill()

class BaseBullet(pygame.sprite.Sprite):
    """
    Represents the base class for all types of bullets.

    Attributes:
        time_self_destroy: The time until the bullet self-destructs.
        current_time_self_destroy: The current time until self-destruction.
        speed: The speed of the bullet.
        zindex: The z-index of the bullet.
        weapon: The weapon associated with the bullet.
        obstacles: The obstacles present in the game.
        direction: The direction of the bullet.
        path: The path to the bullet's image.
        original_image: The original image of the bullet.
        image: The image of the bullet.
        rect: The rectangle representing the bullet.
        hitbox: The hitbox of the bullet.
        start_pos: The starting position of the bullet.
        dealing_damage_cooldown: The cooldown time for dealing damage.
        dealing_damage_current_cooldown: The current cooldown time for dealing damage.

    Methods:
        move(): Moves the bullet.
        check_collision(): Checks for collisions with obstacles and enemies.
        update(): Updates the bullet's state.
    """
    def __init__(self, groups, weapon, obstacles, zindex = 0):
        super().__init__(groups)

        self.time_self_destroy = weapon.bullet_lifetime
        self.current_time_self_destroy = self.time_self_destroy
        self.speed = weapon.bullet_velocity

        self.zindex = zindex
        self.weapon = weapon
        self.obstacles = obstacles
        self.direction = pygame.math.Vector2(1,0).rotate(weapon.target)
        self.path = weapon.path + 'bullet/'
        sprite_path = self.path + '0.png'
        self.original_image = pygame.image.load(sprite_path).convert_alpha()
        self.image = self.original_image 
        dbarrel = weapon.center_to_barrel_rotated
        barrel_pos = weapon.rect.center + dbarrel
        self.rect = self.original_image.get_rect(center=barrel_pos)
        self.hitbox = self.rect.copy()
        self.hitbox.size = (10,10)
        self.start_pos = barrel_pos
        #in degree
        angle = weapon.angle
        if (weapon.stability>weapon.min_stability):
            angle += uniform(-1,1)*min(weapon.stability-weapon.min_stability,weapon.max_stability)
        # print(self.direction,self.rect)
        self.angle = angle

        self.dealing_damage_cooldown = 0.5
        self.dealing_damage_current_cooldown = 0

    @property
    def angle(self): #in degree, world coor
        vec = self.rect.center - self.start_pos
        return atan2(vec.y,vec.x)/pi*180
    @angle.setter
    def angle(self, angle): #in degree, world coor
        self.direction = pygame.math.Vector2(1,0).rotate(angle)
        self.image = pygame.transform.rotate(self.original_image,-angle) #is on screen
        self.rotated_image = self.image
        self.rect = self.image.get_rect(center = self.rect.center)

    def move(self):
        self.rect.center += self.direction*system.delta_time*self.speed
        self.hitbox.center = self.rect.center

    def check_collision(self):
        for sprite in self.obstacles:
            if not self.hitbox.colliderect(sprite.rect): continue
            self.kill()
        
        self.dealing_damage_current_cooldown -= system.delta_time
        self.dealing_damage_current_cooldown = max(self.dealing_damage_current_cooldown,0)
        for target in system.level.enemies:
            if (not self.hitbox.colliderect(target.hitbox)): continue
            if (self.dealing_damage_current_cooldown > 0): continue
            if (target.is_dead): continue
            target.get_damage(self.weapon.damage)
            self.dealing_damage_current_cooldown = self.dealing_damage_cooldown

    def update(self):
        self.move()        
        self.check_collision()
        self.current_time_self_destroy -= system.delta_time
        if (self.current_time_self_destroy<=0):
            self.kill()

class Bullet(BaseBullet):
    """
    Represents a bullet projectile.

    Methods:
        check_collision(): Checks for collisions with enemies.
    """
    def __init__(self, groups, weapon, obstacles, zindex = 0):
        super().__init__(groups, weapon, obstacles, zindex)
        self.bullet_line = BulletLine(groups, self)
        self.hitbox = pygame.rect.Rect((0,0),(14,8))
        self.hitbox.center = self.rect.center

    def check_collision(self):
        for target in system.level.enemies:
            if (not self.hitbox.colliderect(target.hitbox)): continue
            if (self.dealing_damage_current_cooldown > 0): continue
            if (target.is_dead): continue
            target.bleed(self.rect.center)
            self.kill()
        super().check_collision()

class FlameBullet(BaseBullet):
    """
    Represents a flame projectile.

    Attributes:
        flame_pos_std: The standard deviation of flame position.

    Methods:
        update_flame_size(): Updates the size of the flame.
    """
    def __init__(self, groups, weapon, obstacles, zindex = 0):
        weapon.stability = weapon.max_stability
        super().__init__(groups, weapon, obstacles, zindex)
        #slow down or speed up depend on player move
        coef = weapon.player.direction.dot(self.direction)*2
        self.speed += weapon.player.current_speed*coef
        self.dealing_damage_cooldown = 0.1
        self.flame_pos_std = 20
        
        #self.angle = self.angle IS SO WEIRDDDDDDDDD
        self.update_flame_size()
        self.flamesmoke = FlameSmoke(groups, self, obstacles, zindex)

        self.hitbox = pygame.rect.Rect(self.rect)

    def update_flame_size(self):
        #update color (aka more black)
        current_image = self.rotated_image.copy()
        colored_image = pygame.Surface(current_image.get_size(),pygame.SRCALPHA)
        color_add = max(self.current_time_self_destroy/self.time_self_destroy,0)*120
        colored_image.fill((color_add,color_add,color_add,0))
        current_image.blit(colored_image, (0,0), special_flags = pygame.BLEND_RGBA_ADD)
        #now update size (diff with smoke)
        len_side = self.weapon.bullet_start_size+(self.weapon.bullet_end_size-self.weapon.bullet_start_size)*(1-self.current_time_self_destroy/self.time_self_destroy)
        self.image = pygame.transform.scale(current_image,(len_side,len_side))
        self.rect = self.image.get_rect(center = self.rect.center)

    def move(self):
        self.speed *= exp2(-system.delta_time/self.weapon.bullet_velocity_decay_halflife)
        super().move()

    def check_collision(self):
        for target in system.level.enemies:
            if (not self.hitbox.colliderect(target.hitbox)): continue
            if (self.dealing_damage_current_cooldown > 0): continue
            pos = pygame.math.Vector2(self.rect.center)
            pos += pygame.math.Vector2(uniform(-self.flame_pos_std,self.flame_pos_std),uniform(-self.flame_pos_std,self.flame_pos_std))
            system.level.create_flame_particle(pos)
            #if target.is_dead take cooldown
            self.dealing_damage_current_cooldown = self.dealing_damage_cooldown
        super().check_collision()

    def update(self):
        super().update()
        self.update_flame_size()

class FlameSmoke(pygame.sprite.Sprite):
    """
    Represents the smoke produced by a flame projectile.

    Attributes:
        bullet: The flame bullet associated with the smoke.

    Methods:
        update_flamesmoke(): Updates the size and alpha of the smoke.
    """

    def __init__(self, groups, bullet, obstacles, zindex = 0):
        super().__init__(groups)
        self.zindex = zindex-0.25
        self.bullet = bullet
        self.obstacles = obstacles
        self.time_self_destroy = bullet.weapon.flamesmoke_lifetime
        self.current_time_self_destroy = self.time_self_destroy
        self.path = self.bullet.weapon.path + 'flamesmoke/'
        sprite_path = self.path + '0.png'
        self.orginal_image = pygame.image.load(sprite_path).convert_alpha()
        self.image = self.orginal_image
        self.image.set_alpha(bullet.weapon.flamesmoke_start_alpha)
        self.rect = self.image.get_rect(center=bullet.rect.center)
        coef = bullet.weapon.player.direction.dot(bullet.direction)*2
        self.speed = bullet.weapon.flamesmoke_velocity
        self.speed += bullet.weapon.player.current_speed*coef
        # self.angle = self.bullet.angle #VAN SUS LA SAOOOOO
        # self.direction = pygame.math.Vector2(1,0).rotate(self.angle)

    def update_flamesmoke(self):
        #update size
        len_side = self.bullet.weapon.flamesmoke_start_size+(self.bullet.weapon.flamesmoke_end_size-self.bullet.weapon.flamesmoke_start_size)*(1-self.current_time_self_destroy/self.time_self_destroy)
        self.image = pygame.transform.scale(self.orginal_image,(len_side,len_side))
        self.rect = self.image.get_rect(center = self.rect.center)
        
        #update color (aka alpha)
        weapon = self.bullet.weapon
        current_alpha = max((weapon.flamesmoke_end_alpha-weapon.flamesmoke_start_alpha)*self.current_time_self_destroy/self.time_self_destroy+weapon.flamesmoke_start_alpha,0)
        self.image.set_alpha(current_alpha)

    def move(self):
        #update speed
        self.speed *= exp2(-system.delta_time/self.bullet.weapon.flamesmoke_velocity_decay_halflife)
        self.rect.center += self.bullet.direction*self.speed*system.delta_time
    
    def check_collision(self):
        for sprite in self.obstacles:
            if not self.rect.colliderect(sprite.rect): continue
            self.kill()

    def update(self):
        self.move()
        self.update_flamesmoke()
        self.check_collision()
        self.current_time_self_destroy -= system.delta_time
        if (self.current_time_self_destroy<=0):
            self.kill()

class Missile(BaseBullet):
    """
    Represents a missile projectile.

    Methods:
        explode(): Triggers an explosion when the missile hits.
    """
    def __init__(self, groups, weapon, obstacles, zindex = 0):
        super().__init__(groups, weapon, obstacles, zindex)
        self.hitbox = pygame.rect.Rect((0,0),(32,32))
        self.hitbox.center = self.rect.center

    def explode(self):
        Explode(self.groups(), self.hitbox.center, 
            self.weapon.path + 'explode/', self.weapon.damage, zindex = self.zindex)
        system.camera.screen_shake(12)
        self.weapon.explode_sound.play()

    def kill(self):
        self.explode()
        super().kill()

    def check_collision(self):
        for sprite in self.obstacles:
            if not self.hitbox.colliderect(sprite.rect): continue
            self.kill()

        for target in system.level.enemies:
            if (not self.hitbox.colliderect(target.hitbox)): continue
            if (target.is_dead): return
            self.kill()

class Explode(Particle):
    """
    Represents an explosion particle.

    Attributes:
        path: The path to the explosion animation.
        damage: The damage caused by the explosion.

    Methods:
        explode(): Deals damage to enemies within the explosion area.
    """
    def __init__(self, groups, pos, path, damage, zindex = 0):
        self.path = path
        self.damage = damage
        # self.animation = file.import_folder(path)
        # self.image = self.animation[0]
        # self.rect = self.image.get_rect(center = pos)
        super().__init__(groups, pos, scale = 6)
        self.animation_speed = 20
        self.hitbox = pygame.rect.Rect((0,0), 
                pygame.math.Vector2(self.rect.size)/3*2)
        self.hitbox.center = self.rect.center
        self.explode()

    def explode(self):
        enemies = system.level.enemies
        for target in enemies:
            if (not self.hitbox.colliderect(target.hitbox)): continue
            target.get_damage(self.damage)

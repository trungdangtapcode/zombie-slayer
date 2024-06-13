import pygame
from settings import *
import system
from math import acos, pi, atan2, exp2
import json
from sound import Playlist

dirname_to_weapon_shift = [
    pygame.math.Vector2(0,-25),
    pygame.math.Vector2(8,3),
    pygame.math.Vector2(0,5),
    pygame.math.Vector2(-8,-13)
]
weapon_handpos_shilf = pygame.math.Vector2(0,12)

class Weapon(pygame.sprite.Sprite):
    """
    Represents a weapon that a player can use in the game.

    Attributes:
        shooting_cooldown (float): Cooldown time between shots.
        current_shooting_cooldown (float): Current cooldown time.
        zindex (int): Z-index for rendering order.
        player (Player): The player who owns the weapon.
        name (str): Name of the weapon.
        type (str): Type of the weapon.
        path (str): Path to the weapon's graphics directory.
        original_image (Surface): Original image of the weapon.
        image (Surface): Current image of the weapon.
        rect (Rect): Rectangular area representing the weapon's position and size.
        cc (float): Control variable for animation.
        target (float): Target angle for weapon rotation.
        flip (bool): Flag for flipping the weapon image.
        angle (float): Current angle of the weapon.
        current_player_center (Vector2): Current center position of the player.
        force_to_player (int): Force applied to the weapon towards the player.
        decay_fiction_halflife (float): Half-life of the decay friction.
        velocity (Vector2): Current velocity of the weapon.
        recoil (int): Recoil force of the weapon.
        stability (int): Stability of the weapon.
        stability_recover (float): Rate of stability recovery.
        min_stability (int): Minimum stability value.
        max_stability (int): Maximum stability value.
        stability_shot (float): Stability reduction per shot.
        stability_shot_sprint_bonus (float): Bonus stability reduction when sprinting.
        is_disable (bool): Flag indicating if the weapon is disabled.
        clip_ammo (int): Current ammo in the clip.
        clip_max_ammo (int): Maximum ammo capacity of the clip.
        total_ammo (int): Total ammo available.
        is_reloading (bool): Flag indicating if the weapon is currently reloading.
        reloading_time (float): Time taken for reloading.
        reloading_current_time (float): Current time during reloading.

    Methods:
        read_info(path): Reads weapon information from a JSON file.
        weapon_rotate(angle): Rotates the weapon image by a given angle.
        update_transform(): Updates the position and rotation of the weapon.
        reload(): Reloads the weapon.
        update_reloading(): Updates the reloading process.
        update(): Updates the weapon's state.
        change_owner(): Changes the owner of the weapon.
    """
    def __init__(self,player,groups, name, type, zindex = 0):
        super().__init__(groups)

        self.shooting_cooldown = 0.1
        self.current_shooting_cooldown = 0

        self.zindex = zindex
        self.player = player

        self.name = name
        self.type = type
        self.path = PATH + 'graphics/weapon/'+ self.name + '/'
        sprite_path = self.path+ 'sprite/0.png' 
        self.original_image = pygame.image.load(sprite_path).convert_alpha()
        self.image = self.original_image
        
        self.rect = self.image.get_rect()
        self.cc = 0
        self.target = 0
        self.flip = False
        self.angle = 0
        self.current_player_center = pygame.math.Vector2(self.player.rect.center) #move to player center
        self.force_to_player = 2
        self.decay_fiction_halflife = 0.2
        self.velocity = pygame.math.Vector2(0,0)
        self.recoil = 5
        self.stability = 0
        self.stability_recover = 3.5
        self.min_stability = 10
        self.max_stability = 25
        self.max_stability -= self.min_stability
        self.stability_shot = 0.5
        self.stability_shot_sprint_bonus = 1

        self.is_disable = True

        self.clip_ammo = 100
        self.clip_max_ammo = 100
        self.total_ammo = 100
        self.is_reloading = False
        self.reloading_time = 1
        self.reloading_current_time = 0

        info_path = self.path+'info.json'
        self.read_info(info_path)

        self.shoot_sounds = Playlist(self.path+'shoot_playlist/')
        self.reloading_sound = pygame.mixer.Sound(self.path+'reloading.wav')
    
    def read_info(self,path):
        f = open(path, "r")
        data = json.load(f)

        #rotate_point
        self.handpoint = pygame.math.Vector2(data["handpoint"])
        self.barrel = pygame.math.Vector2(data["barrel"])
        self.center_to_barrel = self.barrel-(pygame.math.Vector2(self.original_image.get_size())-pygame.math.Vector2(1,1))/2
        self.center_to_barrel_rotated = self.center_to_barrel
        self.distance_to_ray = -self.barrel.y+self.handpoint.y #handpoint to ray
        self.center_to_handpoint = self.handpoint-(pygame.math.Vector2(self.original_image.get_size())-pygame.math.Vector2(1,1))/2
        self.center_to_handpoint_rotated = self.center_to_handpoint
        
        self.recoil = data["recoil"]
        self.type = data["type"]
        self.shooting_cooldown = data["shooting_cooldown"]
        self.bullet_velocity = data["bullet_velocity"]
        self.bullet_lifetime = data["bullet_lifetime"]
        self.damage = data["damage"]

        self.clip_max_ammo = data["clip_max_ammo"]
        self.clip_ammo = self.clip_max_ammo
        self.total_ammo = data["total_ammo"]
        self.reloading_time = data["reloading_time"]

        return data
    
    def weapon_rotate(self, angle):
        self.image = pygame.transform.rotate(self.original_image,angle)
        self.rect = self.image.get_rect()
        #bug :D => vector rotation is in coor w not on screen
        #note: angle is on screen
        self.center_to_handpoint_rotated = self.center_to_handpoint.rotate(-angle)
        self.center_to_barrel_rotated = self.center_to_barrel.rotate(-angle)

    def update_transform(self):
        #update velocity
        vec = self.player.rect.center-self.current_player_center
        self.velocity += vec*system.delta_time*self.force_to_player
        self.velocity *= exp2(-system.delta_time/self.decay_fiction_halflife)
        self.current_player_center += self.velocity

        # if ((self.current_player_center-self.player.rect.center).magnitude()<=10):
        #     self.current_player_center = pygame.math.Vector2(self.player.rect.center)
        # placement
        # player_hand: O, distance_to_ray: r, tangent: A, mouse M, tarrget = t
        # alpha = MOx, beta = MOA, gamma = tOA = RAO = 90-beta, ans = gamma-alpha
        posM = system.camera.mouse_wolrd_position()
        posO = self.current_player_center + dirname_to_weapon_shift[self.player.dirname]+ self.center_to_handpoint
        if (posM.x<posO.x):
            posM.x = posO.x*2-posM.x
            self.flip = True
        else: self.flip = False
        vecOM = (posM-posO)
        if (self.distance_to_ray<=vecOM.magnitude()): #else get the old target
            alpha = -atan2(vecOM.y,vecOM.x)/pi*180
            beta = acos(self.distance_to_ray/vecOM.magnitude())/pi*180
            gamma = 90-beta
            self.target = gamma-alpha
            self.angle = self.target if not self.flip else 180-self.target
        self.weapon_rotate(-self.target) #because angle is on screen
        #rotate(handpoint-center) = rotate(handpoint)-center = handpoint'-center
        #map: handpoint,center => handpoint', center
        #want handpoint = handpoint' => moving RHS with (handpoint-handpoint')
        #map':  handpoint,center => handpoint, center+handpoint-handpoint'
        self.rect.center = (self.current_player_center 
                        + dirname_to_weapon_shift[self.player.dirname] 
                        + self.center_to_handpoint 
                        - self.center_to_handpoint_rotated)
        if self.flip:
            self.rect.left = posO.x*2-self.rect.right
            self.image = pygame.transform.flip(self.image, True, False)
            self.center_to_barrel_rotated.x *= -1
            self.center_to_handpoint_rotated.x *= -1

        if (self.player.dirname==0 or self.player.dirname==3):
            self.zindex = 0.5
        else: self.zindex = 1.5

    def reload(self):
        if (self.total_ammo==0): return
        if (self.is_reloading): return
        self.total_ammo += self.clip_ammo
        self.clip_ammo = 0
        self.is_reloading = True
        self.reloading_current_time = self.reloading_time
        self.reloading_sound.play()
    
    def update_reloading(self):
        # print(self.clip_ammo, self.total_ammo,sep='/')
        if (not self.is_reloading): return
        self.reloading_current_time -= system.delta_time
        self.reloading_current_time = max(self.reloading_current_time,0)
        if (self.reloading_current_time==0):
            ammo_to_clip = min(self.total_ammo, self.clip_max_ammo)
            self.total_ammo -= ammo_to_clip
            self.clip_ammo += ammo_to_clip
            self.is_reloading = False

    def update(self):
        if (self.is_disable): return
        self.cc += 0.1
        self.stability -= system.delta_time*self.stability_recover
        if (self.stability<0): self.stability = 0
        self.current_shooting_cooldown -= system.delta_time
        if (self.current_shooting_cooldown<0): self.current_shooting_cooldown = 0
        # self.weapon_rotate(45)
        self.update_transform()
        self.update_reloading()

    def change_owner(self):
        pass

class Gun(Weapon):
    """
    Represents a gun weapon type, a subclass of Weapon.

    Methods:
        shoot(): Fires a bullet from the gun.
        read_info(path): Reads additional information specific to the gun from a JSON file.
        update(): Updates the state of the gun.
    """
    def __init__(self,player,groups, name, zindex = 0):
        super().__init__(player,groups, name, 'gun', zindex)

    def shoot(self):
        if (self.current_shooting_cooldown>0): return
        if (self.is_reloading): return
        if (self.clip_ammo<=0): return
        self.clip_ammo -= 1
        system.level.create_bullet(self,'bullet')
        angle = self.target if not self.flip else 180-self.target
        self.velocity -= pygame.math.Vector2(1,0).rotate(angle)*self.recoil
        self.current_shooting_cooldown = self.shooting_cooldown
        self.stability += self.stability_shot
        if (self.player.is_sprinting): self.stability += self.stability_shot_sprint_bonus
        if (self.stability>self.max_stability): self.stability = self.max_stability
        
        self.shoot_sounds.play()

    def read_info(self, path):
        data = super().read_info(path)
        self.bullet_line_color = tuple(data["bullet_line_color"])

    def update(self):
        super().update()

class FlameThrower(Weapon):
    """
    Represents a flamethrower weapon type, a subclass of Weapon.

    Attributes:
        max_stability: The maximum stability of the flamethrower.

    Methods:
        read_info(path): Reads additional information specific to the flamethrower from a JSON file.
        shoot(): Fires flames from the flamethrower.
    """
    def __init__(self,player,groups, name, zindex = 0):
        super().__init__(player,groups, name, 'flamethrower', zindex)
        self.max_stability = 21

    def read_info(self, path):
        data = super().read_info(path)
        self.bullet_velocity_decay_halflife = data["bullet_velocity_decay_halflife"]
        self.bullet_start_size = data["bullet_start_size"]
        self.bullet_end_size = data["bullet_end_size"]
        self.bullet_heat = data["bullet_heat"]
        self.flamesmoke_velocity = data["flamesmoke_velocity"]
        self.flamesmoke_velocity_decay_halflife = data["flamesmoke_velocity_decay_halflife"]
        self.flamesmoke_start_size = data["flamesmoke_start_size"]
        self.flamesmoke_end_size = data["flamesmoke_end_size"]
        self.flamesmoke_lifetime = data["flamesmoke_lifetime"]
        self.flamesmoke_start_alpha = data["flamesmoke_start_alpha"]
        self.flamesmoke_end_alpha = data["flamesmoke_end_alpha"]

    def shoot(self):
        if (self.current_shooting_cooldown>0): return
        if (self.is_reloading): return
        if (self.clip_ammo<=0): return
        self.clip_ammo -= 1
        system.level.create_bullet(self,'flamebullet')
        angle = self.target if not self.flip else 180-self.target
        self.velocity -= pygame.math.Vector2(1,0).rotate(angle)*self.recoil
        self.current_shooting_cooldown = self.shooting_cooldown

        self.shoot_sounds.play()

class MissileLaucher(Weapon):
    """
    Represents a missile launcher weapon type, a subclass of Weapon.

    Methods:
        shoot(): Fires a missile from the missile launcher.
        read_info(path): Reads additional information specific to the missile launcher from a JSON file.
        update(): Updates the state of the missile launcher.
    """
    def __init__(self,player,groups, name, zindex = 0):
        super().__init__(player,groups, name, 'missile_laucher', zindex)
        self.explode_sound = pygame.mixer.Sound(self.path+'explode.wav')

    def shoot(self):
        if (self.current_shooting_cooldown>0): return
        if (self.is_reloading): return
        if (self.clip_ammo<=0): return
        self.clip_ammo -= 1
        system.level.create_bullet(self,'missile')
        angle = self.target if not self.flip else 180-self.target
        self.velocity -= pygame.math.Vector2(1,0).rotate(angle)*self.recoil
        self.current_shooting_cooldown = self.shooting_cooldown
        self.stability += self.stability_shot
        if (self.player.is_sprinting): self.stability += self.stability_shot_sprint_bonus
        if (self.stability>self.max_stability): self.stability = self.max_stability

        self.shoot_sounds.play()

    def read_info(self, path):
        data = super().read_info(path)

    def update(self):
        super().update()
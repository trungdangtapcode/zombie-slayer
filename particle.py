import pygame
from settings import *
import file
import system

class Particle(pygame.sprite.Sprite):
    """
    Represents a particle effect in the game, capable of animating and scaling.
    
    Attributes:
        animation_speed (float): Speed at which the animation progresses.
        frame_index (float): Current frame index of the animation.
        image (Surface): Current image of the particle.
        rect (Rect): Rectangular area representing the particle's position and size.
        zindex (int): Rendering priority of the particle.
        animation (list): List of animation frames.
        path (str): Path to the animation frames.
    Methods:
        load_asset(): Loads the animation frames for the particle.
        update_animation(): Updates the animation by progressing through frames and kills the sprite when the animation ends.
        update(): Calls update_animation() to update the particle's state.
    """
    def __init__(self, groups, pos, zindex = 2, scale = 1):
        "pos_center"
        super().__init__(groups)
        self.load_asset()
        self.animation_speed = 10
        self.frame_index = 0
        self.image = self.animation[0]
        self.rect = self.image.get_rect(center = pos)
        if scale!=1:
            self.rect.size = pygame.math.Vector2(self.rect.size)*scale
            self.rect.center = pos
        self.zindex = zindex

    def load_asset(self):
        path = self.path
        self.animation = file.import_folder(path)

    def update_animation(self):
        self.frame_index += system.delta_time*self.animation_speed
        if (self.frame_index>=len(self.animation)):
            self.kill()
            return
        
        self.image = self.animation[int(self.frame_index)]

    def update(self):
        self.update_animation()
    

class Blood(Particle):
    """
    Represents a blood particle effect in the game.
    """
    def __init__(self, groups, pos, zindex=2):
        self.path = PATH + 'graphics/particle/blood/'
        super().__init__(groups, pos, zindex)

class FlamePariticle(Particle):
    """
    Represents a flame particle effect in the game.
    """
    def __init__(self, groups, pos, zindex=2):
        self.path = PATH + 'graphics/particle/flame/'
        super().__init__(groups, pos, zindex)
        
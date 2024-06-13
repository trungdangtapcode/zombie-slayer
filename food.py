import pygame
from settings import *
import system
import file
import json

class Food(pygame.sprite.Sprite):
    """Represents a food item in the game.

    Attributes:
        player (Player): The player instance associated with the food.
        name (str): The name of the food item.
        path (str): The path to the directory containing the food's graphics.
        eating_current_time (int): The remaining time for the current eating action.
        is_eating (bool): Indicates if the food is currently being eaten.
        image (pygame.surface.Surface): The image of the food item.
        rect (pygame.Rect): The rectangle bounding the food item's image.
        zindex (int): The z-index of the food item.
        is_disable (bool): Indicates if the food item is disabled.
        is_update (bool): Indicates if the food item needs to be updated.

    Methods:
        __init__(groups, name, player): Initialize a Food instance.
        read_info(): Reads information about the food item from its JSON file.
        eat(): Simulates the action of the player eating the food item.
        update_eating(): Updates the state of the food item during eating.
        update(): Updates the state of the food item.
    """
    def __init__(self, groups, name, player):
        super().__init__(groups)
        self.player = player
        self.name = name
        self.path = PATH + 'graphics/food/' + name + '/'
        self.read_info()
        self.eating_current_time = 0
        self.is_eating = False

        self.image = pygame.surface.Surface((1,1))
        self.rect = self.image.get_rect()
        self.zindex = -1
        self.is_disable = True
        self.is_update = False
        
        self.eating_sound = pygame.mixer.Sound(PATH + 'graphics/food/eating.wav')
        self.healing_sound = pygame.mixer.Sound(PATH + 'graphics/food/healing.wav')

    def read_info(self):
        f = open(self.path+'info.json', "r")
        data = json.load(f)
        self.hp_recover = data["hp_recover"]
        self.eating_time = data["eating_time"]
        self.quantity = data["quantity"]

    def eat(self):
        if (self.quantity<=0): return
        if (self.is_eating): return
        self.is_eating = True
        self.eating_current_time = self.eating_time
        self.quantity -= 1
        self.eating_sound.play()

    def update_eating(self):
        if (not self.is_eating): return
        self.eating_current_time -= system.delta_time
        self.eating_current_time = max(self.eating_current_time, 0)
        if (self.eating_current_time==0):
            self.is_eating = False
            self.player.get_heal(self.hp_recover)
            self.healing_sound.play()

    def update(self):
        if (not self.is_update): return
        self.update_eating()
        if (self.quantity<=0 and self.eating_current_time==0):
            self.kill()
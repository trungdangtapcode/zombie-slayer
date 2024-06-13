import pygame
from settings import *
import system
import file
import json
import random

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(64)

class Playlist:
    def __init__(self, path):
        self.path = path
        self.sounds = file.import_playlist(path)
    
    def play(self):
        random.choice(self.sounds).play()
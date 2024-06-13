import pygame 
from settings import *

class Tile(pygame.sprite.Sprite):
	def __init__(self,pos,groups,image,zindex = 0):
		super().__init__(groups)
		self.image = image
		self.rect = self.image.get_rect(topleft = pos)
		self.zindex = zindex
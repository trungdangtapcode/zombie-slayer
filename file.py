from csv import reader
from os import walk
import pygame
import json

def import_csv_layout(path):
    terrain_map = []
    with open(path) as level_map:
        layout = reader(level_map,delimiter = ',')
        for row in layout:
            terrain_map.append(list(row))
        return terrain_map

def import_folder(path):
    surface_list = []

    for _,__,img_files in walk(path):
        for image in sorted(img_files, key = lambda name: int(name.split('.')[0])): 
            full_path = path + '/' + image
            image_surf = pygame.image.load(full_path).convert_alpha()
            surface_list.append(image_surf)

    return surface_list

def import_playlist(path):
    surface_list = []

    for _,__,img_files in walk(path):
        for image in sorted(img_files, key = lambda name: int(name.split('.')[0])): 
            full_path = path + '/' + image
            sound = pygame.mixer.Sound(full_path)
            surface_list.append(sound)

    return surface_list

def import_json(path):
    f = open(path)
    data = json.load(f)
    return data


class SpriteSheet():
    def __init__(self, path, sprite_w, sprite_h):
        self.sheet = pygame.image.load(path).convert_alpha()
        self.sprite_w = sprite_w
        self.sprite_h = sprite_h
        self.w, self.h = self.sheet.get_rect().size
        self.w = self.w // self.sprite_w
        self.h = self.h // self.sprite_h

    def get_image(self, frame):
        assert frame < self.w*self.h, 'frame is out of the sheet'
        #transparent surface not .convert_alpha()
        image = pygame.Surface((self.sprite_w, self.sprite_h),pygame.SRCALPHA)
        offset_w = frame%self.w*self.sprite_w
        offset_h = frame//self.w*self.sprite_h
        image.blit(self.sheet, (0,0), (offset_w, offset_h, self.sprite_w, self.sprite_h))

        return image
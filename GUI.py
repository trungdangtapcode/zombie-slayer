import pygame

pygame.font.init()

class Text():
    def __init__(self, screen = None, text = '', size = 24, color = (0,0,0), pos = (0, 0), fontname = 'oop/font/slkscr.ttf'):
        self.screen = screen # no longer
        self.pos = pos # no longer
        self.text = text
        self.fontname = fontname
        self.change_size(size)
        self.color = color
    def change_size(self,size):
        self.size = size
        self.font = pygame.font.Font(self.fontname,size)
    def draw(self, pos = None, screen = None):
        if (screen==None):
            screen = self.screen
        if (screen==None):
            screen = pygame.display.get_surface()
        if (pos==None):
            pos = self.pos 
        text_surface = self.font.render(self.text, False, self.color)
        self.screen.blit(text_surface,pos)

class Button():
    def __init__(self, screen = None, pos = (0,0), size = (100,100), image = None, text = None):
        self.image = image
        self.change_size(size)
        if (image!=None): self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.screen = screen # no longer
    def change_size(self,size):
        self.size = size
        if (self.image!=None): self.image = pygame.transform.scale(self.image,size)
    def draw(self, pos = None, screen = None):
        if (screen==None):
            screen = self.screen
        if (screen==None):
            screen = pygame.display.get_surface()
        if (pos==None):
            pos = self.rect.topleft
        self.screen.blit(self.image, pos)

    @classmethod
    def create_with_color(cls):
        pass

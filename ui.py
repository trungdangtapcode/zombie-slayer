import pygame
from settings import *
import system

class UI():
    """
    Represents the user interface (UI) for the player, including health, stability, and slot bars.

    Attributes:
        screen (Surface): The screen where the UI elements are drawn.
        hp_bar (HealthBar): The health bar for displaying the player's health.
        stability_bar (StabilityBar): The stability bar for displaying the player's weapon stability.
        slot_bar (SlotBar): The slot bar for displaying the player's inventory slots.
        player (Player): The player object associated with this UI.

    Methods:
        display(): Renders the UI elements on the screen.
        draw_sprite(sprite): Draws a given sprite on the screen.
    """
    def __init__(self, player):
        self.screen = system.screen
        self.hp_bar = HealthBar(player)
        self.stability_bar = StabilityBar(player)
        self.slot_bar = SlotBar(player)
        self.player = player

    def display(self):
        self.hp_bar.display()
        self.stability_bar.display()
        self.slot_bar.display()
        
        w, h = self.screen.get_size()

        if (self.player.current_weapon):
            weapon = self.player.current_weapon
            s = str(weapon.clip_ammo) + '/' + str(weapon.total_ammo)
            ammo_text = Text(s, 35, "White", topleft = (w-250,10))
            self.draw_sprite(ammo_text)
        elif (self.player.current_food):
            food = self.player.current_food


    def draw_sprite(self, sprite):
        pos = sprite.rect.topleft
        self.screen.blit(sprite.image, pos)

class UI_Object():
    """
    Base class for UI objects, providing common methods for drawing on the screen.

    Attributes:
        screen (Surface): The screen where the UI object is drawn.
        player (Player): The player object associated with this UI object.

    Methods:
        rect_to_surf(rect, color): Creates a surface with the given rect size and color.
        apply_mask(surf, mask, pos): Applies a mask to a surface at a given position.
        draw_rect(color, rect): Draws a rectangle of the given color and size.
        draw_parallelogram(color, rect): Draws a parallelogram based on a given rectangle.
        blit(image, pos): Draws an image on the screen at a given position.
    """
    def __init__(self, player):
        self.screen = system.screen   
        self.player = player
    
    def rect_to_surf(self, rect, color):
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        s.fill(color)
        return s

    def apply_mask(self, surf, mask, pos = (0,0)):
        surf.blit(mask,pos,None,pygame.BLEND_RGBA_MULT)

    def draw_rect(self, color, rect):
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        s.fill(color)
        self.screen.blit(s,rect.topleft)

    def draw_parallelogram(self, color, rect: pygame.Rect):
        "rect -> parallelogram. width += height"
        if (rect.width==0): return
        height = rect.height
        p1 = pygame.math.Vector2(0,0)
        p2 = pygame.math.Vector2(rect.topright)-rect.topleft
        p3 = pygame.math.Vector2(rect.bottomright)-rect.topleft
        p4 = pygame.math.Vector2(rect.bottomleft)-rect.topleft
        p1.x += height
        p2.x += height
        surface = pygame.Surface((rect.size[0]+height,rect.size[1]), pygame.SRCALPHA)
        pygame.draw.polygon(surface, color, [p1,p2,p3,p4])
        if (len(color)>3): surface.set_alpha(color[3])
        self.screen.blit(surface, rect.topleft)
    
    def blit(self, image, pos):
        self.screen.blit(image,pos)


class HealthBar(UI_Object):
    """
    Represents a health bar for displaying the player's health.

    Attributes:
        HEALTH_BAR_WIDTH (int): Width of the health bar.
        HEALTH_BAR_HEIGHT (int): Height of the health bar.
        BAR_BG_COLOR (tuple): Background color of the health bar.
        HP_BAR_COLOR_HIGH (tuple): Color of the health bar when health is high.
        HP_BAR_COLOR_MEDIUM (tuple): Color of the health bar when health is medium.
        HP_BAR_COLOR_LOW (tuple): Color of the health bar when health is low.
        health_bar_rect (Rect): Rectangular area representing the health bar.
        current_drain (float): Current drain value for the health bar animation.
        drain_speed (int): Speed at which the health bar drains.
        DRAIN_COLOR (tuple): Color of the health bar drain.
        path (str): Path to the graphics directory.
        hp_mask_left (Surface): Mask for the left side of the health bar.
        hp_mask_right (Surface): Mask for the right side of the health bar.

    Methods:
        show_bar(current, max_amount, bg_rect, color): Displays the health bar with the current health.
        display(): Renders the health bar on the screen.
    """
    def __init__(self, player):
        super().__init__(player)
        self.HEALTH_BAR_WIDTH = 600
        self.HEALTH_BAR_HEIGHT = 20
        self.BAR_BG_COLOR = (0,0,0,150)
        self.HP_BAR_COLOR_HIGH = (87,240,56,255)
        self.HP_BAR_COLOR_MEDIUM = (235,242,39,255)
        self.HP_BAR_COLOR_LOW = (250,60,85,255)

        #init bar
        self.health_bar_rect = pygame.Rect(30,50,self.HEALTH_BAR_WIDTH,self.HEALTH_BAR_HEIGHT)
        self.current_drain = 0
        self.drain_speed = 3 #1/x second to hp
        self.DRAIN_COLOR = (255,255,255,255)

        self.path = PATH + 'graphics/ui/'
        self.hp_mask_left = pygame.image.load(self.path+'hp_bar_mask_left.png').convert_alpha()
        self.hp_mask_right = pygame.image.load(self.path+'hp_bar_mask_right.png').convert_alpha()

    def show_bar(self,current, max_amount, bg_rect, color):
        #bg
        self.draw_parallelogram(self.BAR_BG_COLOR, bg_rect)

        ratio = current/max_amount

        self.current_drain = max(self.current_drain, ratio)
        dx = (self.current_drain-ratio)*system.delta_time*self.drain_speed
        self.current_drain -= dx
        drain_width = self.current_drain*bg_rect.width
        drain_rect = bg_rect.copy()
        drain_rect.width = drain_width
        self.draw_parallelogram(self.DRAIN_COLOR, drain_rect)

        #current bar
        current_width = ratio*bg_rect.width
        current_rect = bg_rect.copy()
        current_rect.width = current_width
        color = self.HP_BAR_COLOR_LOW
        if (ratio>0.6):
            color = self.HP_BAR_COLOR_HIGH
        elif (ratio>0.3): 
            color = self.HP_BAR_COLOR_MEDIUM
        self.draw_parallelogram(color, current_rect)

    def display(self):
        player = self.player
        self.show_bar(player.health, player.max_health, self.health_bar_rect, "dmm")

class StabilityBar(UI_Object):
    """
    Represents a stability bar for displaying the player's weapon stability.

    Attributes:
        BAR_WIDTH (int): Width of the stability bar.
        BAR_HEIGHT (int): Height of the stability bar.
        BAR_BG_COLOR (tuple): Background color of the stability bar.
        BAR_COLOR_LOW (tuple): Color of the stability bar when stability is low.
        BAR_COLOR_HIGH (tuple): Color of the stability bar when stability is high.
        bar_rect (Rect): Rectangular area representing the stability bar.

    Methods:
        show_bar(current, max_amount, bg_rect, min_amount): Displays the stability bar with the current stability.
        display(): Renders the stability bar on the screen.
    """
    def __init__(self, player):
        super().__init__(player)
        self.BAR_WIDTH = 300
        self.BAR_HEIGHT = 10
        self.BAR_BG_COLOR = (0,0,0,150)
        self.BAR_COLOR_LOW = (49,230,55,255)
        self.BAR_COLOR_HIGH = (238,88,13,255)

        #init bar
        self.bar_rect = pygame.Rect(30,50+20,self.BAR_WIDTH,self.BAR_HEIGHT)

    def show_bar(self,current, max_amount, bg_rect, min_amount):
        #bg
        self.draw_parallelogram(self.BAR_BG_COLOR, bg_rect)

        #current bar
        current_width = current/max_amount*bg_rect.width
        current_rect = bg_rect.copy()
        current_rect.width = current_width
        color = self.BAR_COLOR_LOW if current<min_amount else self.BAR_COLOR_HIGH
        self.draw_parallelogram(color, current_rect)

    def display(self):
        player = self.player
        if (player.current_weapon): 
            weapon = player.current_weapon
            self.show_bar(weapon.stability, weapon.max_stability, self.bar_rect, weapon.min_stability)  
        else: 
            self.show_bar(0, 100, self.bar_rect, 0)  

class Text:
    """
    Represents a text object for rendering text on the screen.

    Attributes:
        image (Surface): Surface containing the rendered text.
        rect (Rect): Rectangular area representing the text position and size.

    Methods:
        None
    """
    def __init__(self, text, size, color = "Red", center = None, topleft = None):
        self.image = Font.get_font(size).render(text, False, color)
        if (center!=None):
            self.rect = self.image.get_rect(center = center)
        elif (topleft!=None):
            self.rect = self.image.get_rect(topleft = topleft)
        else: raise Exception("Dm topleft hay center")

class Font:
    """
    Provides a method for retrieving fonts.

    Methods:
        get_font(size): Returns a font object with the given size.
    """
    def get_font(size):
        path = PATH + 'font/slkscr.ttf'
        return pygame.font.Font(path, size)
    
class SlotBar(UI_Object):
    """
    Represents a slot bar for displaying the player's inventory slots.

    Attributes:
        SLOT_BG_COLOR (tuple): Background color of the slot.
        SLOT_BG_COLOR_PRIMARY (tuple): Background color of the primary slot.
        margin_left (int): Left margin for positioning the slots.
        margin_bottom (int): Bottom margin for positioning the slots.
        slot_side_length (int): Side length of each slot.
        slot_size (tuple): Size of each slot.
        slot_spacing (int): Spacing between slots.
        topleft_pos (Vector2): Top-left position for the first slot.
        player (Player): The player object associated with this slot bar.
        inventory (list): List of inventory items.
        primary_frame_thickness (int): Thickness of the primary slot frame.
        primary_frame_color (tuple): Color of the primary slot frame.
        primary_slot_image (Surface): Image for the primary slot frame.

    Methods:
        display_slot(): Displays the inventory slots on the screen.
        display(): Renders the slot bar on the screen.
    """
    def __init__(self, player):
        super().__init__(player)
        self.SLOT_BG_COLOR = (200,200,200,50)
        self.SLOT_BG_COLOR_PRIMARY = (220,220,220,100)
        self.margin_left = 120 *2
        self.margin_bottom = 30 + 20
        self.slot_side_length = 80
        self.slot_size = (self.slot_side_length,self.slot_side_length)
        self.slot_spacing = 10
        self.topleft_pos = pygame.math.Vector2(self.margin_left,
            self.screen.get_height()-self.margin_bottom-self.slot_side_length)

        self.player = player
        self.inventory = player.inventory

        self.primary_frame_thickness = 3
        self.primary_frame_color = (150, 150, 50, 255)
        self.primary_slot_image = pygame.surface.Surface((2*self.primary_frame_thickness+self.slot_side_length)*pygame.math.Vector2(1,1)).convert_alpha()
        self.primary_slot_image.fill(self.primary_frame_color)
        pos = (pygame.math.Vector2(self.primary_slot_image.get_size())-self.slot_size)/2
        sub_img = pygame.surface.Surface(self.slot_size).convert_alpha()
        sub_img.fill((255,255,255,255))
        self.primary_slot_image.blit(sub_img,pos, special_flags = pygame.BLEND_RGBA_SUB)    

    def display_slot(self):
        for slot in range(9):
            #bg
            pos = self.topleft_pos.copy()
            pos += pygame.math.Vector2(self.slot_side_length+self.slot_spacing,0)*slot
            rect = pygame.rect.Rect(pos, self.slot_size)
            color = self.SLOT_BG_COLOR if slot != self.player.current_primary else self.SLOT_BG_COLOR_PRIMARY
            self.draw_rect(color, rect)

            #frame
            if (slot==self.player.current_primary):
                self.blit(self.primary_slot_image, pos - self.primary_frame_thickness*pygame.math.Vector2(1,1))

            #avt
            if (slot<len(self.inventory)):
                item = self.inventory[slot]
                img = pygame.transform.scale(item.avatar, self.slot_size)
                self.blit(img, pos)

            #number
            if (slot<len(self.inventory)):
                item = self.inventory[slot]
                if (hasattr(item,'food')):
                    num_text = Text(str(item.food.quantity), 15, "white", topleft = pos)
                    self.blit(num_text.image, pos)

    def display(self):
        self.display_slot()

class Button:
    """
    Represents a button in the UI.

    Attributes:
        image (Surface): Image of the button.
        font (Font): Font used for the button text.
        base_color (tuple): Base color of the button text.
        hovering_color (tuple): Color of the button text when hovered.
        text_input (str): Text displayed on the button.
        text (Surface): Rendered text surface.
        rect (Rect): Rectangular area representing the button.
        text_rect (Rect): Rectangular area representing the button text.
        is_available (bool): Whether the button is available for interaction.

    Methods:
        update(screen): Updates the button display on the screen.
        checkForInput(position): Checks if the button is clicked.
        disable(): Disables the button.
        changeColor(position): Changes the button color based on mouse position.
    """
    def __init__(self, center, text_input, font, base_color, hovering_color,
                    image = None, bg_color = None, margin = 0):
        self.image = image
        self.font = font
        self.base_color, self.hovering_color = base_color, hovering_color
        self.text_input = text_input
        self.text = self.font.render(self.text_input, True, self.base_color)
        #image -> bg 1 color -> none 
        if self.image is None:
            if bg_color is None:
                self.image = pygame.Surface(self.text.get_size()+pygame.math.Vector2(margin, margin), pygame.SRCALPHA)
            else:
                self.image = pygame.Surface(self.text.get_size()+pygame.math.Vector2(margin, margin))
                self.image.fill(bg_color)
        self.rect = self.image.get_rect(center=center)
        self.text_rect = self.text.get_rect(center=center)
        self.is_available = True

    def update(self, screen):
        mouse = pygame.mouse.get_pos()
        self.changeColor(mouse)
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        if (not self.is_available): return False
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            return True
        return False

    def disable(self):
        self.is_available = False

    def changeColor(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            self.text = self.font.render(self.text_input, True, self.hovering_color)
        else:
            self.text = self.font.render(self.text_input, True, self.base_color)

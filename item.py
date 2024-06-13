import pygame
from settings import *
import system
import file
from weapon import Gun, FlameThrower, MissileLaucher
from food import Food

class ItemObject(pygame.sprite.Sprite):
    """ =))
        Represents a basic item object in the game.

        Methods:
            import_asset(path): Placeholder method for importing assets.
    """
    def __init__(self, pos, groups):
        super().__init__(groups)
        
    def import_asset(self, path):
        return
    
class ItemInventory():
    """
    Represents a basic inventory item.

    Methods:
        import_asset(): Imports the asset for the item.
        change_owner(): Placeholder method for changing the item's owner.
    """
    def __init__(self):
        self.avatar = pygame.surface.Surface((1,1))
        
    def import_asset(self):
        path = self.path + 'avatar.png'
        image = pygame.image.load(path)
        self.avatar = image
    
    def change_owner(self):
        pass

class WeaponItemInventory(ItemInventory):
    """
    Represents a weapon inventory item.

    Methods:
        activate(): Activates the weapon.
        disable(): Disables the weapon.
    """
    def __init__(self, groups, player, name):
        super().__init__()
        self.path = PATH + 'graphics/weapon/' +  name + '/'
        self.weapon = None
        self.player = player
        self.import_asset()

    def activate(self):
        player_pos = self.player.hitbox.center
        self.weapon.current_player_center = pygame.math.Vector2(player_pos)
        self.weapon.rect.center = player_pos
        self.weapon.update()
        self.weapon.is_disable = False
    
    def disable(self):
        self.weapon.is_disable = True

class GunItemInventory(WeaponItemInventory):
    def __init__(self, groups, player, name = 'ak47'):
        super().__init__(groups, player, name)
        self.weapon = Gun(player, groups, name)

class FlameThrowerItemInventory(WeaponItemInventory):
    def __init__(self, groups, player, name = 'flamethrower'):
        super().__init__(groups, player, name)
        self.weapon = FlameThrower(player, groups, name)

class MissileLaucherItemInventory(WeaponItemInventory):
    def __init__(self, groups, player, name = 'missile_laucher'):
        super().__init__(groups, player, name)
        self.weapon = MissileLaucher(player, groups, name)

class FoodItemInventory(ItemInventory):
    """
    Represents a food inventory item.

    Methods:
        activate(): Activates the food item.
        disable(): Disables the food item.
    """
    def __init__(self, groups, player, name):
        super().__init__()
        self.path = PATH + 'graphics/food/' +  name + '/'
        self.food = Food(groups, name, player)
        # self.quantity = self.food.quantity
        self.player = player
        self.import_asset()

    def activate(self):
        self.food.is_update = True
    
    def disable(self):
        self.food.is_update = False
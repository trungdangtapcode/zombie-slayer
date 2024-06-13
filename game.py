import pygame
import GUI
import player 
from settings import *
from level import Level, MenuScreen, Level00, Level01
import system
from pygame.locals import *
import moderngl
import struct

VIRTUAL_RES = (SCREEN_WIDTH, SCREEN_HEIGHT)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('[OOP] Zombie Slayer: Nhu nhung con zombie co ban vao cung ton dan')
        debug = False

        self.CRT_filter = True if not debug else False
        if (self.CRT_filter):
            self.init_CRT() 
        else:
            pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
            system.screen = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
        # self.level = Level()
        self.level = MenuScreen()
        self.clock = pygame.time.Clock()
        if (debug): self.level.darkness_value = 0
        
        self.current_level = 0
        system.go_to_level = self.go_to_level
    def init_CRT(self):
        pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT),DOUBLEBUF|OPENGL)
        system.screen = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT)).convert((255, 65280, 16711680, 0))
        self.ctx = moderngl.create_context()
        ctx = self.ctx

        texture_coordinates = [0, 1,  1, 1,
                            0, 0,  1, 0]

        world_coordinates = [-1, -1,  1, -1,
                            -1,  1,  1,  1]

        render_indices = [0, 1, 2,
                        1, 2, 3]

        prog = ctx.program(
                vertex_shader='''#version 300 es
            in vec2 vert;
            in vec2 in_text;
            out vec2 v_text;
            void main() {
            gl_Position = vec4(vert, 0.0, 1.0);
            v_text = in_text;
            }
            ''',

                fragment_shader='''#version 300 es
            precision mediump float;
            uniform sampler2D Texture;

            out vec4 color;
            in vec2 v_text;
            uniform float current_time;

            void main() {
            vec2 center = vec2(0.5, 0.5);
            vec2 off_center = v_text - center;

            off_center *= 1.0 + 0.8 * pow(abs(off_center.yx), vec2(3));

            vec2 v_text2 = center+off_center;

            if (v_text2.x > 1.0 || v_text2.x < 0.0 ||
                v_text2.y > 1.0 || v_text2.y < 0.0){
                color=vec4(0.0, 0.0, 0.0, 1.0);
            } else {
                color = vec4(texture(Texture, v_text2).rgb, 1.0);
                float fv = fract((v_text2.y+0.05*current_time) * float(textureSize(Texture,0).y)*0.08);
                fv=min(1.0, 0.8+0.5*min(fv, 1.0-fv));
                color.rgb*=fv;
            }
            }
            ''')
        self.prog = prog

        self.screen_texture = ctx.texture(
            VIRTUAL_RES, 3,
            pygame.image.tostring(system.screen, "RGB", 1))
        screen_texture = self.screen_texture

        screen_texture.repeat_x = False
        screen_texture.repeat_y = False

        vbo = ctx.buffer(struct.pack('8f', *world_coordinates))
        uvmap = ctx.buffer(struct.pack('8f', *texture_coordinates))
        ibo= ctx.buffer(struct.pack('6I', *render_indices))

        vao_content = [
            (vbo, '2f', 'vert'),
            (uvmap, '2f', 'in_text')
        ]

        self.vao = ctx.vertex_array(prog, vao_content, ibo)
    
    def render_CRT(self):
        self.prog['current_time'] = system.time
        texture_data = system.screen.get_view('1')
        self.screen_texture.write(texture_data)
        self.ctx.clear(14/255,40/255,66/255)
        self.screen_texture.use()
        self.vao.render()
        pygame.display.flip()

    def run(self):
        if (self.CRT_filter):
            self.run_CRT()
        else:
            self.run_no_CRT()

    def run_CRT(self):
        self.is_run = True
        while self.is_run:
            mouse_wheel_event_check = False
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_w:
                    continue
                    pygame.mixer.music.fadeout(1000)
                if event.type == pygame.QUIT:
                    self.is_run = False
                if event.type == pygame.MOUSEWHEEL:
                    mouse_wheel_event_check = True
                    system.mouse_scroll = event.y
            if (not mouse_wheel_event_check): system.mouse_scroll = 0
            # self.screen.fill('black')
            system.screen.fill('black')
            self.level.update()
            # self.screen.blit(self.level.sprite_sheet.get_image(71), (0,0))
            self.render_CRT()
            system.delta_time = self.clock.tick(FPS)/1000
            system.time += system.delta_time

    def run_no_CRT(self):
        """
             singleton: mouse, system, camera
            Game -> Level -> Tile[Obstacle, Visible]
        """
        self.is_run = True
        while self.is_run:
            mouse_wheel_event_check = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_run = False
                if event.type == pygame.MOUSEWHEEL:
                    mouse_wheel_event_check = True
                    system.mouse_scroll = event.y
            if (not mouse_wheel_event_check): system.mouse_scroll = 0
            #self.screen.fill('black')
            system.screen.fill('black')
            self.level.darkness_value = 0
            self.level.update()
            pygame.display.get_surface().blit(system.screen,(0,0))
            # self.screen.blit(self.level.sprite_sheet.get_image(71), (0,0))
            pygame.display.update()
            system.delta_time = self.clock.tick(FPS)/1000
            
            # print('FPS: ',self.clock.get_fps())
        # filehandler = open('ccbm', 'wb') 
        # pickle.dump(self, filehandler)

    def go_to_level(self, level = None):
        if (level == None):
            self.current_level = -1
            self.level = MenuScreen()
            return

        if (level == 'next'):
            level = self.current_level + 1
            if (level>1):
                level = -1
        elif (level == 'restart'):
            level = self.current_level
        elif (level == 'exit'):
            self.is_run = False
            return

        
        self.current_level = level
        if self.current_level==-1:
            self.level = MenuScreen()
        elif self.current_level==0:
            self.level = Level00()
        elif self.current_level==1:
            self.level = Level01()
        else:
            assert False, f"Cant find level: {self.current_level}"
            self.level = None


game = Game()
game.run()




# button_bg = pygame.image.load('oop/image/button_01.png').convert_alpha()
# x = GUI.Button(screen, (100,100), (200,50), button_bg, 'xin chao')
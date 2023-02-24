import numpy as np

try:
    import pygame
    from pygame import gfxdraw
except:
    print("No pygame installed, ignoring import")
from luxai_s2.map.board import Board
from luxai_s2.state import State
from luxai_s2.unit import UnitType

try:
    import matplotlib.pyplot as plt

    color_to_rgb = dict(
        yellow=[236, 238, 126],
        green=[173, 214, 113],
        blue=[154, 210, 203],
        red=[164, 74, 63],
    )
    strain_colors = plt.colormaps["Pastel1"]
except:
    pass


class Visualizer:
    def __init__(self, w=48, h=48) -> None:
        self.screen_size = (1000, 1000)
        self.tile_width = min(self.screen_size[0] // w, self.screen_size[1] // h,)
        self.WINDOW_SIZE = (self.tile_width * w, self.tile_width * h)
        self.surf = pygame.Surface(self.WINDOW_SIZE)
        self.surf.fill([239, 120, 79])
        pygame.font.init()
        self.screen = None
        self.width = w
        self.height = h

    def init_window(self):
        pygame.init()
        pygame.display.init()
        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)

    def rubble_color(self, rubble):
        max_r = np.max(rubble)
        opacity = (0.2 + min(rubble / max_r, 1) * 0.8) if max_r > 0 else 0
        return [239, 120, 79, opacity * 255]

    def update_scene(self, state: State):
        self.surf.fill([200, 200, 200, 255])
        for x in range(self.width):
            for y in range(self.height):
                rubble_amt = state[x][y]
                rubble_color = self.rubble_color(rubble_amt)
                gfxdraw.box(
                    self.surf,
                    (
                        self.tile_width * x,
                        self.tile_width * y,
                        self.tile_width,
                        self.tile_width,
                    ),
                    rubble_color,
                )

    def render(self):
        pygame.display.update()
        self.screen.blit(self.surf, (0, 0))

    def _create_image_array(self, screen, size):
        scaled_screen = pygame.transform.smoothscale(screen, size)
        return np.transpose(
            np.array(pygame.surfarray.pixels3d(scaled_screen)), axes=(1, 0, 2)
        )

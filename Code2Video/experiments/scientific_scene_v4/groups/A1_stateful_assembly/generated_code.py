from biology_runtime import ScientificScene
from manim import *


class Section4Scene(ScientificScene):
    MODE = "assembly"

    def construct(self):
        self.camera.background_color = "#0E1116"
        self.render_scene(validation_mode="assembly")
        self.wait(0.5)

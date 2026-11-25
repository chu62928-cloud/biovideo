from biology_runtime import ScientificScene
from manim import *
import numpy as np
import math


class Section4Scene(ScientificScene):
    MODE = "full"

    def construct(self):
        self.camera.background_color = "#0E1116"
        self.render_scene(validation_mode="full")
        self.wait(0.5)

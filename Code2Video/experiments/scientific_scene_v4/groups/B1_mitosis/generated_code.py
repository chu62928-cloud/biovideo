import math
import numpy as np
from manim import *
from biology_runtime import ScientificScene


class Section4Scene(ScientificScene):
    def construct(self):
        self.camera.background_color = "#0B1221"
        self.render_scene(validation_mode="full")
        self.wait(1.0)

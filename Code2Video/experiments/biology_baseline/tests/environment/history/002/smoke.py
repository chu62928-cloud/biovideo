from manim import *
class Smoke(Scene):
 def construct(self):
  self.play(Create(Circle()))
  self.wait(0.2)

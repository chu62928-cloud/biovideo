from manim import *
class LatexSmoke(Scene):
 def construct(self):
  self.play(Write(MathTex(r"A=\begin{pmatrix}1&0\\0&1\end{pmatrix}")))
  self.wait(0.2)

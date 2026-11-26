from manim import Text
from scientific_scene.adapters.typed_manim_adapter import TypedScientificScene
class Candidate(TypedScientificScene):
    def construct(self):
        self.camera.background_color = '#11253B'
        self.add(Text('Mitosis   |   From alignment to separation',font_size=33).move_to([0,3.35,0]))
        self.add(Text('RESEARCH CANDIDATE     /     ONE DUPLICATED CHROMOSOME',font_size=16,color='#ACC8DA').move_to([0,2.82,0]))
        self.render_typed('final_scene.json')

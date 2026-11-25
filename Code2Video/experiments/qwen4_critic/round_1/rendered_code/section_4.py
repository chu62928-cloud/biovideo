from manim import *
import numpy as np

class TeachingScene(Scene):
    def setup_layout(self, title_text, lecture_lines):
        # BASE
        self.camera.background_color = "#000000"
        self.title = Text(title_text, font_size=28, color=WHITE).to_edge(UP)
        self.add(self.title)

        # Left-side lecture content (bullets with "-")
        lecture_texts = [Text(line, font_size=22, color=WHITE) for line in lecture_lines]
        self.lecture = VGroup(*lecture_texts).arrange(DOWN, aligned_edge=LEFT).scale(0.8)
        self.lecture.to_edge(LEFT, buff=0.2)
        self.add(self.lecture)

        # Define fine-grained animation grid (4x4 grid on right side)
        self.grid = {}
        rows = ["A", "B", "C", "D", "E", "F"]  # Top to bottom
        cols = ["1", "2", "3", "4", "5", "6"]  # Left to right

        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                x = 0.5 + j * 1
                y = 2.2 - i * 1
                self.grid[f"{row}{col}"] = np.array([x, y, 0])

    def place_at_grid(self, mobject, grid_pos, scale_factor=1.0):
        mobject.scale(scale_factor)
        mobject.move_to(self.grid[grid_pos])
        return mobject

    def place_in_area(self, mobject, top_left, bottom_right, scale_factor=1.0):
        tl_pos = self.grid[top_left]
        br_pos = self.grid[bottom_right]
        
        # Calculate center of the area
        center_x = (tl_pos[0] + br_pos[0]) / 2
        center_y = (tl_pos[1] + br_pos[1]) / 2
        center = np.array([center_x, center_y, 0])
        
        mobject.scale(scale_factor)
        mobject.move_to(center)
        return mobject

class Section4Scene(TeachingScene):
    def construct(self):
        self.setup_layout("Sec 4: Priming and DNA Polymerase Action", [
            'Primase lays down RNA primers.',
            "Polymerase builds DNA only 5' to 3'.",
            'Leading strand is continuous and smooth.',
            'Lagging strand forms Okazaki fragments.',
            'Ligase joins fragments into one strand.'
        ])
        
        # === Animation for Lecture Line 1 ===
        # Highlight lecture line 1
        self.lecture[0].set_color("#BA68C8")  # Purple color for Primase
        
        # Create the replication fork structure
        # Two template strands: one going up-right, one going down-right
        top_template = Line(
            start=self.grid['B2'],
            end=self.grid['A6'],
            color="#90A4AE",
            stroke_width=4
        )
        bottom_template = Line(
            start=self.grid['D2'],
            end=self.grid['E6'],
            color="#90A4AE",
            stroke_width=4
        )
        
        # Add template strands
        self.play(Create(top_template), Create(bottom_template), run_time=1.5)
        
        # Label templates
        top_label = Text("Template", font_size=16, color="#90A4AE")
        top_label.next_to(top_template, UP, buff=0.15)
        bottom_label = Text("Template", font_size=16, color="#90A4AE")
        bottom_label.next_to(bottom_template, DOWN, buff=0.15)
        
        self.play(Write(top_label), Write(bottom_label), run_time=1)
        
        # Primase icon (purple circle with "P")
        primase_circle = Circle(radius=0.25, color="#BA68C8", fill_opacity=0.8)
        primase_text = Text("Primase", font_size=14, color="#BA68C8")
        primase_label = VGroup(primase_circle, primase_text)
        primase_label[1].next_to(primase_label[0], RIGHT, buff=0.1)
        
        # Place primase near the fork (start of top template)
        primase_label.move_to(self.grid['B2'] + np.array([-0.5, 0.3, 0]))
        
        self.play(FadeIn(primase_label), run_time=1)
        
        # RNA primers on each template strand
        primer_top = Rectangle(width=0.6, height=0.12, color="#FFB74D", fill_opacity=0.9)
        primer_top.move_to(top_template.get_start() + np.array([0.3, 0.08, 0]))
        
        primer_bottom = Rectangle(width=0.6, height=0.12, color="#FFB74D", fill_opacity=0.9)
        primer_bottom.move_to(bottom_template.get_start() + np.array([0.3, -0.08, 0]))
        
        # Labels for primers
        primer_top_label = Text("RNA Primer", font_size=14, color="#FFB74D")
        primer_top_label.next_to(primer_top, UP, buff=0.1)
        
        primer_bottom_label = Text("RNA Primer", font_size=14, color="#FFB74D")
        primer_bottom_label.next_to(primer_bottom, DOWN, buff=0.1)
        
        # Animation for primase action
        self.play(FadeIn(primer_top), FadeIn(primer_bottom), run_time=1.5)
        self.play(Write(primer_top_label), Write(primer_bottom_label), run_time=1)
        
        self.wait(1)
        
        # === Animation for Lecture Line 2 ===
        # Highlight lecture line 2
        self.lecture[0].set_color(WHITE)
        self.lecture[1].set_color("#4DD0E1")  # Cyan color for Polymerase
        
        # Polymerase icon (cyan circle with "Pol")
        pol_circle = Circle(radius=0.25, color="#4DD0E1", fill_opacity=0.8)
        pol_text = Text("DNA Pol", font_size=14, color="#4DD0E1")
        pol_label = VGroup(pol_circle, pol_text)
        pol_label[1].next_to(pol_label[0], RIGHT, buff=0.1)
        
        # Place polymerase near the primer on top strand
        pol_label.move_to(self.grid['B3'] + np.array([0.3, 0.4, 0]))
        
        self.play(FadeIn(pol_label), run_time=1)
        
        # Directional arrow showing 5' to 3'
        direction_arrow = Arrow(
            start=top_template.get_start() + np.array([0.6, 0.3, 0]),
            end=top_template.get_start() + np.array([1.6, 0.55, 0]),
            color="#FFEB3B",
            stroke_width=3,
            tip_length=0.15
        )
        
        direction_label = Text("5' → 3'", font_size=16, color="#FFEB3B")
        direction_label.next_to(direction_arrow, UP, buff=0.1)
        
        self.play(Create(direction_arrow), Write(direction_label), run_time=1)
        
        # Show nucleotides being added (small green blocks)
        nucleotide_positions_top = [
            top_template.get_start() + np.array([0.7, 0.1, 0]),
            top_template.get_start() + np.array([1.0, 0.2, 0]),
            top_template.get_start() + np.array([1.3, 0.3, 0]),
        ]
        
        nucleotides_top = VGroup(*[
            Rectangle(width=0.2, height=0.1, color="#69F0AE", fill_opacity=0.9).move_to(pos)
            for pos in nucleotide_positions_top
        ])
        
        self.play(
            *[FadeIn(nuc) for nuc in nucleotides_top],
            run_time=1.5
        )
        
        self.wait(1)
        
        # === Animation for Lecture Line 3 ===
        # Highlight lecture line 3
        self.lecture[1].set_color(WHITE)
        self.lecture[2].set_color("#69F0AE")  # Green for leading strand
        
        # Move polymerase forward on leading strand (top)
        new_pol_pos_top = self.grid['A4'] + np.array([-0.2, 0.1, 0])
        self.play(
            pol_label.animate.move_to(new_pol_pos_top),
            run_time=2
        )
        
        # Build continuous green strand on top template
        leading_strand = Line(
            start=top_template.get_start() + np.array([0.6, 0.1, 0]),
            end=top_template.get_end() + np.array([-0.1, 0.05, 0]),
            color="#69F0AE",
            stroke_width=6
        )
        
        self.play(Create(leading_strand), run_time=2.5)
        
        # Update direction arrow to follow polymerase
        new_arrow = Arrow(
            start=top_template.get_start() + np.array([1.0, 0.5, 0]),
            end=top_template.get_start() + np.array([2.0, 0.75, 0]),
            color="#FFEB3B",
            stroke_width=3,
            tip_length=0.15
        )
        
        self.play(
            Transform(direction_arrow, new_arrow),
            run_time=1.5
        )
        
        self.wait(1)
        
        # === Animation for Lecture Line 4 ===
        # Highlight lecture line 4
        self.lecture[2].set_color(WHITE)
        self.lecture[3].set_color("#FFAB91")  # Salmon for Okazaki
        
        # Move polymerase to lagging strand (bottom)
        pol_label_bottom = VGroup(
            Circle(radius=0.25, color="#4DD0E1", fill_opacity=0.8),
            Text("DNA Pol", font_size=14, color="#4DD0E1")
        )
        pol_label_bottom[1].next_to(pol_label_bottom[0], RIGHT, buff=0.1)
        pol_label_bottom.move_to(self.grid['E3'] + np.array([0.3, -0.5, 0]))
        
        self.play(
            Transform(pol_label, pol_label_bottom),
            run_time=1.5
        )
        
        # Build short Okazaki fragments on bottom template
        # First fragment
        frag1 = Line(
            start=bottom_template.get_start() + np.array([0.6, -0.1, 0]),
            end=bottom_template.get_start() + np.array([1.2, -0.2, 0]),
            color="#69F0AE",
            stroke_width=6
        )
        
        okazaki_label1 = Text("Okazaki", font_size=14, color="#FFAB91")
        okazaki_label1.next_to(frag1, DOWN, buff=0.15)
        
        self.play(
            Create(frag1),
            Write(okazaki_label1),
            run_time=1.5
        )
        
        # Move polymerase forward
        pol_label_bottom_2 = pol_label_bottom.copy()
        pol_label_bottom_2.move_to(self.grid['E4'] + np.array([0.2, -0.6, 0]))
        
        self.play(
            Transform(pol_label, pol_label_bottom_2),
            run_time=1
        )
        
        # Second fragment
        frag2 = Line(
            start=bottom_template.get_start() + np.array([1.5, -0.25, 0]),
            end=bottom_template.get_start() + np.array([2.1, -0.35, 0]),
            color="#69F0AE",
            stroke_width=6
        )
        
        okazaki_label2 = Text("Okazaki", font_size=14, color="#FFAB91")
        okazaki_label2.next_to(frag2, DOWN, buff=0.15)
        
        self.play(
            Create(frag2),
            Write(okazaki_label2),
            run_time=1.5
        )
        
        # Show gap between fragments
        gap_indicator = DashedLine(
            start=frag1.get_end(),
            end=frag2.get_start(),
            color="#FFAB91",
            stroke_width=2,
            dash_length=0.05
        )
        
        gap_label = Text("Gap", font_size=14, color="#FFAB91")
        gap_label.next_to(gap_indicator, DOWN, buff=0.1)
        
        self.play(
            Create(gap_indicator),
            Write(gap_label),
            run_time=1
        )
        
        self.wait(1)
        
        # === Animation for Lecture Line 5 ===
        # Highlight lecture line 5
        self.lecture[3].set_color(WHITE)
        self.lecture[4].set_color("#FFD54F")  # Gold for Ligase
        
        # Ligase icon (gold circle with "Lig")
        ligase_circle = Circle(radius=0.25, color="#FFD54F", fill_opacity=0.8)
        ligase_text = Text("Ligase", font_size=14, color="#FFD54F")
        ligase_label = VGroup(ligase_circle, ligase_text)
        ligase_label[1].next_to(ligase_label[0], RIGHT, buff=0.1)
        
        # Place ligase near the gap
        ligase_label.move_to(self.grid['D5'] + np.array([0, -0.5, 0]))
        
        self.play(FadeIn(ligase_label), run_time=1)
        
        # Seal the gap - animate a connecting segment
        seal_segment = Line(
            start=frag1.get_end(),
            end=frag2.get_start(),
            color="#69F0AE",
            stroke_width=6
        )
        
        # Fade out gap indicator and label
        self.play(
            FadeOut(gap_indicator),
            FadeOut(gap_label),
            run_time=0.5
        )
        
        # Create continuous strand by sealing
        self.play(
            Create(seal_segment),
            run_time=1.5
        )
        
        # Merge into one continuous strand
        continuous_lagging = VMobject(color="#69F0AE", stroke_width=6)
        continuous_lagging.set_points_as_corners([
            frag1.get_start(),
            frag1.get_end(),
            frag2.get_start(),
            frag2.get_end()
        ])
        
        self.play(
            Transform(VGroup(frag1, frag2, seal_segment), continuous_lagging),
            run_time=1.5
        )
        
        # Update labels - remove Okazaki labels and add "Sealed" label
        self.play(
            FadeOut(okazaki_label1),
            FadeOut(okazaki_label2),
            run_time=0.5
        )
        
        sealed_label = Text("Sealed", font_size=16, color="#69F0AE")
        sealed_label.next_to(continuous_lagging, DOWN, buff=0.2)
        
        self.play(Write(sealed_label), run_time=1)
        
        # Final highlight - fade primase and polymerase labels slightly
        self.play(
            ligase_label.animate.set_opacity(0.5),
            pol_label.animate.set_opacity(0.5),
            run_time=1
        )
        
        self.wait(2)
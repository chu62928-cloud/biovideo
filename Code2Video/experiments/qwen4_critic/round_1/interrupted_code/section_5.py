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

class Section5Scene(TeachingScene):
    def construct(self):
        self.setup_layout(
            "Sec 5: Proofreading and Repair",
            [
                "Polymerase proofreads with 3' to 5' exonuclease.",
                "Mismatched bases are removed and replaced.",
                "Error rate is only one in a billion.",
            ],
        )

        # Colors
        CYAN = "#4DD0E1"
        RED = "#FF5252"
        GREEN = "#69F0AE"
        YELLOW = "#FFEB3B"
        LIGHT_BLUE = "#B3E5FC"

        # === Animation for Lecture Line 1 ===
        # Build a simplified DNA strand: template strand + new strand
        # Template backbone (horizontal line)
        template_line = Line(
            self.grid["B1"] + RIGHT * -0.2,
            self.grid["B6"] + RIGHT * 0.2,
            color=GRAY_B,
            stroke_width=4,
        )
        # New strand backbone (horizontal line below)
        new_line = Line(
            self.grid["D1"] + RIGHT * -0.2,
            self.grid["D6"] + RIGHT * 0.2,
            color=GRAY_B,
            stroke_width=4,
        )
        self.play(Create(template_line), Create(new_line), run_time=0.6)

        # Place base pairs along the template strand positions
        base_cols = ["1", "2", "3", "4", "5"]
        base_colors = [CYAN, CYAN, CYAN, CYAN, None]  # last will be mismatch (red)
        template_bases = VGroup()
        new_bases = VGroup()
        for i, col in enumerate(base_cols):
            # template base (small rect on top)
            t_color = LIGHT_BLUE if i != 4 else YELLOW
            t_base = Rectangle(width=0.55, height=0.35, color=t_color, fill_opacity=0.6)
            t_base.move_to(self.grid[f"B{col}"])
            template_bases.add(t_base)
            # new base (initially none for the mismatch slot)
            if i != 4:
                color = base_colors[i] if base_colors[i] is not None else CYAN
                n_base = Rectangle(width=0.55, height=0.35, color=color, fill_opacity=0.7)
                n_base.move_to(self.grid[f"D{col}"])
                new_bases.add(n_base)

        self.play(FadeIn(template_bases), run_time=0.6)
        self.play(FadeIn(new_bases), run_time=0.8)

        # Polymerase enzyme (rounded rectangle) positioned near D4/D5
        polymerase = RoundedRectangle(
            width=1.2, height=0.9, corner_radius=0.15, color=CYAN, fill_opacity=0.35, stroke_width=3
        )
        polymerase.move_to(self.grid["D3"] + RIGHT * 0.4 + UP * 0.2)
        poly_label = Text("Polylmerase", font_size=16, color=CYAN)
        poly_label.next_to(polymerase, DOWN, buff=0.1)
        # fixing typo
        poly_label = Text("Polymerase", font_size=16, color=CYAN)
        poly_label.next_to(polymerase, DOWN, buff=0.1)
        self.play(FadeIn(polymerase), FadeIn(poly_label), run_time=0.6)

        # Highlight lecture line 1
        self.play(self.lecture[0].animate.set_color(CYAN), run_time=0.8)

        # Polymerase "moves" to add nucleotide (small back-and-forth jitter to imply adding)
        self.place_at_grid(polymerase_label, 'E4', scale_factor=0.8)
        self.play(polymerase.animate.shift(LEFT * 0.45), run_time=0.4)
        self.play(polymerase.animate.shift(RIGHT * 0.45), run_time=0.4)

        # The mismatched base appears (RED) at D5
        mismatch_base = Rectangle(width=0.55, height=0.35, color=RED, fill_opacity=0.85)
        mismatch_base.move_to(self.grid["D5"])
        self.play(FadeIn(mismatch_base, scale=1.4), run_time=0.6)

        # Mismatch label flashing above the red base
        mismatch_label = Text("Mismatch", font_size=18, color=RED, weight=BOLD)
        mismatch_label.next_to(mismatch_base, DOWN, buff=0.3)
        self.add(mismatch_label)
        self.play(
            mismatch_label.animate.set_opacity(1.0),
            run_time=0.2,
        )
        self.play(
            mismatch_label.animate.set_opacity(0.2),
            run_time=0.3,
        )
        self.play(
            mismatch_label.animate.set_opacity(1.0),
            run_time=0.3,
        )

        # === Animation for Lecture Line 2 ===
        # Highlight lecture line 2
        self.play(self.lecture[1].animate.set_color(YELLOW), run_time=0.8)

        # Polymerase backtracks (reverse arrow)
        back_arrow = CurvedArrow(
            start_point=polymerase.get_right() + UP * 0.3,
            end_point=polymerase.get_left() + UP * 0.3,
            angle=-PI / 2,
            color=YELLOW,
            stroke_width=3,
        )
        self.play(Create(back_arrow), run_time=0.6)
        self.play(polymerase.animate.shift(LEFT * 1.0), run_time=0.8)
        self.place_at_grid(proofreading_label, 'C4', scale_factor=0.8)

        # Proofreading label appears
        proof_label = Text("Proofreading", font_size=18, color=YELLOW, weight=BOLD)
        proof_label.move_to(self.grid["C1"] + RIGHT * 0.1)
        self.play(FadeIn(proof_label, scale=1.2), run_time=0.6)

        # Remove the mismatched red base (fade out + slight upward jiggle)
        self.play(
            mismatch_base.animate.shift(UP * 0.4).set_opacity(0.0),
            FadeOut(mismatch_label),
            run_time=0.8,
        )
        self.remove(mismatch_base, mismatch_label)

        # Insert the correct GREEN base in its place
        correct_base = Rectangle(width=0.55, height=0.35, color=GREEN, fill_opacity=0.85)
        correct_base.move_to(self.grid["D5"])
        self.play(FadeIn(correct_base, scale=1.4), run_time=0.8)

        # Polymerase moves forward again to continue
        self.play(polymerase.animate.shift(RIGHT * 1.0), run_time=0.7)
        self.play(FadeOut(poly_label), run_time=0.3)

        # === Animation for Lecture Line 3 ===
        # Highlight lecture line 3
        self.play(self.lecture[2].animate.set_color(LIGHT_BLUE), run_time=0.8)

        # Error rate counter area (E2..F5)
        counter = Text("1 error in 10^9", font_size=30, color=LIGHT_BLUE, weight=BOLD)
        self.place_in_area(counter, 'F2', 'F4', scale_factor=0.9)

        # Sanity: keep counter near the strand but below it
        counter.move_to(self.grid["F3"] + UP * 0.1)

        self.play(FadeIn(counter, scale=1.1), run_time=0.8)

        # Pulse the counter brightly
        self.play(counter.animate.set_color(WHITE), run_time=0.35)
        self.play(counter.animate.set_color(LIGHT_BLUE), run_time=0.35)
        self.play(counter.animate.set_color(WHITE), run_time=0.35)
        self.play(counter.animate.set_color(LIGHT_BLUE), run_time=0.35)

        # Checkmark (GREEN) sealing the final correct strand
        check = VGroup(
            Line(LEFT * 0.25 + DOWN * 0.0, DOWN * 0.3, color=GREEN, stroke_width=6),
            Line(DOWN * 0.3, RIGHT * 0.45 + UP * 0.25, color=GREEN, stroke_width=6),
        )
        check.move_to(self.grid["E5"])

        self.play(Create(check), run_time=0.6)

        # Small glow ring around checkmark
        glow = Circle(radius=0.5, color=GREEN, stroke_width=2, stroke_opacity=0.5)
        glow.move_to(check.get_center())
        self.play(FadeIn(glow, scale=1.5), run_time=0.4)
        self.play(glow.animate.scale(1.4).set_opacity(0.0), run_time=0.6)

        # Add a quick highlight around the final correct base (green)
        final_ring = Circle(radius=0.35, color=GREEN, stroke_width=3)
        final_ring.move_to(correct_base.get_center())
        self.play(Create(final_ring), run_time=0.4)
        self.play(final_ring.animate.set_opacity(0.0), run_time=0.5)
        self.remove(final_ring)

        # Final pause
        self.wait(1.0)
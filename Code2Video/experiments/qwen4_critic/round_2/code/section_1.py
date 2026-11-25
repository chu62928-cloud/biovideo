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

# Helper Mobjects (Icons) --------------------------------------------------

class LightningBolt(VGroup):
    def __init__(self, color=YELLOW, **kwargs):
        super().__init__(**kwargs)
        bolt = Polygon(
            [-0.3, 0.5, 0], [0.1, 0.1, 0], [-0.1, 0.1, 0], [0.3, -0.5, 0],
            [0.0, -0.1, 0], [0.2, -0.1, 0], color=color, fill_opacity=0.9,
            stroke_width=2
        )
        self.add(bolt)


class ShieldIcon(VGroup):
    def __init__(self, color=TEAL, **kwargs):
        super().__init__(**kwargs)
        shield = Polygon(
            [-0.35, 0.5, 0], [0.35, 0.5, 0], [0.35, -0.1, 0], [0.0, -0.5, 0],
            [-0.35, -0.1, 0], color=color, fill_opacity=0.9, stroke_width=2
        )
        check = Polygon(
            [-0.15, 0.05, 0], [-0.05, -0.05, 0], [0.2, 0.2, 0],
            color=WHITE, stroke_width=4
        )
        self.add(shield, check)


class BookIcon(VGroup):
    def __init__(self, color=ORANGE, **kwargs):
        super().__init__(**kwargs)
        cover = Rectangle(width=0.6, height=0.8, color=color, fill_opacity=0.9)
        spine = Line(UP*0.4, DOWN*0.4, color=WHITE, stroke_width=2).shift(LEFT*0.3)
        lines = VGroup(*[
            Line(LEFT*0.2, RIGHT*0.2, color=WHITE, stroke_width=1.5)
            .shift(UP*(0.2 - i*0.15) + RIGHT*0.05)
            for i in range(3)
        ])
        self.add(cover, spine, lines)


class CopyMachineIcon(VGroup):
    def __init__(self, color=GREEN, **kwargs):
        super().__init__(**kwargs)
        body = RoundedRectangle(width=0.9, height=0.5, corner_radius=0.08,
                                color=color, fill_opacity=0.9).shift(DOWN*0.1)
        top = Rectangle(width=0.7, height=0.15, color=color,
                        fill_opacity=0.9).shift(UP*0.2)
        slot = Line(LEFT*0.3, RIGHT*0.3, color=WHITE, stroke_width=3).shift(DOWN*0.25)
        self.add(body, top, slot)


class DNAHelix(VGroup):
    """A stylized double helix made from two sine-wave strands and rungs."""

    def __init__(self, color=BLUE, height=2.6, **kwargs):
        super().__init__(**kwargs)
        self.color = color
        self.helix_height = height

        def strand(phase):
            pts = []
            n = 40
            for i in range(n + 1):
                t = i / n
                y = height / 2 - t * height
                x = 0.28 * np.sin(2 * np.pi * t * 1.4 + phase)
                pts.append([x, y, 0])
            return VMobject().set_points_smoothly(pts).set_stroke(color, width=4)

        self.strand_a = strand(0)
        self.strand_b = strand(np.pi)
        self.rungs = VGroup()
        n_rungs = 9
        for i in range(1, n_rungs):
            t = i / n_rungs
            y = height / 2 - t * height
            xa = 0.28 * np.sin(2 * np.pi * t * 1.4)
            xb = 0.28 * np.sin(2 * np.pi * t * 1.4 + np.pi)
            rung = Line([xa, y, 0], [xb, y, 0], color=color, stroke_width=2)
            rung.set_opacity(0.8)
            self.rungs.add(rung)

        self.add(self.strand_a, self.strand_b, self.rungs)


class Section1Scene(TeachingScene):
    def construct(self):
        self.setup_layout(
            "Sec 1: Introduction: The Need for Speed and Accuracy",
            [
                'DNA replication is essential before cell division.',
                '3 billion base pairs must be copied faithfully.',
                'Imagine a library copying 3 billion books.',
                'Speed and accuracy must work together.',
                'The result: two identical DNA copies.'
            ]
        )

        # Pre-declare persistent objects we will reuse/hook across steps
        cell_group = VGroup()
        helix = None  # will be a DNAHelix (or VGroup of two)

        # ============================================================
        # === Animation for Lecture Line 1 ===
        # ============================================================
        self.lecture[0].set_color(YELLOW)

        # Large white cell circle at center-right (area C3-E5)
        cell_circle = Circle(radius=1.55, color=WHITE, fill_color="#E8F1FF",
                             fill_opacity=0.15, stroke_width=3)
        self.place_in_area(cell_circle, 'C3', 'E5', scale_factor=1.0)

        # Glowing double helix inside the cell
        helix = DNAHelix(color="#4FC3F7", height=2.4)
        self.place_at_grid(helix, 'D4', scale_factor=0.85)

        # Cell division label above (area B3-C5 -> top of cell)
        label_cd = Text("Cell Division", font_size=24, color="#FFD54F")
        self.place_at_grid(label_cd, 'B4', scale_factor=0.8)

        self.play(FadeIn(cell_circle, scale=0.9), run_time=1.0)
        self.play(Create(helix), run_time=1.2)
        self.play(Write(label_cd), run_time=0.8)

        cell_group = VGroup(cell_circle, helix, label_cd)

        # Slow rotation of the helix (visible, gentle)
        self.play(
            Rotate(helix, angle=PI / 3, about_point=helix.get_center()),
            run_time=1.5,
            rate_func=smooth
        )

        self.wait(0.5)

        # ============================================================
        # === Animation for Lecture Line 2 ===
        # ============================================================
        self.lecture[1].set_color("#FF7043")

        # Zoom into the DNA helix: create a magnified highlight ring
        zoom_ring = Circle(radius=0.9, color="#FF7043", stroke_width=3)
        self.place_at_grid(zoom_ring, 'D4', scale_factor=1.0)
        self.play(Create(zoom_ring), run_time=0.6)

        # Big number text: 3,000,000,000 bp
        bp_text = Text("3,000,000,000 bp", font_size=32, color="#FF7043")
        self.place_in_area(bp_text, 'B6', 'D6', scale_factor=0.55)
        # Small counter beside it; put it just below the bp text (still within 1 unit)
        counter = Integer(0, font_size=22, color="#FF7043")
        self.place_at_grid(counter, 'E6', scale_factor=0.8)

        # Flash in the bp text
        self.play(FadeIn(bp_text, scale=1.2), run_time=0.5)
        self.play(bp_text.animate(scale=1.05), run_time=0.2)
        self.play(bp_text.animate(scale=1.0), run_time=0.2)

        # Rapid counter tick
        self.play(
            counter.animate.set_value(3000),
            run_time=1.8,
            rate_func=linear
        )

        # Keep these visible briefly, then clean up (fade zoom/numbers)
        self.wait(0.3)
        self.play(
            FadeOut(zoom_ring),
            FadeOut(bp_text),
            FadeOut(counter),
            run_time=0.6
        )

        # ============================================================
        # === Animation for Lecture Line 3 ===
        # ============================================================
        self.lecture[2].set_color("#FFB74D")

        # Fade out the cell scene elements to make room for the library
        self.play(FadeOut(cell_group), run_time=1.0)

        # -- Library of books on the left of the right-side area --
        # We'll build a 4x4 grid of book icons within area B2-E5
        book_color = "#FFB74D"
        books = VGroup()
        rows, cols = 4, 4
        for r in range(rows):
            for c in range(cols):
                b = BookIcon(color=book_color)
                b.scale(0.35)
                x = -0.45 * 3 + c * 0.45
                y = 0.45 * 1.5 - r * 0.5
                b.move_to(np.array([x, y, 0]))
                books.add(b)

        # Anchor the whole book grid to the left portion of the right area.
        # Place the grid center at B2-D4, then shift it left.
        self.place_in_area(books, 'B2', 'C4', scale_factor=0.9)
        books.shift(LEFT * 1.6)

        # Copy machine on the right (area D5-E6)
        copier = CopyMachineIcon(color="#81C784")
        self.place_at_grid(copier, 'D5', scale_factor=1.0)

        # Label "Copy All Books" above the copier (area B5-C5)
        copy_label = Text("Copy All Books", font_size=22, color="#B3E5FC")
        self.place_at_grid(copy_label, 'D4', scale_factor=0.8)

        # Animate: books multiply in (create a couple at a time), copier appears
        book_subset_1 = books[:8]
        book_subset_2 = books[8:]

        self.play(
            LaggedStart(*[FadeIn(b, scale=0.5) for b in book_subset_1],
                        lag_ratio=0.05),
            run_time=1.2
        )
        self.play(FadeIn(copier, scale=0.8), run_time=0.6)
        self.play(
            LaggedStart(*[FadeIn(b, scale=0.5) for b in book_subset_2],
                        lag_ratio=0.05),
            run_time=1.0
        )
        self.play(Write(copy_label), run_time=0.6)

        library_group = VGroup(books, copier, copy_label)

        self.wait(0.5)

        # ============================================================
        # === Animation for Lecture Line 4 ===
        # ============================================================
        self.lecture[3].set_color("#FFEB3B")

        # Fade out library group to make way for speed vs accuracy
        self.play(FadeOut(library_group), run_time=0.8)

        # Lightning bolt icon "Speed"  (left of center)
        bolt = LightningBolt(color="#FFEB3B")
        self.place_at_grid(bolt, 'C4', scale_factor=1.0)
        speed_label = Text("Speed", font_size=24, color="#FFEB3B")
        self.place_at_grid(speed_label, 'B4', scale_factor=0.85)

        # Shield icon "Accuracy" (right of center)
        shield = ShieldIcon(color="#4DD0E1")
        self.place_at_grid(shield, 'C5', scale_factor=1.0)
        acc_label = Text("Accuracy", font_size=24, color="#4DD0E1")
        self.place_in_area(acc_label, 'B5', 'B6', scale_factor=0.7)

        # Arrows underneath each pointing up toward the icons
        arrow_speed = Arrow(
            start=DOWN * 0.6, end=UP * 0.3, color="#FFEB3B",
            stroke_width=5, buff=0.1
        ).next_to(bolt, DOWN, buff=0.25)
        arrow_acc = Arrow(
            start=DOWN * 0.6, end=UP * 0.3, color="#4DD0E1",
            stroke_width=5, buff=0.1
        ).next_to(shield, DOWN, buff=0.25)

        self.play(
            FadeIn(bolt),
            FadeIn(speed_label),
            GrowArrow(arrow_speed),
            run_time=0.8
        )
        self.play(
            FadeIn(shield),
            FadeIn(acc_label),
            GrowArrow(arrow_acc),
            run_time=0.8
        )

        # Pulse alternately to show balance (2 pulses each)
        for _ in range(2):
            self.play(
                bolt.animate.scale(1.15).set_color("#FFF59D"),
                speed_label.animate.set_color("#FFF59D"),
                run_time=0.35
            )
            self.play(
                bolt.animate.scale(1/1.15).set_color("#FFEB3B"),
                speed_label.animate.set_color("#FFEB3B"),
                run_time=0.35
            )
            self.play(
                shield.animate.scale(1.15).set_color("#80DEEA"),
                acc_label.animate.set_color("#80DEEA"),
                run_time=0.35
            )
            self.play(
                shield.animate.scale(1/1.15).set_color("#4DD0E1"),
                acc_label.animate.set_color("#4DD0E1"),
                run_time=0.35
            )

        balance_group = VGroup(bolt, speed_label, shield, acc_label,
                               arrow_speed, arrow_acc)

        self.wait(0.3)

        # ============================================================
        # === Animation for Lecture Line 5 ===
        # ============================================================
        self.lecture[4].set_color("#A5D6A7")

        # Fade out balance group
        self.play(FadeOut(balance_group), run_time=0.8)

        # Two identical helices: start from one and split them
        helix_final = DNAHelix(color="#4FC3F7", height=2.4)
        self.place_at_grid(helix_final, 'D4', scale_factor=0.85)

        # create a second copy at the same spot
        helix_copy = helix_final.copy()
        helix_copy.move_to(helix_final.get_center())

        self.play(FadeIn(helix_final), run_time=0.8)
        self.play(FadeIn(helix_copy), run_time=0.4)

        # Drift apart symmetrically
        left_pos = self.grid['B3']
        right_pos = self.grid['C6']
        # Compute symmetric offsets around center
        center = (left_pos + right_pos) / 2
        offset = (right_pos - left_pos) / 2

        self.play(
            helix_final.animate.move_to(center - offset * 0.55),
            helix_copy.animate.move_to(center + offset * 0.55),
            run_time=2.0,
            rate_func=smooth
        )

        # Label "2 Identical Copies" below them
        copies_label = Text("2 Identical Copies", font_size=26, color="#A5D6A7")
        self.place_at_grid(copies_label, 'E4', scale_factor=0.9)

        self.play(FadeIn(copies_label, shift=UP * 0.2), run_time=1.0)

        # Gentle final pulse on label
        self.play(copies_label.animate.set_color("#C8E6C9"), run_time=0.4)
        self.play(copies_label.animate.set_color("#A5D6A7"), run_time=0.4)

        self.wait(1.5)
        self.play(
            FadeOut(helix_final),
            FadeOut(helix_copy),
            FadeOut(copies_label),
            run_time=1.0
        )
        self.wait(0.3)
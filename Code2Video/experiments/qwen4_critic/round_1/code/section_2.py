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

class Section2Scene(TeachingScene):
    def construct(self):
        self.setup_layout(
            "Sec 2: Origin Recognition and Licensing",
            [
                'Origins of replication are starting sites.',
                'ORC recognizes and binds each origin.',
                'Licensing allows each origin to fire once.',
                'Multiple origins light up along DNA.',
            ],
        )

        colors = ["#4FC3F7", "#FFD54F", "#FF8A65", "#BA68C8"]
        # Lecture line color mapping for highlight
        line_colors = ["#4FC3F7", "#FFD54F", "#BA68C8", "#FFAB91"]

        # === Animation for Lecture Line 1 ===
        # DNA strand across grid B1..B6 area (centered vertically around B row)
        dna_y = self.grid["B1"][1]
        dna_y = (self.grid["B1"][1] + self.grid["C1"][1]) / 2  # between B and C

        left_x = self.grid["A1"][0] + 0.1
        right_x = self.grid["F6"][0] + 0.3

        # Two rails for DNA look
        dna_top = Line(
            np.array([left_x, dna_y + 0.12, 0]),
            np.array([right_x, dna_y + 0.12, 0]),
            color="#4FC3F7",
            stroke_width=5,
        )
        dna_bottom = Line(
            np.array([left_x, dna_y - 0.12, 0]),
            np.array([right_x, dna_y - 0.12, 0]),
            color="#4FC3F7",
            stroke_width=5,
        )
        # Rungs (short connectors)
        rungs = VGroup()
        n_rungs = 28
        for k in range(n_rungs):
            x = left_x + (right_x - left_x) * (k + 0.5) / n_rungs
            rungs.add(
                Line(
                    np.array([x, dna_y + 0.12, 0]),
                    np.array([x, dna_y - 0.12, 0]),
                    color="#4FC3F7",
                    stroke_width=1.5,
                    stroke_opacity=0.6,
                )
            )
        dna = VGroup(dna_top, dna_bottom, rungs)

        self.play(Create(dna), run_time=1.5)

        # ORI positions along DNA (5 origins)
        ori_xs = [
            self.grid["B1"][0] + 0.15,
            (self.grid["B1"][0] + self.grid["C3"][0]) / 2 + 0.2,
            (self.grid["B3"][0] + self.grid["C4"][0]) / 2,
            (self.grid["C5"][0] + self.grid["B5"][0]) / 2,
            self.grid["B6"][0] - 0.15,
        ]

        ori_glows = VGroup()
        ori_dots = VGroup()
        ori_labels = VGroup()
        for x in ori_xs:
            dot = Dot(point=np.array([x, dna_y, 0]), radius=0.09, color="#FFD54F")
            glow = Dot(point=np.array([x, dna_y, 0]), radius=0.20, color="#FFD54F")
            glow.set_opacity(0.25)
            label = Text("ORI", font_size=18, color="#FFD54F")
            label.next_to(dot, UP, buff=0.25)
            ori_dots.add(dot)
            ori_glows.add(glow)
            ori_labels.add(label)

        self.play(
            LaggedStart(
                *[FadeIn(g) for g in ori_glows],
                *[GrowFromCenter(d) for d in ori_dots],
                lag_ratio=0.15,
            ),
            run_time=1.5,
        )
        self.play(
            LaggedStart(*[FadeIn(l) for l in ori_labels], lag_ratio=0.1),
            run_time=0.8,
        )
        # Highlight lecture line 1
        self.play(self.lecture[0].animate.set_color(line_colors[0]), run_time=0.5)

        # === Animation for Lecture Line 2 ===
        self.play(self.lecture[1].animate.set_color(line_colors[1]), run_time=0.5)

        # ORC ring proteins that slide to each ORI
        orcs = VGroup()
        orc_labels = VGroup()
        for i, x in enumerate(ori_xs):
            ring = Circle(radius=0.22, color="#FF8A65", stroke_width=4)
            ring.move_to(np.array([x, dna_y, 0]))
            # small hole adjust: draw as ring via two circles? Keep simple circle outline
            orcs.add(ring)
            lab = Text("ORC", font_size=16, color="#FF8A65")
            lab.next_to(ring, DOWN, buff=0.22)
            orc_labels.add(lab)

        # Start ORCs from left off-strand and slide into position
        start_offsets = [-0.6 + i * 0.15 for i in range(len(ori_xs))]
        for i, ring in enumerate(orcs):
            ring.move_to(np.array([self.grid["A1"][0] - 1.0, dna_y + 0.9, 0]))
            orc_labels[i].move_to(np.array([self.grid["A1"][0] - 1.0, dna_y + 0.55, 0]))

        self.play(
            LaggedStart(*[FadeIn(r) for r in orcs], lag_ratio=0.1),
            *[FadeIn(l) for l in orc_labels],
            run_time=0.8,
        )

        # Slide each ORC to its ORI
        anims = []
        for i, (ring, lab) in enumerate(zip(orcs, orc_labels)):
            target = np.array([ori_xs[i], dna_y, 0])
            target_lab = target + np.array([0, -0.45, 0])
            anims.append(ring.animate.move_to(target))
            anims.append(lab.animate.move_to(target_lab))
        self.play(*anims, run_time=1.8)

        # Flash ORI spots white when bound
        flashes = VGroup()
        for x in ori_xs:
            f = Dot(point=np.array([x, dna_y, 0]), radius=0.30, color="#FFFFFF")
            f.set_opacity(0.0)
            flashes.add(f)
        self.add(flashes)
        self.play(
            *[f.animate.set_opacity(0.6) for f in flashes],
            run_time=0.4,
        )
        self.play(
            *[f.animate.set_opacity(0.0) for f in flashes],
            run_time=0.4,
        )

        # === Animation for Lecture Line 3 ===
        self.play(self.lecture[2].animate.set_color(line_colors[2]), run_time=0.5)

        # Small key icons labeled "License" insert into each ORC
        keys = VGroup()
        key_labels = VGroup()
        checks = VGroup()
        counters = VGroup()

        for i, (x, ring) in enumerate(zip(ori_xs, orcs)):
            # key: stem + head
            stem = Line(ORIGIN, UP * 0.25, color="#BA68C8", stroke_width=4)
            teeth = VGroup(
                Line(UP * 0.25, UP * 0.25 + RIGHT * 0.08, color="#BA68C8", stroke_width=3),
                Line(UP * 0.15, UP * 0.15 + RIGHT * 0.08, color="#BA68C8", stroke_width=3),
            )
            head = Circle(radius=0.08, color="#BA68C8", stroke_width=3).move_to(UP * 0.32)
            key = VGroup(stem, teeth, head)
            key.move_to(np.array([x, dna_y + 0.9, 0]))
            keys.add(key)

            klab = Text("License", font_size=12, color="#BA68C8")
            klab.next_to(key, RIGHT, buff=0.08)
            key_labels.add(klab)

            check = Text("✓", font_size=26, color="#69F0AE")
            check.next_to(ring, UP, buff=0.32)
            checks.add(check)

            counter = Text("1x per cycle", font_size=12, color="#B3E5FC")
            counter.next_to(ring, DOWN, buff=0.55)
            counters.add(counter)

        self.play(
            LaggedStart(*[FadeIn(k) for k in keys], lag_ratio=0.1),
            *[FadeIn(l) for l in key_labels],
            run_time=0.9,
        )

        # Insert keys into ORCs (move down to strand)
        anims = []
        for i, (key, klab, ring) in enumerate(zip(keys, key_labels, orcs)):
            target = np.array([ori_xs[i], dna_y + 0.22, 0])
            anims.append(key.animate.move_to(target))
            anims.append(klab.animate.move_to(target + np.array([0.55, 0.05, 0])))
        self.play(*anims, run_time=1.2)

        # Fade out keys/labels as they "insert"
        self.play(
            *[FadeOut(k) for k in keys],
            *[FadeOut(l) for l in key_labels],
            run_time=0.5,
        )

        # Checkmarks and counters
        self.play(
            LaggedStart(*[GrowFromCenter(c) for c in checks], lag_ratio=0.1),
            run_time=0.8,
        )
        self.play(
            LaggedStart(*[FadeIn(c) for c in counters], lag_ratio=0.1),
            run_time=0.8,
        )

        # === Animation for Lecture Line 4 ===
        self.play(self.lecture[3].animate.set_color(line_colors[3]), run_time=0.5)

        # "Multiple Firing Sites" label above the strand
        multi_label = Text("Multiple Firing Sites", font_size=24, color="#FFAB91")
        multi_label.move_to(np.array([(left_x + right_x) / 2, dna_y + 1.7, 0]))
        self.play(Write(multi_label), run_time=1.0)

        # Synchronized wave pulse along DNA: ori dots pulse outward
        waves = VGroup()
        for x in ori_xs:
            w = Circle(radius=0.15, color="#FFFFFF", stroke_width=3)
            w.move_to(np.array([x, dna_y, 0]))
            w.set_opacity(0.9)
            waves.add(w)
        self.add(waves)
        self.play(
            *[w.animate.scale(4.0).set_opacity(0.0) for w in waves],
            run_time=1.6,
            rate_func=rush_from,
        )

        # Final synchronized ORI pulse
        self.play(
            *[g.animate.set_opacity(0.55) for g in ori_glows],
            run_time=0.4,
        )
        self.play(
            *[g.animate.set_opacity(0.25) for g in ori_glows],
            run_time=0.6,
        )

        self.wait(1.5)
from manim import *
import numpy as np
from biology_runtime import BiologyScene


class Section4Scene(BiologyScene):
    def construct(self):
        # Colors
        C_TEMPLATE = "#4FC3F7"
        C_NEW = "#69F0AE"
        C_RNA = "#FFB74D"
        C_PRIMASE = "#BA68C8"
        C_POL = "#4DD0E1"
        C_LIGASE = "#FFD54F"

        # Title (font 22) at top
        title = Text("DNA Replication in Eukaryotic Cells", font_size=22, weight=BOLD)
        title.move_to(np.array([0, 3.25, 0]))
        self.add(title)

        # Caption (font 20) at bottom
        caption = Text("One fork, two antiparallel templates", font_size=20)
        caption.move_to(np.array([0, -3.2, 0]))
        self.add(caption)

        # ------------------------------------------------------------------
        # Geometry layout
        # ------------------------------------------------------------------
        fork_x = 0.5          # fork junction x
        x_left = -5.6         # left end of opened templates
        x_right = 5.8         # right end of parental duplex
        y_upper = 1.4         # upper template y
        y_lower = -1.4        # lower template y
        y_lead_new = y_upper - 0.55   # new leading strand y (below upper template)
        y_lag_new = y_lower + 0.55    # new lagging strand y (above lower template)

        # ------------------------------------------------------------------
        # EVENT 1: replication fork + parental duplex
        # ------------------------------------------------------------------
        self.mark_event("event_1_fork")

        # Parental duplex (right of fork)
        parent_top = Line(np.array([fork_x, 0.12, 0]),
                          np.array([x_right, 0.12, 0]),
                          color=C_TEMPLATE, stroke_width=5)
        parent_bot = Line(np.array([fork_x, -0.12, 0]),
                          np.array([x_right, -0.12, 0]),
                          color=C_TEMPLATE, stroke_width=5)
        fork_junction = Line(np.array([fork_x, -0.12, 0]),
                             np.array([fork_x, 0.12, 0]),
                             color=C_TEMPLATE, stroke_width=5)
        # Upper template: 3' left -> 5' right
        upper_template = Line(np.array([fork_x, 0.12, 0]),
                              np.array([x_left, y_upper, 0]),
                              color=C_TEMPLATE, stroke_width=5)
        # Lower template: 5' left -> 3' right
        lower_template = Line(np.array([fork_x, -0.12, 0]),
                              np.array([x_left, y_lower, 0]),
                              color=C_TEMPLATE, stroke_width=5)

        fork_group = VGroup(parent_top, parent_bot, fork_junction,
                            upper_template, lower_template)
        self.register_object("replication_fork", fork_group, role="structure")
        self.register_object("template_leading", upper_template, role="template")
        self.register_object("template_lagging", lower_template, role="template")

        self.play(Create(fork_group), run_time=1.2)

        # Polarity labels (small, font 16) - only endpoints
        t3 = Text("3'", font_size=16).move_to(np.array([x_left - 0.25, y_upper + 0.22, 0]))
        t5 = Text("5'", font_size=16).move_to(np.array([fork_x + 0.05, y_upper + 0.28, 0]))
        b5 = Text("5'", font_size=16).move_to(np.array([x_left - 0.25, y_lower - 0.22, 0]))
        b3 = Text("3'", font_size=16).move_to(np.array([fork_x + 0.05, y_lower - 0.30, 0]))
        self.play(FadeIn(t3), FadeIn(t5), FadeIn(b5), FadeIn(b3), run_time=0.5)
        self.wait(1.0)
        # Total so far: 1.2 + 0.5 + 1.0 = 2.7s

        # ------------------------------------------------------------------
        # EVENT 2: Priming (leading primer)
        # ------------------------------------------------------------------
        self.mark_event("event_2_priming")
        cap2 = Text("Primase makes an RNA starting point", font_size=20)
        cap2.move_to(np.array([0, -3.2, 0]))
        self.play(Transform(caption, cap2), run_time=0.4)

        # Primase enzyme (purple pentagon) at the priming site
        primase_shape = RegularPolygon(n=5, start_angle=PI / 2, color=C_PRIMASE,
                                       fill_opacity=0.85)
        primase_shape.scale(0.22)
        primase_shape.move_to(np.array([-1.6, y_lead_new + 0.45, 0]))
        primase_label = Text("Primase", font_size=16, color=C_PRIMASE)
        primase_label.next_to(primase_shape, UP, buff=0.06)
        primase_group = VGroup(primase_shape, primase_label)
        self.register_object("primase", primase_group, role="enzyme")
        self.play(FadeIn(primase_group), run_time=0.35)

        # RNA primer as individual orange segments on leading strand
        primer_children = []
        n_primer = 4
        lead_primer_start_x = -1.55
        lead_primer_end_x = -0.75
        p_xs = np.linspace(lead_primer_start_x, lead_primer_end_x, n_primer)
        for i, x in enumerate(p_xs):
            seg = Line(np.array([x, y_lead_new - 0.07, 0]),
                       np.array([x, y_lead_new + 0.07, 0]),
                       color=C_RNA, stroke_width=6)
            pid = f"rna_primer_leading_{i + 1:02d}"
            self.register_object(pid, seg, role="nucleotide",
                                 strand="leading", material="RNA")
            primer_children.append(seg)
            self.play(Create(seg), run_time=0.15)
        # Group as the required rna_primer
        rna_primer_group = VGroup(*primer_children)
        self.register_object("rna_primer", rna_primer_group, role="primer")

        # Exposed 3' end marker on primer
        prim3 = Text("3'", font_size=16, color=C_RNA).move_to(
            np.array([lead_primer_end_x + 0.2, y_lead_new - 0.22, 0]))
        self.play(FadeIn(prim3), run_time=0.2)
        self.play(FadeOut(primase_group), run_time=0.3)
        self.wait(1.2)
        # event 2 elapsed: 0.4 + 0.35 + 4*0.15 + 0.2 + 0.3 + 1.2 ≈ 3.05 -> total ~5.75s
        # target 8s -> wait extra
        self.wait(2.0)
        # Total ~ 8s

        # ------------------------------------------------------------------
        # EVENT 3: Leading extension by DNA polymerase
        # ------------------------------------------------------------------
        self.mark_event("event_3_extension")
        cap3 = Text("DNA polymerase extends 5' to 3'", font_size=20)
        cap3.move_to(np.array([0, -3.2, 0]))
        self.play(Transform(caption, cap3), run_time=0.4)

        # Register new_leading_strand group first (empty, children added in)
        new_leading_group = VGroup()
        self.register_object("new_leading_strand", new_leading_group,
                             role="nascent_strand")

        # DNA polymerase leading (cyan rounded square)
        pol_body = RoundedRectangle(corner_radius=0.08, color=C_POL,
                                    fill_opacity=0.85, width=0.32, height=0.32)
        pol_label = Text("Pol", font_size=16, color=C_POL)
        pol_label.move_to(pol_body.get_center())
        pol_lead = VGroup(pol_body, pol_label)
        pol_lead.move_to(np.array([lead_primer_end_x + 0.35, y_lead_new + 0.42, 0]))
        self.register_object("dna_polymerase_leading", pol_lead, role="enzyme")
        self.play(FadeIn(pol_lead), run_time=0.35)

        # Active-site anchor for leading polymerase
        lead_anchor = Dot(radius=0.02, color=WHITE)
        lead_anchor.move_to(np.array([lead_primer_end_x + 0.05, y_lead_new, 0]))
        self.register_object("lead_active_anchor", lead_anchor, role="anchor")
        self.add(lead_anchor)
        self.bind_near("dna_polymerase_leading", "lead_active_anchor",
                       offset=(0.0, 0.42, 0.0), max_distance=0.8)

        # Add green DNA nucleotides rightward along upper template
        lead_dna_xs = np.arange(lead_primer_end_x + 0.28, 2.2, 0.30)
        for i, x in enumerate(lead_dna_xs):
            seg = Line(np.array([x, y_lead_new - 0.07, 0]),
                       np.array([x, y_lead_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_leading_{i + 1:02d}"
            self.register_object(nid, seg, role="nucleotide",
                                 strand="leading", fragment="leading",
                                 material="DNA")
            new_leading_group.add(seg)
            new_anchor_pos = np.array([x + 0.10, y_lead_new, 0])
            self.play(
                lead_anchor.animate.move_to(new_anchor_pos),
                Create(seg),
                run_time=0.18
            )
        lead3 = Text("3'", font_size=16, color=C_NEW).move_to(
            np.array([lead_dna_xs[-1] + 0.30, y_lead_new - 0.22, 0]))
        self.play(FadeIn(lead3), run_time=0.2)
        self.wait(1.0)
        # event 3 elapsed: 0.4 + 0.35 + 8*0.18 + 0.2 + 1.0 ≈ 3.59
        # total ~ 11.6 -> need ~16s at end of event 3? Storyboard says 8-16s.
        # We'll continue leading synthesis in event 4 anyway, so fine.

        # ------------------------------------------------------------------
        # EVENT 4: Two modes - continuous leading, lagging fragments
        # ------------------------------------------------------------------
        self.mark_event("event_4_two_modes")
        cap4 = Text("Continuous leading; short lagging fragments", font_size=20)
        cap4.move_to(np.array([0, -3.2, 0]))
        self.play(Transform(caption, cap4), run_time=0.4)

        # Continue leading synthesis toward fork
        more_lead_xs = np.arange(lead_dna_xs[-1] + 0.30, 3.3, 0.28)
        for i, x in enumerate(more_lead_xs):
            seg = Line(np.array([x, y_lead_new - 0.07, 0]),
                       np.array([x, y_lead_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_leading_{len(lead_dna_xs) + i + 1:02d}"
            self.register_object(nid, seg, role="nucleotide",
                                 strand="leading", fragment="leading",
                                 material="DNA")
            new_leading_group.add(seg)
            self.play(lead_anchor.animate.move_to(np.array([x + 0.10, y_lead_new, 0])),
                      Create(seg), run_time=0.12)

        # Register new_lagging_strand TOP-LEVEL group (empty placeholder)
        new_lagging_group = VGroup()
        self.register_object("new_lagging_strand", new_lagging_group,
                             role="nascent_strand")

        # Register incoming_nucleotide (representative, will be used in event 4)
        incoming_nuc = Line(np.array([0.0, 0.0, 0]),
                            np.array([0.0, 0.14, 0]),
                            color=C_NEW, stroke_width=6)
        incoming_nuc.move_to(np.array([2.5, y_lag_new + 1.0, 0]))
        self.register_object("incoming_nucleotide", incoming_nuc, role="nucleotide",
                             strand="lagging", material="DNA")

        # -------- Lagging fragment 1 (far from fork, right side) --------
        lag_primer1_right_x = 2.4
        lag_prim1_parts = []
        p1_xs = np.linspace(lag_primer1_right_x - 0.45, lag_primer1_right_x, 3)
        for i, x in enumerate(p1_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_RNA, stroke_width=6)
            pid = f"rna_primer_lagging_1_{i + 1:02d}"
            self.register_object(pid, seg, role="nucleotide",
                                 strand="lagging", fragment="lagging_1",
                                 material="RNA")
            lag_prim1_parts.append(seg)
        rna_primer_lagging_1 = VGroup(*lag_prim1_parts)
        self.register_object("rna_primer_lagging_1", rna_primer_lagging_1, role="primer")

        # Primase visits fragment 1 primer site
        primase_lag1 = primase_group.copy()
        primase_lag1.move_to(np.array([lag_primer1_right_x, y_lag_new + 0.45, 0]))
        self.play(FadeIn(primase_lag1), run_time=0.2)
        self.play(Create(rna_primer_lagging_1), run_time=0.4)
        self.play(FadeOut(primase_lag1), run_time=0.2)

        # Okazaki fragment 1 group
        okazaki_fragment = VGroup()
        self.register_object("okazaki_fragment", okazaki_fragment, role="DNA_fragment")

        # Lagging polymerase 1 active site (grows left)
        lag_anchor1 = Dot(radius=0.02, color=WHITE)
        lag_anchor1.move_to(np.array([p1_xs[0] - 0.05, y_lag_new, 0]))
        self.register_object("lag_active_anchor_1", lag_anchor1, role="anchor")
        self.add(lag_anchor1)
        pol_lag1 = VGroup(pol_body.copy(), pol_label.copy())
        pol_lag1.move_to(np.array([p1_xs[0] - 0.30, y_lag_new + 0.42, 0]))
        self.register_object("dna_polymerase_lagging", pol_lag1, role="enzyme")
        self.bind_near("dna_polymerase_lagging", "lag_active_anchor_1",
                       offset=(0.0, 0.42, 0.0), max_distance=0.8)
        self.play(FadeIn(pol_lag1), run_time=0.3)

        # Grow leftward
        lag1_dna_xs = np.arange(p1_xs[0] - 0.30, 0.5, -0.28)
        for i, x in enumerate(lag1_dna_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_lagging_1_{i + 1:02d}"
            self.register_object(nid, seg, role="nucleotide",
                                 strand="lagging", fragment="lagging_1",
                                 material="DNA")
            okazaki_fragment.add(seg)
            new_lagging_group.add(seg)
            self.play(
                lag_anchor1.animate.move_to(np.array([x - 0.10, y_lag_new, 0])),
                Create(seg),
                run_time=0.15
            )
        lag1_3p = Text("3'", font_size=16, color=C_NEW).move_to(
            np.array([lag1_dna_xs[-1] - 0.30, y_lag_new - 0.22, 0]))
        self.play(FadeIn(lag1_3p), run_time=0.2)

        # -------- Lagging fragment 2 (nearer the fork) --------
        lag_primer2_right_x = 3.5
        lag_prim2_parts = []
        p2_xs = np.linspace(lag_primer2_right_x - 0.40, lag_primer2_right_x, 3)
        for i, x in enumerate(p2_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_RNA, stroke_width=6)
            pid = f"rna_primer_lagging_2_{i + 1:02d}"
            self.register_object(pid, seg, role="nucleotide",
                                 strand="lagging", fragment="lagging_2",
                                 material="RNA")
            lag_prim2_parts.append(seg)
        rna_primer_lagging_2 = VGroup(*lag_prim2_parts)
        self.register_object("rna_primer_lagging_2", rna_primer_lagging_2, role="primer")

        primase_lag2 = primase_group.copy()
        primase_lag2.move_to(np.array([lag_primer2_right_x, y_lag_new + 0.45, 0]))
        self.play(FadeIn(primase_lag2), run_time=0.2)
        self.play(Create(rna_primer_lagging_2), run_time=0.4)
        self.play(FadeOut(primase_lag2), run_time=0.2)

        okazaki_fragment_2 = VGroup()
        self.register_object("okazaki_fragment_2", okazaki_fragment_2,
                             role="DNA_fragment")

        lag_anchor2 = Dot(radius=0.02, color=WHITE)
        lag_anchor2.move_to(np.array([p2_xs[0] - 0.05, y_lag_new, 0]))
        self.register_object("lag_active_anchor_2", lag_anchor2, role="anchor")
        self.add(lag_anchor2)
        pol_lag2 = VGroup(pol_body.copy(), pol_label.copy())
        pol_lag2.move_to(np.array([p2_xs[0] - 0.30, y_lag_new + 0.42, 0]))
        self.bind_near("dna_polymerase_lagging", "lag_active_anchor_2",
                       offset=(0.0, 0.42, 0.0), max_distance=0.8)
        self.play(FadeIn(pol_lag2), run_time=0.3)

        lag2_dna_xs = np.arange(p2_xs[0] - 0.30, 2.45, -0.28)
        for i, x in enumerate(lag2_dna_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_lagging_2_{i + 1:02d}"
            self.register_object(nid, seg, role="nucleotide",
                                 strand="lagging", fragment="lagging_2",
                                 material="DNA")
            okazaki_fragment_2.add(seg)
            new_lagging_group.add(seg)
            self.play(
                lag_anchor2.animate.move_to(np.array([x - 0.10, y_lag_new, 0])),
                Create(seg),
                run_time=0.15
            )
        lag2_3p = Text("3'", font_size=16, color=C_NEW).move_to(
            np.array([lag2_dna_xs[-1] - 0.30, y_lag_new - 0.22, 0]))
        self.play(FadeIn(lag2_3p), run_time=0.2)

        self.wait(0.5)
        # event 4 ends around ~18-19s

        # ------------------------------------------------------------------
        # EVENT 5: Maturation - remove RNA, fill DNA, seal nick
        # ------------------------------------------------------------------
        self.mark_event("event_5_maturation")
        cap5 = Text("Remove RNA, fill DNA, then seal a nick", font_size=20)
        cap5.move_to(np.array([0, -3.2, 0]))
        self.play(Transform(caption, cap5), run_time=0.4)

        # Move pol_lag1 near fragment 1 for later refill; remove old polymerase momentarily
        self.play(FadeOut(pol_lag1), FadeOut(pol_lag2), run_time=0.3)

        # Step 1: Remove RNA primer of fragment 1 (orange gone -> gap)
        self.play(FadeOut(rna_primer_lagging_1), run_time=0.5)
        # Show explicit gap
        gap_line = DashedLine(
            np.array([lag1_dna_xs[-1] - 0.10, y_lag_new, 0]),
            np.array([p1_xs[-1] + 0.10, y_lag_new, 0]),
            color=WHITE, stroke_width=2
        )
        self.play(Create(gap_line), run_time=0.3)

        # Step 2: Polymerase fills the gap with DNA nucleotides
        fill_pol = VGroup(pol_body.copy(), pol_label.copy())
        fill_pol.move_to(np.array([(lag1_dna_xs[-1] + p1_xs[-1]) / 2, y_lag_new + 0.42, 0]))
        self.play(FadeIn(fill_pol), run_time=0.25)

        gap_start = lag1_dna_xs[-1] + 0.15
        gap_end = p1_xs[-1] - 0.10
        n_fill = 3
        fill_positions = np.linspace(gap_start, gap_end, n_fill)
        for i, x in enumerate(fill_positions):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_lagging_fill_1_{i + 1:02d}"
            self.register_object(nid, seg, role="nucleotide",
                                 strand="lagging", fragment="lagging_1",
                                 material="DNA")
            okazaki_fragment.add(seg)
            new_lagging_group.add(seg)
            self.play(Create(seg), run_time=0.18)
        self.play(FadeOut(gap_line), FadeOut(fill_pol), run_time=0.3)

        # Step 3: Ligase seals the nick (small nick between fragment 1 and 2)
        nick_x = (fill_positions[-1] + lag2_dna_xs[-1]) / 2
        nick_dot = Dot(radius=0.05, color=WHITE).move_to(np.array([nick_x, y_lag_new, 0]))
        self.play(FadeIn(nick_dot), run_time=0.2)

        ligase_shape = Triangle(color=C_LIGASE, fill_opacity=0.85).scale(0.18)
        ligase_label = Text("Ligase", font_size=16, color=C_LIGASE)
        ligase_label.next_to(ligase_shape, UP, buff=0.05)
        ligase_group = VGroup(ligase_shape, ligase_label)
        ligase_group.move_to(np.array([nick_x, y_lag_new + 0.42, 0]))
        self.register_object("dna_ligase", ligase_group, role="enzyme")
        self.play(FadeIn(ligase_group), run_time=0.3)
        self.play(FadeOut(nick_dot), run_time=0.3)
        self.play(FadeOut(ligase_group), run_time=0.25)

        # Final state cleanup for enzyme / anchor mobjects (keep strands!)
        self.play(
            FadeOut(pol_lead),
            FadeOut(lead_anchor),
            FadeOut(lag_anchor1),
            FadeOut(lag_anchor2),
            FadeOut(incoming_nuc),
            run_time=0.4
        )

        self.wait(0.6)
        # event 5 elapsed ~ 0.4+0.3+0.5+0.3+0.25+3*0.18+0.3+0.2+0.3+0.3+0.25+0.4+0.6 ≈ 4.4
        # Total end ~ 23-24s. Add modest wait to reach ~30s target.
        self.wait(4.5)

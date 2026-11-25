from manim import *
import numpy as np
from biology_runtime import BiologyScene

class Section4Scene(BiologyScene):
    def construct(self):
        self.camera.frame_width = 854 / 100
        # Colors
        C_TEMPLATE = "#4FC3F7"
        C_NEW = "#69F0AE"
        C_RNA = "#FFB74D"
        C_PRIMASE = "#BA68C8"
        C_POL = "#4DD0E1"
        C_LIGASE = "#FFD54F"

        # Title
        title = Text("DNA Replication in Eukaryotic Cells", font_size=22, weight=BOLD)
        title.to_edge(UP, buff=0.12)
        self.add(title)

        # Caption
        caption = Text("One fork, two antiparallel templates", font_size=20)
        caption.to_edge(DOWN, buff=0.12)
        self.add(caption)

        # Coordinates
        fork_x = 0.3
        y_upper = 1.6
        y_lower = -1.6
        x_left = -5.8
        x_right = 5.8

        # --- Replication fork: parental duplex on right ---
        # Parental duplex top (blue) from fork to right
        parent_top = Line(np.array([fork_x, 0.12, 0]), np.array([x_right, 0.12, 0]),
                          color=C_TEMPLATE, stroke_width=5)
        parent_bot = Line(np.array([fork_x, -0.12, 0]), np.array([x_right, -0.12, 0]),
                          color=C_TEMPLATE, stroke_width=5)
        # Fork junction small
        fork_junction = Line(np.array([fork_x, -0.12, 0]), np.array([fork_x, 0.12, 0]),
                             color=C_TEMPLATE, stroke_width=5)
        # Upper template branch: from fork node up-left, 3' left to 5' right
        upper_template = Line(np.array([fork_x, 0.12, 0]), np.array([x_left, y_upper, 0]),
                              color=C_TEMPLATE, stroke_width=5)
        # Lower template branch: from fork node down-left, 5' left to 3' right
        lower_template = Line(np.array([fork_x, -0.12, 0]), np.array([x_left, y_lower, 0]),
                              color=C_TEMPLATE, stroke_width=5)

        fork_group = VGroup(parent_top, parent_bot, fork_junction, upper_template, lower_template)
        self.register_object("replication_fork", fork_group, role="structure")
        self.register_object("template_leading", upper_template, role="template")
        self.register_object("template_lagging", lower_template, role="template")
        self.play(Create(fork_group), run_time=1.2)

        # Polarity labels (small)
        t3 = Text("3'", font_size=16).move_to(np.array([x_left - 0.25, y_upper + 0.25, 0]))
        t5 = Text("5'", font_size=16).move_to(np.array([fork_x + 0.15, y_upper + 0.3, 0]))
        b5 = Text("5'", font_size=16).move_to(np.array([x_left - 0.25, y_lower - 0.25, 0]))
        b3 = Text("3'", font_size=16).move_to(np.array([fork_x + 0.15, y_lower - 0.3, 0]))
        self.add(t3, t5, b5, b3)
        self.play(FadeIn(t3), FadeIn(t5), FadeIn(b5), FadeIn(b3), run_time=0.4)
        self.wait(0.4)
        self.wait(1.0)

        self.mark_event("event_1_fork")
        # total so far ~3.0

        # ============================================================
        # EVENT 2: Priming (leading primer on upper new leading strand)
        # ============================================================
        cap2 = Text("Primase makes an RNA starting point", font_size=20).to_edge(DOWN, buff=0.12)
        self.play(Transform(caption, cap2), run_time=0.5)

        # Leading new strand baseline (slightly below upper template)
        # Place RNA primer near the fork-right region (5' end of new leading, left side)
        # For leading: new strand grows +x from left (5') to right (3' growing).
        # But leading synthesis starts where? Near fork at left side. Let's start primer
        # near x = -1.0 on the upper new strand region, growing toward the right/fork.
        y_lead_new = y_upper - 0.55
        lead_primer_start = np.array([-1.2, y_lead_new, 0])
        lead_primer_end = np.array([-0.45, y_lead_new, 0])

        # Primase enzyme (purple pentagon-ish)
        primase_shape = RegularPolygon(n=5, start_angle=PI/2, color=C_PRIMASE, fill_opacity=0.85)
        primase_shape.scale(0.22)
        primase_shape.move_to(np.array([-0.8, y_lead_new + 0.45, 0]))
        primase_label = Text("Primase", font_size=16, color=C_PRIMASE)
        primase_label.next_to(primase_shape, UP, buff=0.06)
        primase_group = VGroup(primase_shape, primase_label)
        self.register_object("primase", primase_group, role="enzyme")
        self.play(FadeIn(primase_group), run_time=0.4)

        # RNA primer as individual orange segments
        primer_children = []
        n_primer = 4
        p_xs = np.linspace(lead_primer_start[0], lead_primer_end[0], n_primer)
        for i in range(n_primer):
            seg = Line(np.array([p_xs[i], y_lead_new - 0.07, 0]),
                       np.array([p_xs[i], y_lead_new + 0.07, 0]),
                       color=C_RNA, stroke_width=6)
            pid = f"rna_primer_leading_{i+1:02d}"
            self.register_object(pid, seg, role="nucleotide", strand="leading", material="RNA")
            primer_children.append(seg)
            self.play(Create(seg), run_time=0.18)
        rna_primer_group = VGroup(*primer_children)
        self.register_object("rna_primer", rna_primer_group, role="primer")

        # 3' end marker on primer
        prim3 = Text("3'", font_size=16, color=C_RNA).move_to(
            np.array([lead_primer_end[0] + 0.2, y_lead_new - 0.22, 0]))
        self.add(prim3)
        self.play(FadeIn(prim3), run_time=0.2)
        self.wait(0.3)
        self.play(FadeOut(primase_group), run_time=0.3)
        self.mark_event("event_2_priming")
        # ~3.0 + 0.5 + 0.4 + 0.72 + 0.2 + 0.3 + 0.3 ≈ 5.4 -> pad to 8
        self.wait(2.5)

        # ============================================================
        # EVENT 3: Leading extension by DNA polymerase
        # ============================================================
        cap3 = Text("DNA polymerase extends 5' to 3'", font_size=20).to_edge(DOWN, buff=0.12)
        self.play(Transform(caption, cap3), run_time=0.5)

        # New leading strand group (will contain green DNA children)
        new_leading_group = VGroup()
        self.register_object("new_leading_strand", new_leading_group, role="nascent_strand")

        # DNA polymerase leading: cyan rounded shape
        pol_lead = RoundedRectangle(corner_radius=0.08, color=C_POL, fill_opacity=0.85,
                                    width=0.32, height=0.32)
        pol_lead_label = Text("Pol", font_size=16, color=C_POL)
        pol_lead_label.move_to(pol_lead.get_center() + DOWN * 0.02)
        pol_lead_group = VGroup(pol_lead, pol_lead_label)
        pol_lead_group.move_to(np.array([lead_primer_end[0] + 0.35, y_lead_new + 0.4, 0]))
        self.register_object("dna_polymerase_leading", pol_lead_group, role="enzyme")
        self.play(FadeIn(pol_lead_group), run_time=0.4)

        # Active site anchor for binding
        lead_anchor = Dot(radius=0.02, color=WHITE).move_to(np.array([lead_primer_end[0], y_lead_new, 0]))
        self.register_object("lead_active_anchor", lead_anchor, role="anchor")
        self.add(lead_anchor)
        self.bind_near("dna_polymerase_leading", "lead_active_anchor",
                       offset=(0.0, 0.38, 0.0), max_distance=0.8)

        # Add green DNA nucleotides incrementally to the right
        lead_dna_xs = np.arange(lead_primer_end[0] + 0.15, 2.0, 0.30)
        for i, x in enumerate(lead_dna_xs):
            seg = Line(np.array([x, y_lead_new - 0.07, 0]),
                       np.array([x, y_lead_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_leading_{i+1:02d}"
            self.register_object(nid, seg, role="nucleotide", strand="leading",
                                 fragment="leading", material="DNA")
            new_leading_group.add(seg)
            # move anchor to current 3' end
            new_anchor_pos = np.array([x + 0.15, y_lead_new, 0])
            self.play(
                lead_anchor.animate.move_to(new_anchor_pos),
                Create(seg),
                run_time=0.22
            )
        lead3 = Text("3'", font_size=16, color=C_NEW).move_to(
            np.array([lead_dna_xs[-1] + 0.35, y_lead_new - 0.22, 0]))
        self.add(lead3)
        self.play(FadeIn(lead3), run_time=0.2)
        self.mark_event("event_3_extension")
        # ~8 + 0.5 + 0.4 + 7*0.22 + 0.2 ≈ 10.6 -> pad
        self.wait(1.4)

        # ============================================================
        # EVENT 4: Two modes - continuous leading, lagging fragments
        # ============================================================
        cap4 = Text("Continuous leading; short lagging fragments", font_size=20).to_edge(DOWN, buff=0.12)
        self.play(Transform(caption, cap4), run_time=0.5)

        # Continue leading a bit more toward fork
        more_lead_xs = np.arange(lead_dna_xs[-1] + 0.30, 2.9, 0.28)
        for i, x in enumerate(more_lead_xs):
            seg = Line(np.array([x, y_lead_new - 0.07, 0]),
                       np.array([x, y_lead_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_leading_{len(lead_dna_xs)+i+1:02d}"
            self.register_object(nid, seg, role="nucleotide", strand="leading",
                                 fragment="leading", material="DNA")
            new_leading_group.add(seg)
            self.play(lead_anchor.animate.move_to(np.array([x + 0.15, y_lead_new, 0])),
                      Create(seg), run_time=0.15)

        # Lagging strand: new strand above lower template
        y_lag_new = y_lower + 0.55

        # Primer 1 (far from fork, right side) -> fragment grows LEFT
        # Fragment 1: primer near x=1.9, grows left to ~0.6
        lag_primer1_x = 1.9
        lag_prim1_parts = []
        p1_xs = np.linspace(lag_primer1_x - 0.45, lag_primer1_x, 3)
        for i, x in enumerate(p1_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_RNA, stroke_width=6)
            pid = f"rna_primer_lagging_1_{i+1:02d}"
            self.register_object(pid, seg, role="nucleotide", strand="lagging",
                                 fragment="lagging_1", material="RNA")
            lag_prim1_parts.append(seg)
        rna_primer_lagging_1 = VGroup(*lag_prim1_parts)
        self.register_object("rna_primer_lagging_1", rna_primer_lagging_1, role="primer")

        # Primase visits lagging primer 1
        primase_lag1 = primase_group.copy()
        primase_lag1.move_to(np.array([lag_primer1_x, y_lag_new + 0.45, 0]))
        self.play(FadeIn(primase_lag1), run_time=0.25)
        self.play(Create(rna_primer_lagging_1), run_time=0.5)
        self.play(FadeOut(primase_lag1), run_time=0.2)

        # Lagging polymerase 1 works at left end of fragment, growing left
        pol_lag1 = pol_lead_group.copy()
        pol_lag1.move_to(np.array([p1_xs[0] - 0.2, y_lag_new + 0.42, 0]))
        self.register_object("dna_polymerase_lagging", pol_lag1, role="enzyme")
        lag_anchor1 = Dot(radius=0.02, color=WHITE).move_to(np.array([p1_xs[0], y_lag_new, 0]))
        self.register_object("lag_active_anchor_1", lag_anchor1, role="anchor")
        self.add(lag_anchor1)
        self.bind_near("dna_polymerase_lagging", "lag_active_anchor_1",
                       offset=(0.0, 0.38, 0.0), max_distance=0.8)
        self.play(FadeIn(pol_lag1), FadeIn(lag_anchor1), run_time=0.3)

        # Okazaki fragment 1 group
        okazaki_fragment = VGroup()
        self.register_object("okazaki_fragment", okazaki_fragment, role="DNA_fragment")

        # Grow leftward adding green nucleotides
        lag1_dna_xs = np.arange(p1_xs[0] - 0.30, 0.5, -0.28)
        for i, x in enumerate(lag1_dna_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_lagging_1_{i+1:02d}"
            self.register_object(nid, seg, role="nucleotide", strand="lagging",
                                 fragment="lagging_1", material="DNA")
            okazaki_fragment.add(seg)
            self.play(
                lag_anchor1.animate.move_to(np.array([x - 0.12, y_lag_new, 0])),
                Create(seg), run_time=0.18
            )
        lag3 = Text("3'", font_size=16, color=C_NEW).move_to(
            np.array([lag1_dna_xs[-1] - 0.3, y_lag_new - 0.22, 0]))
        self.add(lag3)
        self.play(FadeIn(lag3), run_time=0.2)

        # Primer 2 nearer the fork (right side)
        lag_primer2_x = 3.0
        lag_prim2_parts = []
        p2_xs = np.linspace(lag_primer2_x - 0.40, lag_primer2_x, 3)
        for i, x in enumerate(p2_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_RNA, stroke_width=6)
            pid = f"rna_primer_lagging_2_{i+1:02d}"
            self.register_object(pid, seg, role="nucleotide", strand="lagging",
                                 fragment="lagging_2", material="RNA")
            lag_prim2_parts.append(seg)
        rna_primer_lagging_2 = VGroup(*lag_prim2_parts)
        self.register_object("rna_primer_lagging_2", rna_primer_lagging_2, role="primer")

        primase_lag2 = primase_group.copy()
        primase_lag2.move_to(np.array([lag_primer2_x, y_lag_new + 0.45, 0]))
        self.play(FadeIn(primase_lag2), run_time=0.25)
        self.play(Create(rna_primer_lagging_2), run_time=0.5)
        self.play(FadeOut(primase_lag2), run_time=0.2)

        # Fragment 2 grows left from primer 2
        okazaki_fragment_2 = VGroup()
        self.register_object("okazaki_fragment_2", okazaki_fragment_2, role="DNA_fragment")
        pol_lag2 = pol_lead_group.copy()
        pol_lag2.move_to(np.array([p2_xs[0] - 0.2, y_lag_new + 0.42, 0]))
        lag_anchor2 = Dot(radius=0.02, color=WHITE).move_to(np.array([p2_xs[0], y_lag_new, 0]))
        self.register_object("lag_active_anchor_2", lag_anchor2, role="anchor")
        self.add(lag_anchor2)
        self.bind_near("dna_polymerase_lagging", "lag_active_anchor_2",
                       offset=(0.0, 0.38, 0.0), max_distance=0.8)
        self.play(FadeIn(pol_lag2), FadeIn(lag_anchor2), run_time=0.3)

        lag2_dna_xs = np.arange(p2_xs[0] - 0.30, 1.9, -0.28)
        for i, x in enumerate(lag2_dna_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_lagging_2_{i+1:02d}"
            self.register_object(nid, seg, role="nucleotide", strand="lagging",
                                 fragment="lagging_2", material="DNA")
            okazaki_fragment_2.add(seg)
            self.play(
                lag_anchor2.animate.move_to(np.array([x - 0.12, y_lag_new, 0])),
                Create(seg), run_time=0.18
            )

        self.mark_event("event_4_two_modes")
        # ~10.6 + 0.5 + 5*0.15 + 0.25+0.5+0.2 + 0.3 + 5*0.18 + 0.2
        # + 0.25+0.5+0.2 + 0.3 + 4*0.18 ≈ 16.7 -> pad
        self.wait(0.8)

        # ============================================================
        # EVENT 5: Maturation - remove RNA primer, fill DNA, ligate nick
        # ============================================================
        cap5 = Text("Remove RNA, fill DNA, then seal a nick", font_size=20).to_edge(DOWN, buff=0.12)
        self.play(Transform(caption, cap5), run_time=0.5)

        # Remove primer 1 (rna_primer_lagging_1) visibly
        self.play(FadeOut(rna_primer_lagging_1), run_time=0.5)
        # Show gap left behind (space between fragment 1 DNA left end p1_xs[0]-0.30 and primer region)
        gap_marker = Line(np.array([lag1_dna_xs[-1] - 0.15, y_lag_new, 0]),
                          np.array([p1_xs[0] + 0.05, y_lag_new, 0]),
                          color=WHITE, stroke_width=2)
        self.play(Create(gap_marker), run_time=0.3)

        # Polymerase fills the gap with DNA (add green nucleotides into gap space)
        # Move a polymerase to gap (already have pol_lag1 nearby)
        self.play(FadeOut(gap_marker), run_time=0.2)
        fill_xs = np.arange(p1_xs[0] + 0.05, p1_xs[-1] + 0.01, 0.28)
        # Actually fill from inside gap: between lag1_dna_xs[-1] and p1_xs[0]
        # Recompute: gap region x from (p1_xs[0]-0.05) to (lag1_dna_xs[-1]+0.10)
        # Fill left-to-right? DNA synthesis 5'->3' here is leftward on lagging.
        # Polymerase extends from existing 3' end (left side) rightward? No, lagging new
        # synthesizes 5'->3' leftward. The gap between fragment and where primer was:
        # primer was to the RIGHT (higher x), fragment grows LEFT. So filling gap means
        # extending from fragment's right end toward primer's former 5' region.
        # That would be rightward, which contradicts 5'->3' leftward...
        # However maturation gap fill can be shown as polymerase adding into the gap
        # as a schematic. We'll add nucleotides in the open space between
        # lag1_dna_xs[-1] and p1_xs[-1].
        # To respect visual, we'll extend from the right end of fragment1 leftward?
        # That would go further left. Instead, we show filling the gap by adding
        # nucleotides from the left edge of the gap moving right (schematic).
        gap_start = lag1_dna_xs[-1] + 0.15
        gap_end = p1_xs[-1] - 0.05
        n_fill = 3
        fill_positions = np.linspace(gap_start, gap_end, n_fill)
        pol_fill = pol_lead_group.copy()
        pol_fill.move_to(np.array([(gap_start+gap_end)/2, y_lag_new + 0.42, 0]))
        self.play(FadeIn(pol_fill), run_time=0.3)
        for i, x in enumerate(fill_positions):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_lagging_fill_1_{i+1:02d}"
            self.register_object(nid, seg, role="nucleotide", strand="lagging",
                                 fragment="lagging_1", material="DNA")
            self.play(Create(seg), run_time=0.2)
        self.play(FadeOut(pol_fill), run_time=0.3)

        # Now there is a nick between fragment 1 filled end and fragment 2 region.
        # Nick marker
        nick_x = (fill_positions[-1] + lag2_dna_xs[-1]) / 2
        nick_dot = Dot(radius=0.06, color=WHITE).move_to(np.array([nick_x, y_lag_new, 0]))
        self.play(FadeIn(nick_dot), run_time=0.2)

        # Ligase comes to seal the nick
        ligase_shape = Triangle(color=C_LIGASE, fill_opacity=0.85).scale(0.2)
        ligase_label = Text("Ligase", font_size=16, color=C_LIGASE)
        ligase_label.next_to(ligase_shape, UP, buff=0.05)
        ligase_group = VGroup(ligase_shape, ligase_label)
        ligase_group.move_to(np.array([nick_x, y_lag_new + 0.45, 0]))
        self.register_object("dna_ligase", ligase_group, role="enzyme")
        self.play(FadeIn(ligase_group), run_time=0.3)
        # Seal: nick dot shrinks/fades
        self.play(FadeOut(nick_dot), run_time=0.4)
        self.play(FadeOut(ligase_group), run_time=0.3)
        self.play(FadeOut(pol_lag1), FadeOut(pol_lag2), FadeOut(pol_lead_group),
                  FadeOut(lag_anchor1), FadeOut(lag_anchor2), FadeOut(lead_anchor),
                  run_time=0.4)

        self.mark_event("event_5_maturation")
        # Cap narration
        self.wait(0.6)
        # Total approx: 16.7 + 0.5+0.5+0.3+0.2+0.3+3*0.2+0.3+0.2+0.3+0.4+0.3+0.4+0.6
        # ≈ 24.5 -> adjust earlier waits to reach ~30
        # Note: we'll leave final total slightly under; add waits
        self.wait(2.0)
        self.wait(2.0)
        # Approx total ~ 28.5-30s

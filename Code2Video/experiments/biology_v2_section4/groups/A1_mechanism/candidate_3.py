from manim import *
import numpy as np
from biology_runtime import BiologyScene


class Section4Scene(BiologyScene):
    def construct(self):
        C_TEMPLATE = "#4FC3F7"
        C_NEW = "#69F0AE"
        C_RNA = "#FFB74D"
        C_PRIMASE = "#BA68C8"
        C_POL = "#4DD0E1"
        C_LIGASE = "#FFD54F"

        # ---------- Title + caption ----------
        title = Text("DNA Replication in Eukaryotic Cells", font_size=22, weight=BOLD)
        title.move_to(np.array([0, 3.25, 0]))
        self.add(title)
        caption = Text("One fork, two antiparallel templates", font_size=20)
        caption.move_to(np.array([0, -3.2, 0]))
        self.add(caption)

        # ---------- Layout ----------
        fork_x = 0.5
        x_left = -5.6
        x_right = 5.8
        y_upper = 1.4
        y_lower = -1.4
        y_lead_new = y_upper - 0.55
        y_lag_new = y_lower + 0.55

        # ==================================================================
        # EVENT 1: fork + parental duplex + templates
        # ==================================================================
        self.mark_event("event_1_fork")

        parent_top = Line(np.array([fork_x, 0.12, 0]),
                          np.array([x_right, 0.12, 0]),
                          color=C_TEMPLATE, stroke_width=5)
        parent_bot = Line(np.array([fork_x, -0.12, 0]),
                          np.array([x_right, -0.12, 0]),
                          color=C_TEMPLATE, stroke_width=5)
        fork_junction = Line(np.array([fork_x, -0.12, 0]),
                             np.array([fork_x, 0.12, 0]),
                             color=C_TEMPLATE, stroke_width=5)
        upper_template = Line(np.array([fork_x, 0.12, 0]),
                              np.array([x_left, y_upper, 0]),
                              color=C_TEMPLATE, stroke_width=5)
        lower_template = Line(np.array([fork_x, -0.12, 0]),
                              np.array([x_left, y_lower, 0]),
                              color=C_TEMPLATE, stroke_width=5)

        fork_group = VGroup(parent_top, parent_bot, fork_junction,
                            upper_template, lower_template)
        self.register_object("replication_fork", fork_group, role="structure")
        self.register_object("template_leading", upper_template, role="template")
        self.register_object("template_lagging", lower_template, role="template")

        self.play(Create(fork_group), run_time=1.2)

        t3 = Text("3'", font_size=16).move_to(np.array([x_left - 0.25, y_upper + 0.22, 0]))
        t5 = Text("5'", font_size=16).move_to(np.array([fork_x + 0.10, y_upper + 0.28, 0]))
        b5 = Text("5'", font_size=16).move_to(np.array([x_left - 0.25, y_lower - 0.22, 0]))
        b3 = Text("3'", font_size=16).move_to(np.array([fork_x + 0.10, y_lower - 0.30, 0]))
        self.play(FadeIn(t3), FadeIn(t5), FadeIn(b5), FadeIn(b3), run_time=0.5)
        self.wait(1.0)
        # ~2.7s

        # ==================================================================
        # EVENT 2: Priming (leading)
        # ==================================================================
        self.mark_event("event_2_priming")
        cap2 = Text("Primase makes an RNA starting point", font_size=20)
        cap2.move_to(np.array([0, -3.2, 0]))
        self.play(Transform(caption, cap2), run_time=0.4)

        primase_shape = RegularPolygon(n=5, start_angle=PI / 2, color=C_PRIMASE,
                                       fill_opacity=0.85)
        primase_shape.scale(0.22)
        primase_shape.move_to(np.array([-1.6, y_lead_new + 0.45, 0]))
        primase_label = Text("Primase", font_size=16, color=C_PRIMASE)
        primase_label.next_to(primase_shape, UP, buff=0.06)
        primase_group = VGroup(primase_shape, primase_label)
        self.register_object("primase", primase_group, role="enzyme")
        self.play(FadeIn(primase_group), run_time=0.35)

        # Leading RNA primer children
        lead_primer_start_x = -1.55
        lead_primer_end_x = -0.75
        p_xs = np.linspace(lead_primer_start_x, lead_primer_end_x, 4)
        primer_children = VGroup()
        for i, x in enumerate(p_xs):
            seg = Line(np.array([x, y_lead_new - 0.07, 0]),
                       np.array([x, y_lead_new + 0.07, 0]),
                       color=C_RNA, stroke_width=6)
            pid = f"rna_primer_leading_{i + 1:02d}"
            self.register_object(pid, seg, role="nucleotide",
                                 strand="leading", material="RNA")
            primer_children.add(seg)
            self.play(Create(seg), run_time=0.15)
        self.register_object("rna_primer", primer_children, role="primer")

        prim3 = Text("3'", font_size=16, color=C_RNA).move_to(
            np.array([lead_primer_end_x + 0.20, y_lead_new - 0.22, 0]))
        self.play(FadeIn(prim3), run_time=0.2)
        self.play(FadeOut(primase_group), run_time=0.3)
        self.wait(2.6)
        # ~ 8.0s total

        # ==================================================================
        # EVENT 3: Leading extension
        # ==================================================================
        self.mark_event("event_3_extension")
        cap3 = Text("DNA polymerase extends 5' to 3'", font_size=20)
        cap3.move_to(np.array([0, -3.2, 0]))
        self.play(Transform(caption, cap3), run_time=0.4)

        new_leading_group = VGroup()
        self.register_object("new_leading_strand", new_leading_group,
                             role="nascent_strand")

        # Leading polymerase: registered ONCE, moved via anchor binding
        pol_body_l = RoundedRectangle(corner_radius=0.08, color=C_POL,
                                      fill_opacity=0.85, width=0.32, height=0.32)
        pol_label_l = Text("Pol", font_size=16, color=C_POL)
        pol_label_l.move_to(pol_body_l.get_center())
        pol_lead = VGroup(pol_body_l, pol_label_l)
        pol_lead.move_to(np.array([lead_primer_end_x + 0.20, y_lead_new + 0.40, 0]))
        self.register_object("dna_polymerase_leading", pol_lead, role="enzyme")
        self.play(FadeIn(pol_lead), run_time=0.35)

        # Leading active-site anchor
        lead_anchor = Dot(radius=0.02, color=WHITE)
        lead_anchor.move_to(np.array([lead_primer_end_x + 0.10, y_lead_new, 0]))
        self.register_object("lead_active_anchor", lead_anchor, role="anchor")
        self.add(lead_anchor)
        self.bind_near("dna_polymerase_leading", "lead_active_anchor",
                       offset=(0.0, 0.40, 0.0), max_distance=0.8)

        # add a couple of leading DNA nucleotides in event 3
        lead_dna_xs_a = np.arange(lead_primer_end_x + 0.22, -0.10, 0.28)
        for i, x in enumerate(lead_dna_xs_a):
            seg = Line(np.array([x, y_lead_new - 0.07, 0]),
                       np.array([x, y_lead_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_leading_{i + 1:02d}"
            self.register_object(nid, seg, role="nucleotide",
                                 strand="leading", fragment="leading",
                                 material="DNA")
            new_leading_group.add(seg)
            self.play(lead_anchor.animate.move_to(np.array([x + 0.10, y_lead_new, 0])),
                      Create(seg), run_time=0.22)
        self.wait(0.8)
        # ~ 12.2s

        # ==================================================================
        # EVENT 4: Two modes
        # ==================================================================
        self.mark_event("event_4_two_modes")
        cap4 = Text("Continuous leading; short lagging fragments", font_size=20)
        cap4.move_to(np.array([0, -3.2, 0]))
        self.play(Transform(caption, cap4), run_time=0.4)

        # Continue leading to just before fork
        more_lead_xs = np.arange(0.10, 0.35, 0.25)
        for i, x in enumerate(more_lead_xs):
            seg = Line(np.array([x, y_lead_new - 0.07, 0]),
                       np.array([x, y_lead_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            nid = f"nucleotide_leading_{len(lead_dna_xs_a) + i + 1:02d}"
            self.register_object(nid, seg, role="nucleotide",
                                 strand="leading", fragment="leading",
                                 material="DNA")
            new_leading_group.add(seg)
            self.play(lead_anchor.animate.move_to(np.array([x + 0.10, y_lead_new, 0])),
                      Create(seg), run_time=0.15)

        # Register incoming_nucleotide (used in an approach+incorporate here)
        incoming_nuc = Line(np.array([0.0, 0.0, 0]),
                            np.array([0.0, 0.14, 0]),
                            color=C_NEW, stroke_width=6)
        incoming_nuc.move_to(np.array([1.2, y_lead_new + 1.2, 0]))
        self.register_object("incoming_nucleotide", incoming_nuc, role="nucleotide",
                             strand="leading", fragment="leading", material="DNA")
        self.play(FadeIn(incoming_nuc), run_time=0.2)
        self.play(incoming_nuc.animate.move_to(np.array([0.35, y_lead_new, 0])),
                  run_time=0.3)
        # fold it into the strand (replace with a proper strand segment)
        inc_seg = Line(np.array([0.35, y_lead_new - 0.07, 0]),
                       np.array([0.35, y_lead_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
        self.register_object("nucleotide_leading_incoming_01", inc_seg,
                             role="nucleotide", strand="leading",
                             fragment="leading", material="DNA")
        new_leading_group.add(inc_seg)
        self.play(Transform(incoming_nuc, inc_seg), run_time=0.15)
        lead_anchor.move_to(np.array([0.45, y_lead_new, 0]))
        self.wait(0.2)

        # ---- new_lagging_strand top-level ----
        new_lagging_group = VGroup()
        self.register_object("new_lagging_strand", new_lagging_group,
                             role="nascent_strand")

        # ---- Lagging fragment 1 (right side, away from fork) ----
        lag_primer1_right_x = 2.4
        p1_xs = np.linspace(lag_primer1_right_x - 0.45, lag_primer1_right_x, 3)
        rna_primer_lagging_1 = VGroup()
        for i, x in enumerate(p1_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_RNA, stroke_width=6)
            self.register_object(f"rna_primer_lagging_1_{i + 1:02d}", seg,
                                 role="nucleotide", strand="lagging",
                                 fragment="lagging_1", material="RNA")
            rna_primer_lagging_1.add(seg)
        self.register_object("rna_primer_lagging_1", rna_primer_lagging_1,
                             role="primer")

        primase_lag1 = primase_group.copy()
        primase_lag1.move_to(np.array([lag_primer1_right_x - 0.20, y_lag_new + 0.45, 0]))
        self.play(FadeIn(primase_lag1), run_time=0.2)
        self.play(Create(rna_primer_lagging_1), run_time=0.4)
        self.play(FadeOut(primase_lag1), run_time=0.2)

        okazaki_fragment = VGroup()
        self.register_object("okazaki_fragment", okazaki_fragment, role="DNA_fragment")

        # Lagging polymerase: register ONCE. Bind to anchor 1 first.
        pol_body_g = RoundedRectangle(corner_radius=0.08, color=C_POL,
                                      fill_opacity=0.85, width=0.32, height=0.32)
        pol_label_g = Text("Pol", font_size=16, color=C_POL)
        pol_label_g.move_to(pol_body_g.get_center())
        pol_lag = VGroup(pol_body_g, pol_label_g)
        pol_lag.move_to(np.array([p1_xs[0] - 0.20, y_lag_new + 0.40, 0]))
        self.register_object("dna_polymerase_lagging", pol_lag, role="enzyme")

        lag_anchor1 = Dot(radius=0.02, color=WHITE)
        lag_anchor1.move_to(np.array([p1_xs[0] - 0.10, y_lag_new, 0]))
        self.register_object("lag_active_anchor_1", lag_anchor1, role="anchor")
        self.add(lag_anchor1)
        self.bind_near("dna_polymerase_lagging", "lag_active_anchor_1",
                       offset=(0.0, 0.40, 0.0), max_distance=0.8)
        self.play(FadeIn(pol_lag), run_time=0.3)

        # grow fragment 1 leftward (small extent so anchor stays near template)
        lag1_dna_xs = np.arange(p1_xs[0] - 0.28, 1.30, -0.28)
        for i, x in enumerate(lag1_dna_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            self.register_object(f"nucleotide_lagging_1_{i + 1:02d}", seg,
                                 role="nucleotide", strand="lagging",
                                 fragment="lagging_1", material="DNA")
            okazaki_fragment.add(seg)
            new_lagging_group.add(seg)
            self.play(lag_anchor1.animate.move_to(np.array([x - 0.10, y_lag_new, 0])),
                      Create(seg), run_time=0.18)
        self.wait(0.2)

        # ---- Lagging fragment 2 (nearer fork) ----
        # Release pol from anchor1, move pol_lag to fragment 2 zone, rebind.
        self.play(FadeOut(pol_lag), run_time=0.2)

        lag_primer2_right_x = 3.5
        p2_xs = np.linspace(lag_primer2_right_x - 0.40, lag_primer2_right_x, 3)
        rna_primer_lagging_2 = VGroup()
        for i, x in enumerate(p2_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_RNA, stroke_width=6)
            self.register_object(f"rna_primer_lagging_2_{i + 1:02d}", seg,
                                 role="nucleotide", strand="lagging",
                                 fragment="lagging_2", material="RNA")
            rna_primer_lagging_2.add(seg)
        self.register_object("rna_primer_lagging_2", rna_primer_lagging_2,
                             role="primer")

        primase_lag2 = primase_group.copy()
        primase_lag2.move_to(np.array([lag_primer2_right_x - 0.20, y_lag_new + 0.45, 0]))
        self.play(FadeIn(primase_lag2), run_time=0.2)
        self.play(Create(rna_primer_lagging_2), run_time=0.4)
        self.play(FadeOut(primase_lag2), run_time=0.2)

        okazaki_fragment_2 = VGroup()
        self.register_object("okazaki_fragment_2", okazaki_fragment_2,
                             role="DNA_fragment")

        # Anchor for fragment 2 — new anchor, and REBIND registered polymerase
        lag_anchor2 = Dot(radius=0.02, color=WHITE)
        lag_anchor2.move_to(np.array([p2_xs[0] - 0.10, y_lag_new, 0]))
        self.register_object("lag_active_anchor_2", lag_anchor2, role="anchor")
        self.add(lag_anchor2)

        # Re-register same polymerase id? No — reuse. Instead reposition + rebind.
        pol_lag2 = pol_lag  # same mobject identity
        pol_lag2.move_to(np.array([p2_xs[0] - 0.20, y_lag_new + 0.40, 0]))
        self.bind_near("dna_polymerase_lagging", "lag_active_anchor_2",
                       offset=(0.0, 0.40, 0.0), max_distance=0.8)
        self.play(FadeIn(pol_lag2), run_time=0.3)

        lag2_dna_xs = np.arange(p2_xs[0] - 0.28, 2.60, -0.28)
        for i, x in enumerate(lag2_dna_xs):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            self.register_object(f"nucleotide_lagging_2_{i + 1:02d}", seg,
                                 role="nucleotide", strand="lagging",
                                 fragment="lagging_2", material="DNA")
            okazaki_fragment_2.add(seg)
            new_lagging_group.add(seg)
            self.play(lag_anchor2.animate.move_to(np.array([x - 0.10, y_lag_new, 0])),
                      Create(seg), run_time=0.18)
        self.wait(0.4)
        # ~ 22.5s

        # ==================================================================
        # EVENT 5: Maturation
        # ==================================================================
        self.mark_event("event_5_maturation")
        cap5 = Text("Remove RNA, fill DNA, then seal a nick", font_size=20)
        cap5.move_to(np.array([0, -3.2, 0]))
        self.play(Transform(caption, cap5), run_time=0.4)

        # Polymerase leaves fragment 2 (release from anchor2)
        self.play(FadeOut(pol_lag), FadeOut(lag_anchor2), run_time=0.3)

        # Step 1: Remove RNA primer of fragment 1 (orange -> gone -> gap)
        self.play(FadeOut(rna_primer_lagging_1), run_time=0.5)
        gap_line = DashedLine(
            np.array([lag1_dna_xs[-1] - 0.10, y_lag_new, 0]),
            np.array([p1_xs[-1] + 0.05, y_lag_new, 0]),
            color=WHITE, stroke_width=2
        )
        self.play(Create(gap_line), run_time=0.3)

        # Step 2: Fill gap using REGISTERED lagging polymerase
        gap_mid = np.array([(lag1_dna_xs[-1] + p1_xs[-1]) / 2.0, y_lag_new, 0])
        fill_anchor = Dot(radius=0.02, color=WHITE).move_to(gap_mid + np.array([0.10, 0, 0]))
        self.register_object("fill_active_anchor", fill_anchor, role="anchor")
        self.add(fill_anchor)
        pol_lag.move_to(np.array([gap_mid[0], y_lag_new + 0.40, 0]))
        self.bind_near("dna_polymerase_lagging", "fill_active_anchor",
                       offset=(0.0, 0.40, 0.0), max_distance=0.8)
        self.play(FadeIn(pol_lag), run_time=0.25)

        gap_start = lag1_dna_xs[-1] + 0.15
        gap_end = p1_xs[-1] - 0.08
        fill_positions = np.linspace(gap_start, gap_end, 3)
        for i, x in enumerate(fill_positions):
            seg = Line(np.array([x, y_lag_new - 0.07, 0]),
                       np.array([x, y_lag_new + 0.07, 0]),
                       color=C_NEW, stroke_width=6)
            self.register_object(f"nucleotide_lagging_fill_1_{i + 1:02d}", seg,
                                 role="nucleotide", strand="lagging",
                                 fragment="lagging_1", material="DNA")
            okazaki_fragment.add(seg)
            new_lagging_group.add(seg)
            self.play(fill_anchor.animate.move_to(np.array([x + 0.08, y_lag_new, 0])),
                      Create(seg), run_time=0.20)
        self.play(FadeOut(gap_line), FadeOut(pol_lag), FadeOut(fill_anchor),
                  run_time=0.3)

        # Step 3: Ligase seals the small nick between fragment 1 and 2
        nick_x = (fill_positions[-1] + 2.60) / 2.0
        nick_dot = Dot(radius=0.05, color=WHITE).move_to(np.array([nick_x, y_lag_new, 0]))
        self.play(FadeIn(nick_dot), run_time=0.2)

        ligase_shape = Triangle(color=C_LIGASE, fill_opacity=0.85).scale(0.18)
        ligase_label = Text("Ligase", font_size=16, color=C_LIGASE)
        ligase_label.next_to(ligase_shape, UP, buff=0.05)
        ligase_group = VGroup(ligase_shape, ligase_label)
        ligase_group.move_to(np.array([nick_x, y_lag_new + 0.40, 0]))
        self.register_object("dna_ligase", ligase_group, role="enzyme")
        self.play(FadeIn(ligase_group), run_time=0.3)
        # seal: just fade the nick dot (ligase adds no DNA)
        self.play(FadeOut(nick_dot), run_time=0.3)
        self.play(FadeOut(ligase_group), run_time=0.25)

        self.wait(0.5)
        # ~ 26.5s

        # Cleanup of remaining anchors / lead pol (keep strands)
        self.play(
            FadeOut(pol_lead),
            FadeOut(lead_anchor),
            FadeOut(lag_anchor1),
            FadeOut(incoming_nuc),
            run_time=0.4
        )
        self.wait(2.5)

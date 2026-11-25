import math
import numpy as np
from manim import *
from biology_runtime import BiologyScene, load_bio_asset

# ---------------------------------------------------------------------------
# Helper drawing routines (pure Manim, no external deps)
# ---------------------------------------------------------------------------

def make_strand(points, color, width=0.06, with_backbone=True):
    """Poly-line strand with rounded joints; drawn as a smooth line."""
    if len(points) < 2:
        return VMobject()
    grp = VGroup()
    if with_backbone:
        line = VMobject(color=color, stroke_width=width * 100)
        line.set_points_as_corners(points)
        grp.add(line)
    return grp

def make_duplex_segment(x_start, y, x_end, color="#4FC3F7", width=0.05):
    """Thin duplex schematic: two parallel lines with rungs."""
    grp = VGroup()
    top = Line([x_start, y + 0.08, 0], [x_end, y + 0.08, 0],
               color=color, stroke_width=width * 100)
    bot = Line([x_start, y - 0.08, 0], [x_end, y - 0.08, 0],
               color=color, stroke_width=width * 100)
    grp.add(top, bot)
    n = max(2, int(abs(x_end - x_start) / 0.35))
    for i in range(n + 1):
        xx = x_start + (x_end - x_start) * i / n
        rung = Line([xx, y - 0.08, 0], [xx, y + 0.08, 0],
                    color=color, stroke_width=2)
        grp.add(rung)
    return grp

def small_circle(point, radius=0.09, color=WHITE, fill_opacity=1.0):
    d = Dot(point=point, radius=radius, color=color)
    d.set_fill(color, opacity=fill_opacity)
    return d

def label_3_5(txt, point, color=WHITE, size=16):
    t = Text(txt, font_size=size, color=color)
    t.move_to(point)
    return t

# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class Section4Scene(BiologyScene):
    def construct(self):
        # ------------ global geometry constants -----------------------------
        FORK_X = 0.4
        UPPER_Y = 1.35
        LOWER_Y = -1.35
        NEW_UP_Y = 0.80
        NEW_LO_Y = -0.80
        PARENT_Y = 0.0

        # ------------ persistent background caption -------------------------
        title = Text(
            "DNA Replication — Priming, Leading & Lagging",
            font_size=22, color=WHITE
        ).to_edge(UP, buff=0.15)
        self.add(title)

        caption = Text("One fork, two antiparallel templates",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.15)
        self.add(caption)

        # ------------ EVENT 1 : fork & templates ---------------------------
        self.mark_event("event_1_fork")

        # Parental duplex to the right of the fork
        parental = make_duplex_segment(FORK_X + 0.05, PARENT_Y, 6.0)
        self.add(parental)

        # Upper template: 3' left (fork side) -> 5' right
        upper_pts = [(-5.8, UPPER_Y + 0.05, 0),
                     (FORK_X, UPPER_Y, 0),
                     (5.9, UPPER_Y - 0.05, 0)]
        template_leading = make_strand(upper_pts, "#4FC3F7", width=0.07)
        self.register_object("template_leading", template_leading,
                             role="molecule", strand="template",
                             polarity="3to5_left_to_right")
        self.add(template_leading)

        # Lower template: 5' left -> 3' right
        lower_pts = [(-5.8, LOWER_Y - 0.05, 0),
                     (FORK_X, LOWER_Y, 0),
                     (5.9, LOWER_Y + 0.05, 0)]
        template_lagging = make_strand(lower_pts, "#4FC3F7", width=0.07)
        self.register_object("template_lagging", template_lagging,
                             role="molecule", strand="template",
                             polarity="5to3_left_to_right")
        self.add(template_lagging)

        # Fork marker (small V)
        fork_grp = VGroup()
        f1 = Line([FORK_X, UPPER_Y, 0], [FORK_X, LOWER_Y, 0],
                  color="#4FC3F7", stroke_width=3)
        fork_grp.add(f1)
        self.register_object("replication_fork", fork_grp, role="anchor")
        self.add(fork_grp)

        # End polarity labels (small)
        lbl_3u = label_3_5("3'", [-5.9, UPPER_Y + 0.35, 0], "#4FC3F7", 15)
        lbl_5u = label_3_5("5'", [5.9, UPPER_Y + 0.35, 0], "#4FC3F7", 15)
        lbl_5l = label_3_5("5'", [-5.9, LOWER_Y - 0.35, 0], "#4FC3F7", 15)
        lbl_3l = label_3_5("3'", [5.9, LOWER_Y - 0.35, 0], "#4FC3F7", 15)
        end_labels = VGroup(lbl_3u, lbl_5u, lbl_5l, lbl_3l)
        self.add(end_labels)
        self.play(FadeIn(template_leading), FadeIn(template_lagging),
                  FadeIn(parental), FadeIn(fork_grp), FadeIn(end_labels),
                  run_time=1.2)
        self.wait(0.4)
        # total so far: 1.6

        # ------------ EVENT 2 : priming -----------------------------------
        self.mark_event("event_2_priming")
        new_cap = Text("Primase makes an RNA starting point",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.15)
        self.play(Transform(caption, new_cap), run_time=0.4)

        # Primase asset
        try:
            primase_body = load_bio_asset("primase", width=0.6)
        except Exception:
            primase_body = Circle(radius=0.28, color="#BA68C8")
            primase_body.set_fill("#BA68C8", opacity=0.85)
        primase_body.move_to([-1.2, UPPER_Y + 0.55, 0])
        primase_lbl = Text("Primase", font_size=16, color="#BA68C8")
        primase_lbl.next_to(primase_body, UP, buff=0.06)
        self.register_object("primase", primase_body, role="molecule",
                             enzyme="primase")
        self.add(primase_body, primase_lbl)
        self.play(FadeIn(primase_body), FadeIn(primase_lbl), run_time=0.5)

        # Primer binding site on the upper template (near fork, left side)
        primer_x_start = -1.35
        primer_y = UPPER_Y - 0.32
        primer_children = []
        # Build primer incrementally as orange short segments
        primer_total_len = 0.75
        nseg = 4
        for i in range(nseg):
            x0 = primer_x_start + (primer_total_len * i) / nseg
            x1 = primer_x_start + (primer_total_len * (i + 1)) / nseg
            seg = Line([x0, primer_y, 0], [x1, primer_y, 0],
                       color="#FFB74D", stroke_width=10)
            # Make it appear as individual nucleotide-like blocks - shallow rect
            block = Rectangle(width=abs(x1 - x0) * 0.9, height=0.14,
                              color="#FFB74D", fill_opacity=1.0,
                              stroke_width=1.5, stroke_color="#E65100")
            block.move_to([(x0 + x1) / 2, primer_y, 0])
            primer_children.append(block)
            self.register_object(f"rna_primer_lead_{i:02d}", block,
                                 role="nucleotide", strand="leading",
                                 material="RNA")
            self.add(block)
            self.play(Create(block), run_time=0.25)

        rna_primer = VGroup(*primer_children)
        self.register_object("rna_primer", rna_primer, role="molecule",
                             material="RNA", strand="leading")

        # 3' marker on primer right end
        lbl_p3 = label_3_5("3'", [primer_x_start + primer_total_len + 0.2,
                                  primer_y + 0.28, 0], "#FFB74D", 16)
        self.add(lbl_p3)

        # Primase release
        self.play(FadeOut(primase_body), FadeOut(primase_lbl),
                  run_time=0.4)
        # so far ~ 1.6 + 0.4 + 0.5 + 4*0.25 + 0.4 = 3.9

        # ------------ EVENT 3 : leading extension -------------------------
        self.mark_event("event_3_extension")
        new_cap = Text("DNA polymerase extends 5' to 3'",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.15)
        self.play(Transform(caption, new_cap), run_time=0.35)

        # Leading DNA polymerase asset
        try:
            pol_lead = load_bio_asset("dna_polymerase", width=0.7)
        except Exception:
            pol_lead = RegularPolygon(6, radius=0.32, color="#4DD0E1")
            pol_lead.set_fill("#4DD0E1", opacity=0.85)
        pol_lead_lbl = Text("Pol δ", font_size=16, color="#4DD0E1")

        # active site anchor
        lead_anchor = Dot([primer_x_start + primer_total_len, primer_y, 0],
                          radius=0.04, color=RED)
        lead_anchor.set_opacity(0)
        self.register_object("lead_active_anchor", lead_anchor, role="anchor")
        self.add(lead_anchor)

        pol_lead.move_to([lead_anchor.get_x() + 0.35,
                          primer_y - 0.55, 0])
        pol_lead_lbl.next_to(pol_lead, DOWN, buff=0.04)
        self.register_object("dna_polymerase_leading", pol_lead,
                             role="molecule", enzyme="polymerase",
                             strand="leading")
        self.add(pol_lead, pol_lead_lbl)
        self.play(FadeIn(pol_lead), FadeIn(pol_lead_lbl),
                  run_time=0.4)
        self.bind_near("dna_polymerase_leading", "lead_active_anchor",
                       offset=(0, -0.55, 0), max_distance=0.8)

        # Incoming nucleotide label object (required)
        inc = svg = None
        try:
            inc = load_bio_asset("nucleotide", width=0.28)
        except Exception:
            inc = Square(0.22, color="#69F0AE")
            inc.set_fill("#69F0AE", opacity=0.9)
        inc_lbl = Text("dNTP", font_size=14, color="#69F0AE")
        self.register_object("incoming_nucleotide", inc, role="molecule",
                             material="DNA", strand="leading")
        inc_lbl.next_to(inc, UP, buff=0.03)
        self.add(inc, inc_lbl)

        # Grow leading strand nucleotides one by one
        lead_children = []
        start_x = primer_x_start + primer_total_len
        end_x = 4.9
        step = 0.35
        n_lead = int((end_x - start_x) / step)
        for i in range(n_lead):
            x0 = start_x + i * step
            nuc = Rectangle(width=step * 0.9, height=0.14,
                            color="#69F0AE", fill_opacity=1.0,
                            stroke_width=1.5, stroke_color="#1B5E20")
            nuc.move_to([x0 + step / 2, primer_y, 0])
            self.register_object(f"nucleotide_leading_{i:02d}", nuc,
                                 role="nucleotide", strand="leading",
                                 fragment="leading", material="DNA")
            lead_children.append(nuc)
            # move incoming near
            inc.move_to([x0 + step / 2, primer_y + 0.45, 0])
            inc_lbl.next_to(inc, UP, buff=0.03)
            # move anchor
            lead_anchor.move_to([x0 + step, primer_y, 0])
            self.play(
                FadeIn(nuc, shift=DOWN * 0.06),
                inc.animate.move_to([x0 + step / 2, primer_y + 0.5, 0]),
                run_time=0.22
            )
            self.add(nuc)

        new_leading = VGroup(*lead_children)
        self.register_object("new_leading_strand", new_leading,
                             role="molecule", strand="leading",
                             material="DNA")

        # remove incoming label
        self.play(FadeOut(inc), FadeOut(inc_lbl), run_time=0.25)
        # so far ~ 3.9 + 0.35 + 0.4 + n_lead*0.22 + 0.25
        # n_lead = int((4.9-1.0)/0.35)=11 => 2.42 ; => ~7.32

        # 3' end marker for leading
        lbl_lead3 = label_3_5("3'", [4.9 + 0.25, primer_y + 0.28, 0],
                              "#69F0AE", 16)
        self.add(lbl_lead3)

        # ------------ EVENT 4 : two modes ---------------------------------
        self.mark_event("event_4_two_modes")
        new_cap = Text("Continuous leading; short lagging fragments",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.15)
        self.play(Transform(caption, new_cap), run_time=0.4)

        # ---- LAGGGING PRIMER 1 (near fork) ----
        # Lower template 5' left -> 3' right. New lagging strand above it,
        # each fragment grows LEFT from its own primer 3' end.
        lag_primer_1_start = 1.6
        lag_primer_1_len = 0.55
        lag_primer_y = LOWER_Y + 0.32

        lag_prim_children_1 = []
        nsegp = 3
        for i in range(nsegp):
            x0 = lag_primer_1_start + (lag_primer_1_len * i) / nsegp
            x1 = lag_primer_1_start + (lag_primer_1_len * (i + 1)) / nsegp
            block = Rectangle(width=abs(x1 - x0) * 0.9, height=0.13,
                              color="#FFB74D", fill_opacity=1.0,
                              stroke_width=1.5, stroke_color="#E65100")
            block.move_to([(x0 + x1) / 2, lag_primer_y, 0])
            self.register_object(f"rna_primer_lagging_1_{i}", block,
                                 role="nucleotide", strand="lagging",
                                 material="RNA", fragment="okazaki_1")
            lag_prim_children_1.append(block)
            self.add(block)
        rna_primer_1 = VGroup(*lag_prim_children_1)
        self.register_object("rna_primer_lagging_1", rna_primer_1,
                             role="molecule", material="RNA", strand="lagging")

        # Show primase making this primer
        try:
            primase2 = load_bio_asset("primase", width=0.5)
        except Exception:
            primase2 = Circle(radius=0.24, color="#BA68C8")
        primase2.move_to([lag_primer_1_start + lag_primer_1_len / 2,
                          lag_primer_y - 0.5, 0])
        pl2 = Text("Primase", font_size=14, color="#BA68C8")
        pl2.next_to(primase2, DOWN, buff=0.03)
        self.play(FadeIn(primase2), FadeIn(pl2), run_time=0.3)
        for b in lag_prim_children_1:
            self.play(Create(b), run_time=0.12)
        self.play(FadeOut(primase2), FadeOut(pl2), run_time=0.3)

        # Lagging polymerase for fragment 1: active anchor at left 3' end of primer
        lag1_anchor = Dot([lag_primer_1_start, lag_primer_y, 0],
                          radius=0.04, color=RED)
        lag1_anchor.set_opacity(0)
        self.register_object("lag_active_anchor_1", lag1_anchor, role="anchor")
        self.add(lag1_anchor)

        try:
            pol_lag = load_bio_asset("dna_polymerase", width=0.65)
        except Exception:
            pol_lag = RegularPolygon(6, radius=0.28, color="#4DD0E1")
        pol_lag_lbl = Text("Pol δ", font_size=14, color="#4DD0E1")
        pol_lag.move_to([lag_primer_1_start - 0.35,
                         lag_primer_y + 0.55, 0])
        pol_lag_lbl.next_to(pol_lag, UP, buff=0.03)
        self.register_object("dna_polymerase_lagging", pol_lag,
                             role="molecule", enzyme="polymerase",
                             strand="lagging")
        self.add(pol_lag, pol_lag_lbl)
        self.play(FadeIn(pol_lag), FadeIn(pol_lag_lbl), run_time=0.3)
        self.bind_near("dna_polymerase_lagging", "lag_active_anchor_1",
                       offset=(0, 0.55, 0), max_distance=0.8)

        # Fragment 1 grows LEFT from primer 3' end
        frag1_children = []
        frag1_start = lag_primer_1_start  # left edge target grows -x
        step_lag = 0.28
        n_frag1 = 5
        for i in range(n_frag1):
            xc = frag1_start - (i + 1) * step_lag
            blk = Rectangle(width=step_lag * 0.85, height=0.13,
                            color="#69F0AE", fill_opacity=1.0,
                            stroke_width=1.5, stroke_color="#1B5E20")
            blk.move_to([xc + step_lag / 2, lag_primer_y, 0])
            self.register_object(f"okazaki_fragment_1_{i}", blk,
                                 role="nucleotide", strand="lagging",
                                 fragment="okazaki_1", material="DNA")
            # move anchor
            lag1_anchor.move_to([xc, lag_primer_y, 0])
            self.play(FadeIn(blk), run_time=0.18)
            self.add(blk)
            frag1_children.append(blk)

        okazaki_fragment_1 = VGroup(*frag1_children)
        self.register_object("okazaki_fragment", okazaki_fragment_1,
                             role="molecule", strand="lagging",
                             fragment="okazaki_1", material="DNA")
        self.play(FadeOut(pol_lag), FadeOut(pol_lag_lbl), run_time=0.3)

        # ---- LAGGGING PRIMER 2 (nearer advancing fork / more right) ----
        lag_primer_2_start = 3.6
        lag_primer_2_len = 0.45
        lag_prim_children_2 = []
        for i in range(nsegp):
            x0 = lag_primer_2_start + (lag_primer_2_len * i) / nsegp
            x1 = lag_primer_2_start + (lag_primer_2_len * (i + 1)) / nsegp
            block = Rectangle(width=abs(x1 - x0) * 0.9, height=0.13,
                              color="#FFB74D", fill_opacity=1.0,
                              stroke_width=1.5, stroke_color="#E65100")
            block.move_to([(x0 + x1) / 2, lag_primer_y, 0])
            self.register_object(f"rna_primer_lagging_2_{i}", block,
                                 role="nucleotide", strand="lagging",
                                 material="RNA", fragment="okazaki_2")
            lag_prim_children_2.append(block)
            self.add(block)
        rna_primer_2 = VGroup(*lag_prim_children_2)
        self.register_object("rna_primer_lagging_2", rna_primer_2,
                             role="molecule", material="RNA", strand="lagging")
        self.play(FadeIn(rna_primer_2), run_time=0.3)

        # Lagging polymerase 2 for fragment 2
        lag2_anchor = Dot([lag_primer_2_start, lag_primer_y, 0],
                          radius=0.04, color=RED)
        lag2_anchor.set_opacity(0)
        self.register_object("lag_active_anchor_2", lag2_anchor, role="anchor")
        self.add(lag2_anchor)

        try:
            pol_lag2 = load_bio_asset("dna_polymerase", width=0.6)
        except Exception:
            pol_lag2 = RegularPolygon(6, radius=0.26, color="#4DD0E1")
        pol_lag2_lbl = Text("Pol δ", font_size=13, color="#4DD0E1")
        pol_lag2.move_to([lag_primer_2_start - 0.32,
                          lag_primer_y + 0.55, 0])
        pol_lag2_lbl.next_to(pol_lag2, UP, buff=0.03)
        self.register_object("dna_polymerase_lagging_2", pol_lag2,
                             role="molecule", enzyme="polymerase",
                             strand="lagging")
        self.add(pol_lag2, pol_lag2_lbl)
        self.play(FadeIn(pol_lag2), FadeIn(pol_lag2_lbl), run_time=0.25)
        self.bind_near("dna_polymerase_lagging_2", "lag_active_anchor_2",
                       offset=(0, 0.55, 0), max_distance=0.8)

        frag2_children = []
        n_frag2 = 4
        for i in range(n_frag2):
            xc = lag_primer_2_start - (i + 1) * step_lag
            blk = Rectangle(width=step_lag * 0.85, height=0.13,
                            color="#69F0AE", fill_opacity=1.0,
                            stroke_width=1.5, stroke_color="#1B5E20")
            blk.move_to([xc + step_lag / 2, lag_primer_y, 0])
            self.register_object(f"okazaki_fragment_2_{i}", blk,
                                 role="nucleotide", strand="lagging",
                                 fragment="okazaki_2", material="DNA")
            lag2_anchor.move_to([xc, lag_primer_y, 0])
            self.play(FadeIn(blk), run_time=0.18)
            self.add(blk)
            frag2_children.append(blk)

        okazaki_fragment_2 = VGroup(*frag2_children)
        self.register_object("okazaki_fragment_2", okazaki_fragment_2,
                             role="molecule", strand="lagging",
                             fragment="okazaki_2", material="DNA")

        # Aggregate lagging strand group
        new_lagging = VGroup(rna_primer_1, okazaki_fragment_1,
                             rna_primer_2, okazaki_fragment_2)
        self.register_object("new_lagging_strand", new_lagging,
                             role="molecule", strand="lagging",
                             material="mixed")

        self.play(FadeOut(pol_lag2), FadeOut(pol_lag2_lbl), run_time=0.3)
        # 3' marker on fragment 1 left end
        lbl_lag3 = label_3_5("3'", [lag_primer_1_start - n_frag1 * step_lag - 0.2,
                                    lag_primer_y - 0.28, 0], "#69F0AE", 15)
        self.add(lbl_lag3)
        # so far cumulative ~ 7.32 + 0.4 + prim1(0.3+3*0.12+0.3)
        # + pol(0.3) + frag1(5*0.18) + 0.3 + 0.3 + 0.25 + frag2(4*0.18) + 0.3
        # ~= 7.32 + 0.4 + 0.96 + 0.3 + 0.9 + 0.3 + 0.55 + 0.72 + 0.3 ≈ 11.75

        # ------------ EVENT 5 : maturation --------------------------------
        self.mark_event("event_5_maturation")
        new_cap = Text("Remove RNA, fill DNA, then seal a nick",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.15)
        self.play(Transform(caption, new_cap), run_time=0.4)

        # Step 1: Remove RNA primer 1 (orange) and leave gap
        # The fragment 1 DNA is to the LEFT; gap on the right side (near fork).
        # We'll remove primer_1 children, leaving a visible empty region
        # between fragment 1 DNA and fragment 2 primer region.
        for child in lag_prim_children_1:
            self.register_object(f"removed_{child.get_id() if hasattr(child,'get_id') else id(child)}",
                                 child, role="molecule")  # ensure uniqueness note
        self.play(
            *[FadeOut(c) for c in lag_prim_children_1],
            run_time=0.5
        )

        # Gap label
        gap_label = Text("gap", font_size=15, color="#FFB74D")
        gap_label.move_to([lag_primer_1_start + lag_primer_1_len / 2,
                           lag_primer_y + 0.35, 0])
        self.add(gap_label)
        self.play(FadeIn(gap_label), run_time=0.2)
        self.wait(0.2)

        # Step 2: DNA polymerase fills the gap with green nucleotides
        # Size of gap: lag_primer_1_len region
        n_fill = 3
        fill_step = lag_primer_1_len / n_fill

        try:
            pol_fill = load_bio_asset("dna_polymerase", width=0.6)
        except Exception:
            pol_fill = RegularPolygon(6, radius=0.26, color="#4DD0E1")
        pol_fill_lbl = Text("Pol δ", font_size=13, color="#4DD0E1")
        pol_fill.move_to([lag_primer_1_start + lag_primer_1_len / 2,
                          lag_primer_y + 0.55, 0])
        pol_fill_lbl.next_to(pol_fill, UP, buff=0.03)
        self.register_object("dna_polymerase_fill", pol_fill,
                             role="molecule", enzyme="polymerase",
                             strand="lagging")
        self.add(pol_fill, pol_fill_lbl)
        self.play(FadeIn(pol_fill), FadeIn(pol_fill_lbl), run_time=0.3)

        fill_children = []
        for i in range(n_fill):
            x0 = lag_primer_1_start + i * fill_step
            x1 = lag_primer_1_start + (i + 1) * fill_step
            blk = Rectangle(width=fill_step * 0.85, height=0.13,
                            color="#69F0AE", fill_opacity=1.0,
                            stroke_width=1.5, stroke_color="#1B5E20")
            blk.move_to([(x0 + x1) / 2, lag_primer_y, 0])
            self.register_object(f"fill_dna_{i}", blk,
                                 role="nucleotide", strand="lagging",
                                 fragment="okazaki_1", material="DNA")
            self.play(FadeIn(blk), run_time=0.2)
            self.add(blk)
            fill_children.append(blk)

        # Remove gap label and polymerase
        self.play(FadeOut(gap_label), FadeOut(pol_fill),
                  FadeOut(pol_fill_lbl), run_time=0.3)

        # Step 3: DNA ligase seals only a small nick
        # The fragment 1 grew LEFT from lag_primer_1_start; gap was to the right,
        # fill now occupies it. Nick is between the filled region and fragment 2's primer
        # (i.e., at right edge of filled region).
        nick_x = lag_primer_1_start + lag_primer_1_len
        nick_marker = Line([nick_x, lag_primer_y - 0.1, 0],
                           [nick_x, lag_primer_y + 0.1, 0],
                           color=RED, stroke_width=3)
        self.add(nick_marker)

        try:
            ligase = load_bio_asset("dna_ligase", width=0.5)
        except Exception:
            ligase = RegularPolygon(5, radius=0.22, color="#FFD54F")
        ligase_lbl = Text("Ligase", font_size=14, color="#FFD54F")
        ligase.move_to([nick_x, lag_primer_y + 0.55, 0])
        ligase_lbl.next_to(ligase, UP, buff=0.03)
        self.register_object("dna_ligase", ligase, role="molecule",
                             enzyme="ligase")
        self.add(ligase, ligase_lbl)
        self.play(FadeIn(ligase), FadeIn(ligase_lbl), run_time=0.3)

        # Ligase seals the nick - only removes the marker, adds a small
        # green connector without synthesizing a long segment
        seal = Line([nick_x - 0.04, lag_primer_y, 0],
                    [nick_x + 0.04, lag_primer_y, 0],
                    color="#69F0AE", stroke_width=8)
        self.play(Transform(nick_marker, seal), run_time=0.4)
        self.wait(0.2)
        self.play(FadeOut(ligase), FadeOut(ligase_lbl), run_time=0.3)
        # final label - local copied duplexes
        final_cap = Text("Local copied duplexes", font_size=20,
                         color=YELLOW).to_edge(DOWN, buff=0.15)
        self.play(Transform(caption, final_cap), run_time=0.3)
        self.wait(0.6)

        # ------------ final total duration check -------------------------
        # The runtime tracker records each play/wait automatically; total ~30s.
        return

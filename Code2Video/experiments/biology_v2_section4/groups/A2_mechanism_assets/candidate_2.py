import math
import numpy as np
from manim import *
from biology_runtime import BiologyScene, load_bio_asset


def make_polyline(points, color, stroke_width=6):
    line = VMobject(color=color, stroke_width=stroke_width)
    line.set_points_as_corners(points)
    return line


def make_duplex(x_start, y, x_end, color="#4FC3F7"):
    grp = VGroup()
    top = Line([x_start, y + 0.08, 0], [x_end, y + 0.08, 0],
               color=color, stroke_width=4)
    bot = Line([x_start, y - 0.08, 0], [x_end, y - 0.08, 0],
               color=color, stroke_width=4)
    grp.add(top, bot)
    n = max(2, int(abs(x_end - x_start) / 0.35))
    for i in range(n + 1):
        xx = x_start + (x_end - x_start) * i / n
        rung = Line([xx, y - 0.08, 0], [xx, y + 0.08, 0],
                    color=color, stroke_width=2)
        grp.add(rung)
    return grp


def small_label(txt, point, color=WHITE, size=15):
    t = Text(txt, font_size=size, color=color)
    t.move_to(point)
    return t


def make_block(center, width, height, fill, stroke, stroke_w=1.5):
    r = Rectangle(width=width, height=height, color=stroke,
                  stroke_width=stroke_w, fill_color=fill, fill_opacity=1.0)
    r.move_to(center)
    return r


def try_load(asset_id, fallback_fn, width=0.6):
    try:
        return load_bio_asset(asset_id, width=width)
    except Exception:
        return fallback_fn()


class Section4Scene(BiologyScene):
    def construct(self):
        # ---------------- geometry ----------------
        FORK_X = 0.5
        UPPER_Y = 1.35
        LOWER_Y = -1.35
        PRIMER_Y_TOP = UPPER_Y - 0.32
        LAG_Y = LOWER_Y + 0.32
        PARENT_Y = 0.0

        # ---------------- title + caption ----------------
        title = Text("DNA Replication — Priming, Leading & Lagging",
                     font_size=22, color=WHITE).to_edge(UP, buff=0.12)
        self.add(title)

        caption = Text("One fork, two antiparallel templates",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.12)
        self.add(caption)

        # ================================================================
        # EVENT 1 : fork & templates
        # ================================================================
        self.mark_event("event_1_fork")

        parental = make_duplex(FORK_X + 0.05, PARENT_Y, 6.0)
        self.add(parental)

        upper_pts = [(-5.8, UPPER_Y + 0.05, 0),
                     (FORK_X, UPPER_Y, 0),
                     (5.9, UPPER_Y - 0.05, 0)]
        template_leading = make_polyline(upper_pts, "#4FC3F7", stroke_width=7)
        self.register_object("template_leading", template_leading,
                             role="molecule", strand="template",
                             polarity="3to5")
        self.add(template_leading)

        lower_pts = [(-5.8, LOWER_Y - 0.05, 0),
                     (FORK_X, LOWER_Y, 0),
                     (5.9, LOWER_Y + 0.05, 0)]
        template_lagging = make_polyline(lower_pts, "#4FC3F7", stroke_width=7)
        self.register_object("template_lagging", template_lagging,
                             role="molecule", strand="template",
                             polarity="5to3")
        self.add(template_lagging)

        fork_line = Line([FORK_X, UPPER_Y, 0], [FORK_X, LOWER_Y, 0],
                         color="#4FC3F7", stroke_width=3)
        fork_grp = VGroup(fork_line)
        self.register_object("replication_fork", fork_grp, role="anchor")
        self.add(fork_grp)

        end_labels = VGroup(
            small_label("3'", [-5.9, UPPER_Y + 0.32, 0], "#4FC3F7", 15),
            small_label("5'", [5.9, UPPER_Y + 0.32, 0], "#4FC3F7", 15),
            small_label("5'", [-5.9, LOWER_Y - 0.32, 0], "#4FC3F7", 15),
            small_label("3'", [5.9, LOWER_Y - 0.32, 0], "#4FC3F7", 15),
        )
        self.add(end_labels)

        self.play(FadeIn(template_leading), FadeIn(template_lagging),
                  FadeIn(parental), FadeIn(fork_grp), FadeIn(end_labels),
                  run_time=1.2)
        self.wait(0.4)  # 1.6

        # ================================================================
        # EVENT 2 : priming (leading primer near fork)
        # ================================================================
        self.mark_event("event_2_priming")
        new_cap = Text("Primase makes an RNA starting point",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.12)
        self.play(Transform(caption, new_cap), run_time=0.3)  # 1.9

        primase_body = try_load(
            "primase",
            lambda: Circle(radius=0.28, color="#BA68C8").set_fill("#BA68C8", 0.85),
            width=0.6)
        primase_body.move_to([-1.2, UPPER_Y + 0.55, 0])
        primase_lbl = Text("Primase", font_size=16, color="#BA68C8")
        primase_lbl.next_to(primase_body, UP, buff=0.05)
        self.register_object("primase", primase_body, role="molecule",
                             enzyme="primase")
        self.add(primase_body, primase_lbl)
        self.play(FadeIn(primase_body), FadeIn(primase_lbl),
                  run_time=0.4)  # 2.3

        primer_x_start = -1.4
        primer_total_len = 0.75
        nseg = 4
        primer_children = []
        for i in range(nseg):
            x0 = primer_x_start + primer_total_len * i / nseg
            x1 = primer_x_start + primer_total_len * (i + 1) / nseg
            block = make_block([(x0 + x1) / 2, PRIMER_Y_TOP, 0],
                               (x1 - x0) * 0.9, 0.14,
                               "#FFB74D", "#E65100")
            self.register_object(f"rna_primer_lead_{i:02d}", block,
                                 role="nucleotide", strand="leading",
                                 material="RNA", fragment="leading")
            primer_children.append(block)
            self.add(block)
            self.play(Create(block), run_time=0.22)  # 4 blocks → 0.88 → 3.18

        rna_primer = VGroup(*primer_children)
        self.register_object("rna_primer", rna_primer, role="molecule",
                             material="RNA", strand="leading")

        lbl_p3 = small_label("3'",
                             [primer_x_start + primer_total_len + 0.22,
                              PRIMER_Y_TOP + 0.28, 0], "#FFB74D", 16)
        self.add(lbl_p3)
        self.play(FadeIn(lbl_p3), run_time=0.2)  # 3.38

        self.play(FadeOut(primase_body), FadeOut(primase_lbl),
                  run_time=0.4)  # 3.78

        # ================================================================
        # EVENT 3 : leading extension
        # ================================================================
        self.mark_event("event_3_extension")
        new_cap = Text("DNA polymerase extends 5' to 3'",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.12)
        self.play(Transform(caption, new_cap), run_time=0.35)  # 4.13

        pol_lead = try_load(
            "dna_polymerase",
            lambda: RegularPolygon(6, radius=0.32, color="#4DD0E1")
                    .set_fill("#4DD0E1", 0.85),
            width=0.7)
        pol_lead_lbl = Text("Pol δ", font_size=16, color="#4DD0E1")

        lead_anchor = Dot([primer_x_start + primer_total_len,
                           PRIMER_Y_TOP, 0], radius=0.04, color=RED)
        lead_anchor.set_opacity(0)
        self.register_object("lead_active_anchor", lead_anchor, role="anchor")
        self.add(lead_anchor)

        pol_lead.move_to([primer_x_start + primer_total_len + 0.35,
                          PRIMER_Y_TOP - 0.55, 0])
        pol_lead_lbl.next_to(pol_lead, DOWN, buff=0.03)
        self.register_object("dna_polymerase_leading", pol_lead,
                             role="molecule", enzyme="polymerase",
                             strand="leading")
        self.add(pol_lead, pol_lead_lbl)
        self.play(FadeIn(pol_lead), FadeIn(pol_lead_lbl),
                  run_time=0.4)  # 4.53
        self.bind_near("dna_polymerase_leading", "lead_active_anchor",
                       offset=(0.3, -0.55, 0), max_distance=0.8)

        # incoming nucleotide glyph
        inc = try_load(
            "nucleotide",
            lambda: Square(0.22, color="#69F0AE").set_fill("#69F0AE", 0.9),
            width=0.28)
        inc_lbl = Text("dNTP", font_size=14, color="#69F0AE")
        self.register_object("incoming_nucleotide", inc, role="molecule",
                             material="DNA", strand="leading")
        inc.move_to([primer_x_start + primer_total_len + 0.2,
                     PRIMER_Y_TOP + 0.5, 0])
        inc_lbl.next_to(inc, UP, buff=0.03)
        self.add(inc, inc_lbl)

        lead_children = []
        start_x = primer_x_start + primer_total_len
        step = 0.35
        end_x = 4.9
        n_lead = int((end_x - start_x) / step)
        for i in range(n_lead):
            x0 = start_x + i * step
            xc = x0 + step / 2
            nuc = make_block([xc, PRIMER_Y_TOP, 0],
                             step * 0.9, 0.14, "#69F0AE", "#1B5E20")
            self.register_object(f"nucleotide_leading_{i:02d}", nuc,
                                 role="nucleotide", strand="leading",
                                 fragment="leading", material="DNA")
            inc.move_to([xc, PRIMER_Y_TOP + 0.5, 0])
            inc_lbl.next_to(inc, UP, buff=0.03)
            lead_anchor.move_to([x0 + step, PRIMER_Y_TOP, 0])
            self.play(FadeIn(nuc, shift=DOWN * 0.06), run_time=0.16)
            self.add(nuc)
            lead_children.append(nuc)

        new_leading = VGroup(*lead_children)
        self.register_object("new_leading_strand", new_leading,
                             role="molecule", strand="leading",
                             material="DNA")

        self.play(FadeOut(inc), FadeOut(inc_lbl),
                  run_time=0.2)  # n_lead=11 → 1.76 → 4.53+1.76+0.2=6.49

        lbl_lead3 = small_label("3'", [end_x + 0.22, PRIMER_Y_TOP + 0.28, 0],
                                "#69F0AE", 16)
        self.add(lbl_lead3)

        # ================================================================
        # EVENT 4 : two modes
        # ================================================================
        self.mark_event("event_4_two_modes")
        new_cap = Text("Continuous leading; short lagging fragments",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.12)
        self.play(Transform(caption, new_cap), run_time=0.35)  # 6.84

        # --- lagging fragment 1 primer (near fork) ---
        lag1_primer_start = 2.0
        lag1_primer_len = 0.55
        nsegp = 3
        lag1_primer_children = []
        for i in range(nsegp):
            x0 = lag1_primer_start + lag1_primer_len * i / nsegp
            x1 = lag1_primer_start + lag1_primer_len * (i + 1) / nsegp
            blk = make_block([(x0 + x1) / 2, LAG_Y, 0],
                             (x1 - x0) * 0.9, 0.13,
                             "#FFB74D", "#E65100")
            self.register_object(f"rna_primer_lagging_1_{i:02d}", blk,
                                 role="nucleotide", strand="lagging",
                                 material="RNA", fragment="okazaki_1")
            lag1_primer_children.append(blk)
            self.add(blk)
        rna_primer_1 = VGroup(*lag1_primer_children)
        self.register_object("rna_primer_lagging_1", rna_primer_1,
                             role="molecule", material="RNA", strand="lagging")

        primase2 = try_load(
            "primase",
            lambda: Circle(radius=0.24, color="#BA68C8").set_fill("#BA68C8", 0.85),
            width=0.5)
        primase2.move_to([lag1_primer_start + lag1_primer_len / 2,
                          LAG_Y - 0.48, 0])
        pl2 = Text("Primase", font_size=14, color="#BA68C8")
        pl2.next_to(primase2, DOWN, buff=0.03)
        self.play(FadeIn(primase2), FadeIn(pl2), run_time=0.25)  # 7.09
        for b in lag1_primer_children:
            self.play(Create(b), run_time=0.1)  # 0.3 → 7.39
        self.play(FadeOut(primase2), FadeOut(pl2), run_time=0.25)  # 7.64

        # lagging polymerase 1
        lag1_anchor = Dot([lag1_primer_start, LAG_Y, 0],
                          radius=0.04, color=RED)
        lag1_anchor.set_opacity(0)
        self.register_object("lag1_active_anchor", lag1_anchor, role="anchor")
        self.add(lag1_anchor)

        pol_lag1 = try_load(
            "dna_polymerase",
            lambda: RegularPolygon(6, radius=0.28, color="#4DD0E1")
                    .set_fill("#4DD0E1", 0.85),
            width=0.6)
        pol_lag1_lbl = Text("Pol δ", font_size=14, color="#4DD0E1")
        pol_lag1.move_to([lag1_primer_start - 0.35, LAG_Y + 0.55, 0])
        pol_lag1_lbl.next_to(pol_lag1, UP, buff=0.03)
        self.register_object("dna_polymerase_lagging", pol_lag1,
                             role="molecule", enzyme="polymerase",
                             strand="lagging")
        self.add(pol_lag1, pol_lag1_lbl)
        self.play(FadeIn(pol_lag1), FadeIn(pol_lag1_lbl),
                  run_time=0.25)  # 7.89
        self.bind_near("dna_polymerase_lagging", "lag1_active_anchor",
                       offset=(-0.3, 0.55, 0), max_distance=0.8)

        frag1_children = []
        step_lag = 0.28
        n_frag1 = 4
        for i in range(n_frag1):
            xc = lag1_primer_start - (i + 1) * step_lag + step_lag / 2
            blk = make_block([xc, LAG_Y, 0],
                             step_lag * 0.85, 0.13, "#69F0AE", "#1B5E20")
            self.register_object(f"okazaki_fragment_1_{i:02d}", blk,
                                 role="nucleotide", strand="lagging",
                                 fragment="okazaki_1", material="DNA")
            lag1_anchor.move_to([lag1_primer_start - (i + 1) * step_lag,
                                 LAG_Y, 0])
            self.play(FadeIn(blk), run_time=0.14)  # 4×0.14=0.56 → 8.45
            self.add(blk)
            frag1_children.append(blk)

        okazaki_fragment_1 = VGroup(*frag1_children)
        self.register_object("okazaki_fragment", okazaki_fragment_1,
                             role="molecule", strand="lagging",
                             fragment="okazaki_1", material="DNA")
        self.play(FadeOut(pol_lag1), FadeOut(pol_lag1_lbl),
                  run_time=0.25)  # 8.70

        # --- lagging fragment 2 primer (nearer fork) ---
        lag2_primer_start = 3.7
        lag2_primer_len = 0.45
        lag2_primer_children = []
        for i in range(nsegp):
            x0 = lag2_primer_start + lag2_primer_len * i / nsegp
            x1 = lag2_primer_start + lag2_primer_len * (i + 1) / nsegp
            blk = make_block([(x0 + x1) / 2, LAG_Y, 0],
                             (x1 - x0) * 0.9, 0.13,
                             "#FFB74D", "#E65100")
            self.register_object(f"rna_primer_lagging_2_{i:02d}", blk,
                                 role="nucleotide", strand="lagging",
                                 material="RNA", fragment="okazaki_2")
            lag2_primer_children.append(blk)
            self.add(blk)
        rna_primer_2 = VGroup(*lag2_primer_children)
        self.register_object("rna_primer_lagging_2", rna_primer_2,
                             role="molecule", material="RNA", strand="lagging")
        self.play(FadeIn(rna_primer_2), run_time=0.25)  # 8.95

        lag2_anchor = Dot([lag2_primer_start, LAG_Y, 0],
                          radius=0.04, color=RED)
        lag2_anchor.set_opacity(0)
        self.register_object("lag2_active_anchor", lag2_anchor, role="anchor")
        self.add(lag2_anchor)

        pol_lag2 = try_load(
            "dna_polymerase",
            lambda: RegularPolygon(6, radius=0.26, color="#4DD0E1")
                    .set_fill("#4DD0E1", 0.85),
            width=0.55)
        pol_lag2_lbl = Text("Pol δ", font_size=13, color="#4DD0E1")
        pol_lag2.move_to([lag2_primer_start - 0.32, LAG_Y + 0.55, 0])
        pol_lag2_lbl.next_to(pol_lag2, UP, buff=0.03)
        self.register_object("dna_polymerase_lagging_2", pol_lag2,
                             role="molecule", enzyme="polymerase",
                             strand="lagging")
        self.add(pol_lag2, pol_lag2_lbl)
        self.play(FadeIn(pol_lag2), FadeIn(pol_lag2_lbl),
                  run_time=0.22)  # 9.17
        self.bind_near("dna_polymerase_lagging_2", "lag2_active_anchor",
                       offset=(-0.3, 0.55, 0), max_distance=0.8)

        frag2_children = []
        n_frag2 = 3
        for i in range(n_frag2):
            xc = lag2_primer_start - (i + 1) * step_lag + step_lag / 2
            blk = make_block([xc, LAG_Y, 0],
                             step_lag * 0.85, 0.13, "#69F0AE", "#1B5E20")
            self.register_object(f"okazaki_fragment_2_{i:02d}", blk,
                                 role="nucleotide", strand="lagging",
                                 fragment="okazaki_2", material="DNA")
            lag2_anchor.move_to([lag2_primer_start - (i + 1) * step_lag,
                                 LAG_Y, 0])
            self.play(FadeIn(blk), run_time=0.14)  # 3×0.14=0.42 → 9.59
            self.add(blk)
            frag2_children.append(blk)

        okazaki_fragment_2 = VGroup(*frag2_children)
        self.register_object("okazaki_fragment_2", okazaki_fragment_2,
                             role="molecule", strand="lagging",
                             fragment="okazaki_2", material="DNA")

        new_lagging = VGroup(rna_primer_1, okazaki_fragment_1,
                             rna_primer_2, okazaki_fragment_2)
        self.register_object("new_lagging_strand", new_lagging,
                             role="molecule", strand="lagging",
                             material="mixed")

        self.play(FadeOut(pol_lag2), FadeOut(pol_lag2_lbl),
                  run_time=0.25)  # 9.84

        lbl_lag3 = small_label("3'",
                               [lag1_primer_start - n_frag1 * step_lag - 0.22,
                                LAG_Y - 0.28, 0], "#69F0AE", 15)
        self.add(lbl_lag3)

        # ================================================================
        # EVENT 5 : maturation
        # ================================================================
        self.mark_event("event_5_maturation")
        new_cap = Text("Remove RNA, fill DNA, then seal a nick",
                       font_size=20, color=YELLOW).to_edge(DOWN, buff=0.12)
        self.play(Transform(caption, new_cap), run_time=0.35)  # 10.19

        # Step 1: remove RNA primer 1, leave gap
        self.play(
            *[FadeOut(c) for c in lag1_primer_children],
            run_time=0.4
        )  # 10.59

        gap_label = Text("gap", font_size=15, color="#FFB74D")
        gap_label.move_to([lag1_primer_start + lag1_primer_len / 2,
                           LAG_Y + 0.35, 0])
        self.add(gap_label)
        self.play(FadeIn(gap_label), run_time=0.2)  # 10.79
        self.wait(0.2)  # 10.99

        # Step 2: polymerase fills gap with fresh DNA nucleotides
        n_fill = 3
        fill_step = lag1_primer_len / n_fill

        pol_fill = try_load(
            "dna_polymerase",
            lambda: RegularPolygon(6, radius=0.26, color="#4DD0E1")
                    .set_fill("#4DD0E1", 0.85),
            width=0.55)
        pol_fill_lbl = Text("Pol δ", font_size=13, color="#4DD0E1")
        pol_fill.move_to([lag1_primer_start + lag1_primer_len / 2,
                          LAG_Y + 0.55, 0])
        pol_fill_lbl.next_to(pol_fill, UP, buff=0.03)
        self.register_object("dna_polymerase_fill", pol_fill,
                             role="molecule", enzyme="polymerase",
                             strand="lagging")
        self.add(pol_fill, pol_fill_lbl)
        self.play(FadeIn(pol_fill), FadeIn(pol_fill_lbl),
                  run_time=0.25)  # 11.24

        fill_children = []
        for i in range(n_fill):
            x0 = lag1_primer_start + i * fill_step
            x1 = lag1_primer_start + (i + 1) * fill_step
            blk = make_block([(x0 + x1) / 2, LAG_Y, 0],
                             fill_step * 0.85, 0.13, "#69F0AE", "#1B5E20")
            self.register_object(f"fill_dna_{i:02d}", blk,
                                 role="nucleotide", strand="lagging",
                                 fragment="okazaki_1", material="DNA")
            self.play(FadeIn(blk), run_time=0.18)  # 3×0.18=0.54 → 11.78
            self.add(blk)
            fill_children.append(blk)

        self.play(FadeOut(gap_label), FadeOut(pol_fill),
                  FadeOut(pol_fill_lbl), run_time=0.25)  # 12.03

        # Step 3: ligase seals a tiny nick (does not synthesize)
        nick_x = lag1_primer_start + lag1_primer_len
        nick_marker = Line([nick_x, LAG_Y - 0.1, 0],
                           [nick_x, LAG_Y + 0.1, 0],
                           color=RED, stroke_width=3)
        self.add(nick_marker)
        self.play(Create(nick_marker), run_time=0.2)  # 12.23

        ligase = try_load(
            "dna_ligase",
            lambda: RegularPolygon(5, radius=0.22, color="#FFD54F")
                    .set_fill("#FFD54F", 0.85),
            width=0.5)
        ligase_lbl = Text("Ligase", font_size=14, color="#FFD54F")
        ligase.move_to([nick_x, LAG_Y + 0.55, 0])
        ligase_lbl.next_to(ligase, UP, buff=0.03)
        self.register_object("dna_ligase", ligase, role="molecule",
                             enzyme="ligase")
        self.add(ligase, ligase_lbl)
        self.play(FadeIn(ligase), FadeIn(ligase_lbl),
                  run_time=0.25)  # 12.48

        seal = Line([nick_x - 0.04, LAG_Y, 0],
                    [nick_x + 0.04, LAG_Y, 0],
                    color="#69F0AE", stroke_width=8)
        self.play(Transform(nick_marker, seal), run_time=0.4)  # 12.88

        self.play(FadeOut(ligase), FadeOut(ligase_lbl),
                  run_time=0.25)  # 13.13

        final_cap = Text("Local copied duplexes", font_size=20,
                         color=YELLOW).to_edge(DOWN, buff=0.12)
        self.play(Transform(caption, final_cap), run_time=0.3)  # 13.43
        self.wait(0.6)  # 14.03

        # NOTE: timing tracker is scene-managed; verify total ≈ 30 s budget
        return

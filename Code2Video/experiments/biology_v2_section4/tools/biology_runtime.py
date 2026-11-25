"""Reusable scene instrumentation and SVG loading; contains no lesson animation."""
from manim import *
import json
from pathlib import Path


class BiologyScene(Scene):
    def setup(self):
        self.always_update_mobjects = True
        self.objects = {}
        self.object_meta = {}
        self.bindings = []
        self._binding_updaters = {}
        self.observations = []
        self.events = []
        self._sample_clock = 0.0

    def register_object(self, object_id, mobject, role="molecule", **metadata):
        if object_id in self.objects:
            raise ValueError("Duplicate object ID: " + object_id)
        self.objects[object_id] = mobject
        self.object_meta[object_id] = {"role": role, **metadata}
        return mobject

    def bind_near(self, object_id, target_id, offset=(0, 0, 0), max_distance=0.8):
        obj, target = self.objects[object_id], self.objects[target_id]
        offset = np.array(offset, dtype=float)
        old = self._binding_updaters.get(object_id)
        if old is not None:
            obj.remove_updater(old)
        updater = lambda mob: mob.move_to(target.get_center() + offset)
        obj.move_to(target.get_center() + offset)
        obj.add_updater(updater)
        self._binding_updaters[object_id] = updater
        self.bindings = [b for b in self.bindings if b['object_id'] != object_id]
        self.bindings.append({"object_id": object_id, "target_id": target_id,
                              "offset": offset.tolist(), "max_distance": max_distance})

    def mark_event(self, event_id):
        self.events.append({"id": event_id, "time": float(self.time)})
        self.capture_geometry()

    def capture_geometry(self):
        present = {id(m) for top in self.mobjects for m in top.get_family()}
        data = {}
        for name, mob in self.objects.items():
            points = mob.get_all_points()
            if len(points):
                lo, hi = points.min(axis=0), points.max(axis=0)
            else:
                lo = hi = mob.get_center()
            # Presence and opacity are measured, rather than inferred from model narration.
            opacity = 0.0
            for part in mob.get_family():
                try:
                    opacity = max(opacity, float(part.get_fill_opacity()), float(part.get_stroke_opacity()))
                except (AttributeError, TypeError, ValueError):
                    pass
            data[name] = {"center": mob.get_center().tolist(), "bbox": [lo.tolist(), hi.tolist()],
                          "visible": bool(any(id(part) in present for part in mob.get_family()) and opacity > .05),
                          **self.object_meta[name]}
        self.observations.append({"time": float(self.time), "objects": data,
                                  "bindings": [dict(b) for b in self.bindings]})

    def update_mobjects(self, dt):
        super().update_mobjects(dt)
        self._sample_clock += dt
        if self._sample_clock >= .20:
            self._sample_clock = 0
            self.capture_geometry()

    def tear_down(self):
        self.capture_geometry()
        Path("geometry_trace.json").write_text(json.dumps({"frames": self.observations,
            "events": self.events, "bindings": self.bindings, "object_metadata": self.object_meta}, indent=2))
        super().tear_down()


def load_bio_asset(asset_id, width=0.7):
    registry = json.loads(Path("assets/asset_registry.json").read_text())
    item = next(x for x in registry["assets"] if x["id"] == asset_id)
    return SVGMobject(str(Path("assets") / item["filename"])).set_width(width)


class HistoryScene(BiologyScene):
    """Instrumentation base for replaying historical source without changing animation."""
    def observe_historical(self, name, mobject):
        self.objects[name] = mobject
        self.object_meta[name] = {"role": "historical"}

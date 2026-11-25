from manim import VMobject,Transform
import numpy as np,json
results=[]
for fill in [None,0]:
 a=VMobject(color='#4FC3F7',stroke_width=5);a.set_points_as_corners([[-5,.15,0],[2.5,.15,0],[6,.15,0]])
 b=VMobject(color='#4FC3F7',stroke_width=5);b.set_points_as_corners([[-5,1.2,0],[2.5,.15,0],[6,.15,0]])
 if fill is not None:a.set_fill(opacity=fill);b.set_fill(opacity=fill)
 a.set_opacity(1);b.set_opacity(1)
 if fill is not None:a.set_fill(opacity=fill);b.set_fill(opacity=fill)
 animation=Transform(a,b);animation.begin()
 for alpha in [0,.25,.5,.75,1]:
  animation.interpolate(alpha)
  results.append({'explicit_fill':fill,'alpha':alpha,'fill_opacity':float(a.get_fill_opacity()),'stroke_width':float(a.get_stroke_width()),'closed':bool(np.allclose(a.get_start(),a.get_end())),'points':a.get_points().tolist()})
print(json.dumps(results,indent=2))

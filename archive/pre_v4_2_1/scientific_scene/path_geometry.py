"""Topic-independent unfilled paths, stable identity and continuous progress."""
from manim import VMobject,Animation
import numpy as np
class PathGeometry(VMobject):
 def __init__(self,points,mode='polyline',**kwargs):
  kwargs['fill_opacity']=0
  super().__init__(**kwargs);self.path_mode=mode;self.set_path(points,mode)
 def set_path(self,points,mode=None):
  self.control_points=np.array(points,dtype=float);self.path_mode=mode or self.path_mode
  self.clear_points()
  if self.path_mode=='curve':self.set_points_smoothly(self.control_points)
  else:self.set_points_as_corners(self.control_points)
  self.set_fill(opacity=0);return self
 def set_opacity(self,opacity,family=True):
  super().set_opacity(opacity,family=family);self.set_fill(opacity=0);return self
 def get_path_anchor(self,spec):
  if spec['kind']=='point':return self.control_points[spec['index']]
  if spec['kind']=='between':return (1-spec['alpha'])*self.control_points[spec['a']]+spec['alpha']*self.control_points[spec['b']]
  return self.get_center()
 def put_start_and_end_on(self,start,end):
  return self.set_path([start,end])

class PathMorph(Animation):
 def __init__(self,mobject,target_points,target_mode=None,**kwargs):
  self.start_controls=mobject.control_points.copy();self.target_controls=np.array(target_points,dtype=float);self.target_mode=target_mode or mobject.path_mode
  if len(self.start_controls)!=len(self.target_controls):
   def resample(p,n):
    at=np.linspace(0,len(p)-1,n);return np.array([p[int(t)]*(1-(t-int(t)))+p[min(int(t)+1,len(p)-1)]*(t-int(t)) for t in at])
   n=max(len(self.start_controls),len(self.target_controls));self.start_controls=resample(self.start_controls,n);self.target_controls=resample(self.target_controls,n)
  super().__init__(mobject,**kwargs)
 def interpolate_mobject(self,alpha):
  self.mobject.set_path((1-alpha)*self.start_controls+alpha*self.target_controls,self.target_mode)

class ProgressDrivenTransition:
 """Progress evolves only declared geometry. Rules may inspect every sampled state."""
 def __init__(self,start,end,invariants=()):self.start=np.array(start,dtype=float);self.end=np.array(end,dtype=float);self.invariants=invariants
 def at(self,progress):
  if not 0<=progress<=1:raise ValueError('Progress outside [0,1]')
  state=(1-progress)*self.start+progress*self.end
  if not all(rule(state) for rule in self.invariants):raise ValueError('Continuous invariant rejected')
  return state

"""Render only bounded, declarative slide data inside the existing sandbox."""
from pathlib import Path
import json
from manim import *

def fitted(value,size,width,color=WHITE):
    obj=Text(value,font_size=size,color=color)
    if obj.width>width: obj.scale_to_fit_width(width)
    return obj

class Lesson(Scene):
    def construct(self):
        scene=json.loads(Path('scene.json').read_text())
        self.camera.background_color='#11263B'
        title=fitted(scene['title'],38,12).move_to([0,3.2,0])
        caption=fitted(scene['caption'],27,12.8).move_to([0,-3.15,0])
        objects=[]
        for item in scene['objects']:
            pts=[[x,y,0] for x,y in item['points']]
            shape=VMobject(color=item['color'],stroke_width=4)
            if item['closed']:
                shape.set_points_as_corners(pts+[pts[0]]).set_fill(item['color'],opacity=.45)
            else:
                shape.set_points_smoothly(pts)
            off=item.get('label_offset',[0,.38])
            label=fitted(item['label'],19,2.8).move_to(shape.get_center()+[off[0],off[1],0]) if item['label'] else VMobject()
            objects.append(VGroup(shape,label))
        self.add(title,caption,*objects)
        seconds=scene['duration']
        self.wait(seconds*.15)
        trace=[]
        for group,item in zip(objects,scene['objects']):
            trace.append({'id':item['id'],'start':group[0].get_center().tolist()})
        self.play(*[group.animate.shift([*item['shift'],0]) for group,item in zip(objects,scene['objects'])],run_time=seconds*.65,rate_func=smooth)
        self.wait(seconds*.20)
        for rec,group in zip(trace,objects):rec['end']=group[0].get_center().tolist()
        Path('trace.json').write_text(json.dumps({'objects':trace,'actual_end_time':self.time}))

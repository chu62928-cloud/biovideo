import sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import run as d, motion as m
for label,g in [('B2_fork_motion',m.motion_graph()),('B3_mechanism_fix',m.integrated_graph())]:
 folder=d.E/'groups'/label
 archive=folder/'superseded_preintegration'
 archive.mkdir(exist_ok=True)
 for name in ['status.json','scene_graph.json','video.mp4','geometry_trace.json','validation_report.json']:
  if (folder/name).exists():shutil.copy2(folder/name,archive/name)
 result=d.render(label,g,tag='continuous_integrated')
 assert result['render_success'],result

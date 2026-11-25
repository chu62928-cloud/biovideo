from pathlib import Path
import hashlib,ast
def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def label_origin(label,stage_artifacts):
 """Earliest available artifact containing a concrete label; missing stages retain uncertainty."""
 normalized=''.join(label.lower().split())
 matches=[stage for stage,text in stage_artifacts if normalized in ''.join(str(text).lower().split())]
 return {'label':label,'first_observed_stage':matches[0] if matches else None,'searched_stages':[s for s,t in stage_artifacts],'unobserved_stages_are_unknown':True}

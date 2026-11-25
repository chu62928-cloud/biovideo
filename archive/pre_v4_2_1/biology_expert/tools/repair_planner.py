"""Root-cause routing and an AST-bounded Coder adapter; never writes a lesson by hand."""
from pathlib import Path
import ast,json,uuid,shutil
from ..state import write,digest
from ..schemas import validate
def plan_repair(review_result,context):
 issues=[i for i in review_result['issues'] if i['severity'] in ['blocker','major']]
 if not issues:return {'decision':'NEEDS_HUMAN_REVIEW','reason':'No located actionable scientific issue'}
 issue=next((i for i in issues if i['issue_id']=='BIO-DIRECTION'),issues[0])
 root=issue['root_cause_stage']
 task={'repair_id':'REP-'+uuid.uuid4().hex[:12],'issue_id':issue['issue_id'],'decision':'REVISE','category':issue['category'],'severity':issue['severity'],'root_cause_stage':root,'scene_id':'section4','object_ids':issue['object_ids'],'repair_scope':issue['suggested_repair_scope'],'instruction':issue['description'],'preserve':['approved_script','asset_identity','unaffected_events','non_target_AST'],'verification':['source_diff_scope','strand_polarity_check','growth_trace_check','rendered_video_review'],'invalidate':['CODE_GATE','RENDER','VIDEO_SCIENCE_GATE','VISUAL_CRITIC','FINAL_SCIENCE_GATE','APPROVED'],'source_review_id':review_result['review_id'],'input_hash':context['input_hash'],'event_id':issue.get('artifact_evidence',{}).get('check',{}).get('event_id')}
 if issue['issue_id']=='BIO-DIRECTION':
  task['instruction']='Repair ONLY event_5_maturation gap-fill nucleotide addition so actual visible addition progresses from the existing nascent 3prime side, consistent with the observed antiparallel lower template and 5prime-to-3prime synthesis. Change the n_fill loop, not arrows, glyphs or molecular identities. Keep removal before polymerase fill and nick sealing afterwards. Move the actual gap polymerase along with new nucleotides. Preserve all other events, IDs, SVGs, time budget, imports and helpers.'
 if root in ['SCRIPT','CAST','ASSETS','STORYBOARD']:
  ordered=['SCRIPT_GATE','CAST_ASSET_GATE','STORYBOARD_GATE','CODE_GATE','RENDER','VIDEO_SCIENCE_GATE','VISUAL_CRITIC','FINAL_SCIENCE_GATE','APPROVED']
  begin={'SCRIPT':0,'CAST':1,'ASSETS':1,'STORYBOARD':2}[root];task['invalidate']=ordered[begin:]
 validate('repair_task',task);return task
def bounded_patch(code,reply):
 import re,textwrap
 match=re.search(r'\x60\x60\x60(?:python)?[^\S\r\n]*\r?\n([\s\S]*?)\x60\x60\x60',reply)
 text=textwrap.dedent(match.group(1) if match else reply).strip()
 incoming=ast.parse(text);tree=ast.parse(code)
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Section4Scene')
 fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='construct')
 targets=[(i,n) for i,n in enumerate(fn.body) if isinstance(n,ast.For) and any(isinstance(s,ast.Constant) and isinstance(s.value,str) and s.value.startswith('fill_dna_') for s in ast.walk(n))]
 if len(targets)!=1:raise ValueError('Unique original gap-fill loop not found')
 if len(incoming.body)==1 and isinstance(incoming.body[0],ast.For):new=incoming.body[0]
 else:
  loops=[n for n in ast.walk(incoming) if isinstance(n,ast.For) and any(isinstance(s,ast.Constant) and isinstance(s.value,str) and s.value.startswith('fill_dna_') for s in ast.walk(n))]
  if len(loops)!=1:raise ValueError('No unique generated replacement gap-fill loop')
  new=loops[0]
 old_index,old=targets[0]
 if ast.dump(new.target)!=ast.dump(old.target) or ast.dump(new.iter)!=ast.dump(old.iter):raise ValueError('Loop index/iteration count changed')
 forbidden={'mark_event','bind_near','add_updater','remove','clear','clear_updaters'}
 if any(isinstance(n,ast.Attribute) and n.attr in forbidden for n in ast.walk(new)):raise ValueError('Replacement attempts to alter unrelated state')
 fn.body[old_index]=new
 patched=ast.unparse(ast.fix_missing_locations(tree))+'\n'
 # All other code is structurally identical. This is scope enforcement, not an animation edit.
 baseline=ast.parse(code);replacement=ast.parse(patched)
 def strip(t):
  c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Section4Scene')
  f=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='construct')
  f.body[old_index]=ast.Pass()
  return ast.dump(t,include_attributes=False)
 assert strip(baseline)==strip(replacement),'Non-target AST was changed'
 return patched,{'only_target_loop_changed':True,'original_loop_line':old.lineno,'manual_animation_code':False}
class CoderAdapter:
 def __init__(self,gateway):self.gateway=gateway
 def generate(self,task,code):
  prompt="""You are the existing Code2Video DeepSeek Coder. Execute the scientific Repair Task with the smallest possible change. Return ONLY a complete replacement 'for i in range(n_fill):' loop in a Python code fence. This replaces the existing unique loop that registers fill_dna_XX.
Do not return a module, class or construct. Keep all existing register_object IDs, role/strand/material metadata, FadeIn duration, self.add and fill_children append calls. Keep all other events and code outside this loop unchanged.
Use the CURRENT actual variable names. The lower blue TEMPLATE has 5prime at left and 3prime at right, so newly filled lower nascent DNA must grow toward the LEFT. Within the existing RNA-removed gap [lag1_primer_start, lag1_primer_start+lag1_primer_len], add fill_dna_00 at the RIGHTMOST segment, then 01 then 02 successively LEFT. Calculate segment endpoints accordingly; do not reverse visible labels or just arrows.
During each addition move pol_fill adjacent to that segment (above the strand, roughly0.55 scene units), using existing Mobject methods; keep labels following appropriately. Do not add new imports or access file/network/processes.
Task:\n"""+json.dumps(task,ensure_ascii=False)+'\nCURRENT VERIFIED MODULE:\n'+code
  return self.gateway.request('deepseek','scientific_event5_repair',prompt)

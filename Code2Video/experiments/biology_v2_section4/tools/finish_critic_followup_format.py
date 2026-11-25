from pathlib import Path
import ast,json,sys,shutil
T=Path('/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4/tools')
sys.path.insert(0,str(T))
import run_biology_v2 as b
from biology_v2_pipeline import TransactionRenderer,replace_construct
E=b.E;g=E/'groups/A3_critic_followup_two_rounds';d=g/'round_2'
tx=TransactionRenderer(g,b.RUNTIME,E/'assets',(25,35))
before=tx.state();old=Path(before['code']).read_text();raw=(d/'model_function.py').read_text()
oldtree=ast.parse(old);newtree=ast.parse(raw)
def outside(tree):
 parts=[]
 for node in tree.body:
  if isinstance(node,ast.ClassDef) and node.name=='Section4Scene':
   cp=ast.ClassDef(name=node.name,bases=node.bases,keywords=node.keywords,body=[n for n in node.body if not(isinstance(n,ast.FunctionDef) and n.name=='construct')],decorator_list=node.decorator_list)
   parts.append(ast.dump(cp,include_attributes=False))
  else:parts.append(ast.dump(node,include_attributes=False))
 return parts
assert outside(oldtree)==outside(newtree),'Unexpected helper/import changes in model output'
cls=next(x for x in newtree.body if isinstance(x,ast.ClassDef) and x.name=='Section4Scene')
fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='construct')
function=ast.unparse(fn)+'\n'
(d/'extracted_model_function.py').write_text(function)
(d/'format_adaptation.json').write_text(json.dumps({'reason':'Model returned complete module instead of requested function','outside_construct_AST_identical':True,'action':'Extract only model-generated Section4Scene.construct; no authored animation changes','additional_API_calls':0},indent=2))
candidate=replace_construct(old,function);(d/'candidate_code.py').write_text(candidate)
# Same full-render and geometry gate, without importing the executable follow-up runner.
def validator(stage,trace,layout):
 b.validate(stage,trace,layout)
 assert not layout['out_of_frame'],'Out of frame'
 labels=[k for k,v in trace['object_metadata'].items() if v.get('role')=='label']
 assert len(labels)>=12
 first={}
 for f in trace['frames']:
  for key,obj in f['objects'].items():
   if key.startswith('fill_dna_') and obj.get('visible') and key not in first:first[key]={'time':f['time'],'x':obj['center'][0]}
 ordered=sorted(first.items(),key=lambda x:x[1]['time'])
 assert len(ordered)>=3 and all(a[1]['x']>z[1]['x'] for a,z in zip(ordered,ordered[1:])),'Gap fill direction'
 (stage/'followup_checks.json').write_text(json.dumps({'registered_labels':labels,'fill_first_visibility':ordered,'fill_direction_pass':True,'label_overlap_samples':len(layout['label_overlaps'])},indent=2))
result=tx.attempt(candidate,'critic_round_2',extra_validator=validator)
(d/'transaction.json').write_text(json.dumps(result,indent=2))
summary=json.loads((g/'summary.json').read_text());summary['format_exception_preserved']={k:summary.pop(k) for k in ['error_type','error'] if k in summary}
summary['rounds'].append({'round':2,'committed':result['committed'],'result':result,'issues':json.loads((d/'structured_feedback.json').read_text())['issues']})
summary['completed_rounds']=sum(r['committed'] for r in summary['rounds'])
summary['format_adaptation']='Extracted generated construct from returned module; unchanged helper/import AST; zero additional API'
if result['committed']:
 shutil.copy2(result['after']['video'],d/'video.mp4');shutil.copy2(result['after']['code'],d/'rendered_code.py')
(g/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print('ROUND2',result['committed'],result.get('error'),flush=True)

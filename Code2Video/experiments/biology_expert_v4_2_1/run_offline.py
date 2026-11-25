from pathlib import Path
import sys,json,hashlib,csv,subprocess
R=Path(__file__).resolve().parents[3];E=Path(__file__).parent
sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.contract_cli import audit
from biology_expert.contracts import write,digest
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--evidence-root',required=True);args=parser.parse_args();H=Path(args.evidence_root)
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
all_results=[];bindings={};checks={};mutations={};manifest=[];comparison=[]
for topic,label in [('dna_replication','B4_expert_repair'),('mitosis','M1_mitosis'),('protein_translation',None)]:
 folder=H/'biology_expert_v4_2/contracts'/topic;cp=folder/'scientific_contract.json';rp=folder/'contract_review.json';c=load(cp)
 sp=H/'scientific_scene_v4_1/groups'/label/'scene_graph.json' if label else folder/'generated_scene_graph.json'
 tp=sp.parent/'geometry_trace.json' if label else None;vp=sp.parent/'video.mp4' if label else None;reviewp=H/'biology_expert_v4_2/reviews/video_reviews'/(topic+'.json') if label else None
 scene=load(sp);trace=load(tp) if tp else {};review=load(reviewp) if reviewp else {}
 dest=E/'details'/topic;res=audit(c,scene,trace,dest,review,vp,'qwen3.8-27b',load(rp));res['topic']=topic
 res['static_structure_subchecks']=sum(len(x.get('static_subchecks',[])) for x in load(dest/'checks.json')['checks'])
 all_results.append(res);bindings[topic]=load(dest/'bindings.json');checks[topic]={'runtime':load(dest/'checks.json'),'semantic':load(dest/'semantic_observations.json'),'coverage':load(dest/'coverage.json')};mutations[topic]=load(dest/'mutations.json')
 for kind,p in [('contract',cp),('contract_review',rp),('scene',sp),('trace',tp),('video',vp),('vlm_review',reviewp)]:manifest.append({'topic':topic,'kind':kind,'path':str(p) if p else None,'sha256':sha(p) if p else None,'exists':p.exists() if p else False,'historical_v4_1':bool(label and kind in ['scene','trace','video']),'rerendered':False})
 oldcov=load(H/'biology_expert_v4_2/coverage'/({'dna_replication':'dna','mitosis':'mitosis','protein_translation':'translation'}[topic]+'_coverage.json'))
 res['coverage_before_measured']=oldcov['actual_observation_coverage'];res['coverage_after_measured']=checks[topic]['coverage']['actual_observation_coverage']
 for group in ['G0','G1','G2','G3','G4']:
  comparison.append({'group':group,'topic':topic,'roles_bound':res['roles_bound'] if group!='G0' else None,'runtime_checks_measured':res['runtime_checks_measured'] if group in ['G2','G3','G4'] else None,'vlm_checks_supported':res['vlm_checks_supported'] if group in ['G3','G4'] else None,'coverage_status':'REVIEW_INCOMPLETE','valid_mutations':res['scientific_mutations_valid'] if group=='G4' else None,'detected':res['scientific_mutations_detected'] if group=='G4' else None,'missed':mutations[topic]['missed'] if group=='G4' else None,'false_positives':mutations[topic]['false_positives'] if group=='G4' else None})
for name,value in [('results',{'experiment':'V4.2.1','topics':all_results,'paid_model_calls':0,'new_videos':0}),('bindings',bindings),('checks',checks),('mutations',mutations),('evidence_manifest',{'inputs':manifest,'loaded_module':str(__import__('biology_expert.contract_cli',fromlist=['x']).__file__),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'source_hashes':{str(p.relative_to(R)):sha(p) for p in (R/'Code2Video/src/biology_expert').glob('*.py')},'historical_inputs_unchanged':all((x['sha256']==sha(Path(x['path']))) for x in manifest if x['path']),'paid_model_calls':0})]:write(E/(name+'.json'),value)
with (E/'comparison.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(comparison[0]));w.writeheader();w.writerows(comparison)
print(json.dumps(all_results,ensure_ascii=False))

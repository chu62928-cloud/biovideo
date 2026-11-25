from pathlib import Path
import sys,json,copy,math
R=Path('/autodl-tmp/code2biovideo/Code2Video');E=R/'experiments/scientific_scene_v4_1';sys.path.insert(0,str(R/'src'))
from scientific_scene.scientific_review import *
from scientific_scene.models import write
g=json.loads((R/'experiments/scientific_scene_v4/groups/A2_scene_graph_fsm/scene_graph.json').read_text());p=json.loads((E/'knowledge/dna_replication/knowledge_pack.json').read_text())
verified={f['fact_id'] for f in p['facts'] if f.get('verification')=='VERIFIED'};facts=['X_7574276a','X_bf28604c']
results=[]
def check(name,fn):
 try:fn();results.append({'test':name,'passed':True})
 except Exception as e:results.append({'test':name,'passed':False,'error':str(e)})
def fixture(reverse=False):
 t={'object_id':'template','scientific_properties':{'endpoint_labels':{'start':"5'" if reverse else "3'",'end':"3'" if reverse else "5'"}},'visual_representation':{'points':[[-3,1,0],[3,1,0]]}}
 n={'object_id':'nascent','scientific_properties':{'endpoint_labels':{'start':"5'",'end':"3'"},'growth_port':'end'}}
 before=[[2,0,0],[1.9,0,0]] if reverse else [[-2,0,0],[-1.9,0,0]]
 after=[[2,0,0],[-1,0,0]] if reverse else [[-2,0,0],[1,0,0]]
 return t,n,before,after
def verdict(f):return polarity_check(*f,facts,verified)['status']
def expect(f,value):assert verdict(f)==value,(verdict(f),value)
check('template_3left_5right_growth_right',lambda:expect(fixture(), 'PASS'))
check('template_5left_3right_growth_left',lambda:expect(fixture(True),'PASS'))
def wrong():
 f=fixture();f[0]['scientific_properties']['endpoint_labels']={'start':"5'",'end':"3'"};expect(f,'FAIL')
check('wrong_template_polarity_rejected',wrong)
def wrong_end():
 f=fixture();f[1]['scientific_properties']['growth_port']='start';expect(f,'FAIL')
check('wrong_addition_end_rejected',wrong_end)
def rotated():
 for theta in [math.pi,.7,-1.2]:
  for rev in [False,True]:
   t,n,b,a=fixture(rev)
   rot=lambda q:[q[0]*math.cos(theta)-q[1]*math.sin(theta),q[0]*math.sin(theta)+q[1]*math.cos(theta),q[2]]
   t['visual_representation']['points']=[rot(q) for q in t['visual_representation']['points']]
   expect((t,n,[rot(q) for q in b],[rot(q) for q in a]),'PASS')
check('rotations_preserve_science',rotated)
def mirrored():
 t,n,b,a=fixture();flip=lambda q:[-q[0],q[1],q[2]];t['visual_representation']['points']=[flip(q) for q in t['visual_representation']['points']];expect((t,n,[flip(q) for q in b],[flip(q) for q in a]),'PASS')
check('mirror_preserves_science',mirrored)
def missing():
 f=fixture();f[1]['scientific_properties'].pop('growth_port');expect(f,'UNCERTAIN')
check('missing_growth_port_uncertain',missing)
def nofacts():assert polarity_check(*fixture(),['unknown'],verified)['status']=='UNCERTAIN'
check('unknown_evidence_uncertain',nofacts)
def annotate(graph):
 out=copy.deepcopy(graph)
 for o in out['objects']:
  if o['object_id'] in ['new_leading','fragment_1','fragment_2','gap_fill']:
   o['scientific_properties'].update(endpoint_labels={'start':"5'",'end':"3'"},growth_port='end',template_id='template_leading' if o['object_id']=='new_leading' else 'template_lagging',polarity_evidence_ids=facts)
 return out
annotated=annotate(g);checks=graph_polarity(annotated,p)
check('V4_lagging_endpoints_independently_revalidated',lambda: (_ for _ in ()).throw(AssertionError('V4 growth mismatch')) if not checks or any(c['status']!='PASS' for c in checks) else None)
original=graph_polarity(g,p)
check('unannotated_V4_missing_contract_uncertain',lambda: (_ for _ in ()).throw(AssertionError()) if not all(c['status']=='UNCERTAIN' for c in original) else None)
root=E/'tests/router_fixture';(root/'scene_ir').mkdir(parents=True,exist_ok=True);write(root/'scene_ir/dna_section4.json',g)
router=RepairRouter();task=router.task({'issue_id':'identity','root_cause_stage':'SCENE_IR','target_objects':['primase'],'target_fields':['scientific_identity.name','visual_representation.label']})
def no_op():assert router.apply(root,task,[])['status']=='REPAIR_NOT_APPLIED'
check('no_op_repair_does_not_render',no_op)
def patch():
 out=router.apply(root,task,[{'object_id':'primase','field':'scientific_identity.name','value':'RNA primase'},{'object_id':'primase','field':'visual_representation.label','value':'Primase'}]);assert out['status']=='CANDIDATE_CREATED' and len(out['changed'])==2
check('true_IR_fields_changed',patch)
def forbidden():
 before=(root/'scene_ir/dna_section4.json').read_bytes()
 try:router.apply(root,task,[{'object_id':'new_leading','field':'scientific_identity.name','value':'wrong'}])
 except ValueError:pass
 else:raise AssertionError('Not rejected')
 assert before==(root/'scene_ir/dna_section4.json').read_bytes()
check('unrelated_object_patch_rejected_atomically',forbidden)
cal={'all_passed':all(x['passed'] for x in results[:10]),'includes_negative_controls':True}
review=json.loads((R/'experiments/scientific_scene_v4/validation/dna_repaired_ir_review.json').read_text());mapped=copy.deepcopy(review)
for issue in mapped['issues']:
 if issue['issue_id']=='polarity_label_conflict':issue['rule_id']='DNA_STRAND_POLARITY'
adjudications=ScientificConflictAdjudicator().adjudicate(annotated,p,checks,mapped,cal)
check('specific_false_positive_adjudicated_other_issues_retained',lambda: (_ for _ in ()).throw(AssertionError()) if len(adjudications)!=1 or adjudications[0]['status']!='REVIEWER_FALSE_POSITIVE' or len(review['issues'])!=3 else None)
uncertain=ScientificConflictAdjudicator().adjudicate(g,p,original,mapped,cal)
check('insufficient_contract_requires_human',lambda: (_ for _ in ()).throw(AssertionError()) if uncertain[0]['status']!='NEEDS_HUMAN_REVIEW' else None)
write(E/'reviewer_fix/polarity_test_cases.json',results[:10]);write(E/'reviewer_fix/deterministic_results.json',checks);write(E/'reviewer_fix/original_V4_results.json',original);write(E/'reviewer_fix/conflict_cases.json',mapped);write(E/'reviewer_fix/adjudication_results.json',adjudications);write(E/'reviewer_fix/historical_issue_mapping.json',{'review_file':'V4/validation/dna_repaired_ir_review.json','issue_id':'polarity_label_conflict','assigned_rule_id':'DNA_STRAND_POLARITY','basis':'Explicit full description asserts reversed antiparallel rule; mapping by inspected issue, not free-text classifier'})
write(E/'tests/test_results.json',{'all_passed':all(x['passed'] for x in results),'passed':sum(x['passed'] for x in results),'total':len(results),'includes_negative_controls':True,'results':results})
print(json.dumps(results,ensure_ascii=False));assert all(x['passed'] for x in results)

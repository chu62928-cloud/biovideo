from pathlib import Path
import sys,json,os,copy,time
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.agent import BiologyExpertAgent
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write,digest
from biology_expert.model_reliability import EvidenceGapResearch,validate_repair,ScientificCausalGraphValidator
from biology_expert.contract_builder import ScientificEvidenceRetriever
from biology_expert.typed_science_builder import validate_typed_model,TypedScienceModelReviewer
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
G=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000})
for topic in ['mitosis','dna_replication','vesicle_transport']:
 f=E/'science'/topic;f.mkdir(parents=True,exist_ok=True);inp=E/'inputs'/topic
 old=json.loads((inp/'typed_result.json').read_text());task=json.loads((inp/'task.json').read_text());retrieval=json.loads((inp/('retrieval_publisher.json' if (inp/'retrieval_publisher.json').exists() else 'retrieval.json')).read_text())
 try:
  agent=BiologyExpertAgent(f/'workflow',G);auditfile=f/'audit.json'
  if not auditfile.exists():write(auditfile,agent.audit_typed_reliability(task,old['model'],retrieval['evidence'],old['review']))
  audit=json.loads(auditfile.read_text());print('AUDITED',topic,flush=True)
  if topic=='mitosis':continue
  researchfile=f/'gap_research.json'
  if not researchfile.exists():write(researchfile,EvidenceGapResearch(G,ScientificEvidenceRetriever(E/'research',limit=80,visual_limit=0)).retrieve(task,audit['evidence']['issues']+audit['causal']['issues'],f/'research_cache'))
  research=json.loads(researchfile.read_text());new=research['evidence'];write(f/'evidence.json',retrieval['evidence']+new)
  if not new:write(f/'repair_result.json',{'status':'NEEDS_HUMAN_REVIEW','reason':'Targeted research returned no new verifiable source'});continue
  all_evidence=retrieval['evidence']+new
  for attempt in range(2):
   out=f/('candidate_'+str(attempt)+'.json')
   previous=json.loads((f/('review_'+str(attempt-1)+'.json')).read_text()) if attempt else old['review']
   before=json.loads((f/('candidate_'+str(attempt-1)+'.json')).read_text()) if attempt else old['model']
   if not out.exists():
    schema=json.loads((R/'src/biology_expert/schemas/typed_science_model.schema.json').read_text())
    prompt='Repair this typed scientific model against targeted new source evidence and original task. Return COMPLETE compact JSON under5500 tokens. Preserve ALL original process_semantic_ids and constraint_ids; do not delete failures, narrow user scope or substitute labels for mechanism. Add evidence-supported actors/states/intermediate processes only as needed. Explicit initial_states dictionary must be source-supported. preconditions/effects must use same keys/values and declared start/end conditions. Preserve exact contiguous quote/location on every entity,relation,process,observable. Avoid claiming biological specificity unsupported by sources. Resolve all reviewer issues, but flag conflicts unresolved. Do not self-approve. '
    sources=[]
    for ev in all_evidence:
     # Targeted passage ranking uses task+gap text, never a topic-specific fact table.
     import re
     words=set(re.findall('[a-z]+',(task['user_request']+json.dumps(audit)).lower()))
     ranked=sorted(ev['passages'],key=lambda q:-len(words&set(re.findall('[a-z]+',q['text'].lower()))))[:12]
     sources.append({k:ev[k] for k in ['evidence_id','url','title']}|{'passages':ranked})
    candidate=parse_json(G.request('deepseek','evidence_grounded_model_repair',prompt+json.dumps({'task':task,'candidate':before,'review':previous,'gaps':audit,'schema':schema,'sources':sources},ensure_ascii=False)));write(out,candidate)
   candidate=json.loads(out.read_text());accept=validate_repair(old['model'],candidate,new,audit['evidence']['issues']);write(f/('patch_acceptance_'+str(attempt)+'.json'),accept)
   if not accept['accepted']:break
   try:validate_typed_model(candidate,all_evidence)
   except Exception as ex:write(f/('schema_error_'+str(attempt)+'.json'),{'error':str(ex),'stage':'SCIENTIFIC_MODEL_SCHEMA'});break
   reviewfile=f/('review_'+str(attempt)+'.json')
   if not reviewfile.exists():write(reviewfile,TypedScienceModelReviewer(G).review(candidate,all_evidence,task))
   review=json.loads(reviewfile.read_text());causal=ScientificCausalGraphValidator().validate(candidate);write(f/('causal_'+str(attempt)+'.json'),causal)
   write(f/'repair_result.json',{'status':review['decision'],'candidate_path':str(out),'review':review,'causal':causal,'before_sha256':digest(old['model']),'after_sha256':digest(candidate),'new_evidence_ids':[v['evidence_id'] for v in new]})
   print('REVIEW',topic,attempt,review['decision'],flush=True)
   if review['decision']=='PASS':break
 except Exception as ex:
  write(f/'error.json',{'stage':'SCIENCE_RELIABILITY','type':type(ex).__name__,'message':str(ex)[:1500]});print('ERROR',topic,type(ex).__name__,flush=True)

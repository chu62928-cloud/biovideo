"""Same evidence-grounded builder for any topic; no topic facts in code."""
import re
from ..state import write
from ..providers import parse_json
from ..schemas import validate
def normalize(text):
 import unicodedata
 text=unicodedata.normalize('NFKC',text).replace('′',"'").replace('’',"'").lower()
 text=re.sub(r'\s*([,.;:()—–])\s*',r'\1',text)
 return re.sub(r'\s+',' ',text).strip()

def topic_analyzer(user_request):
 obj=dict(user_request) if isinstance(user_request,dict) else {'topic':str(user_request)}
 obj.setdefault('audience','high_school');obj.setdefault('video_goal','Explain the biological mechanism accurately')
 obj['topic_id']=obj.get('topic_id') or re.sub('[^a-z0-9]+','_',obj['topic'].lower()).strip('_')
 obj['scope_status']='PROVISIONAL'
 return obj
class KnowledgeTools:
 def __init__(self,gateway,root):self.gateway=gateway;self.root=root
 def build(self,scope,retrieval):
  if not retrieval['evidence']:return {'status':'UNVERIFIED','facts':[],'topic_scope':scope}
  prompt="""Build an evidence-grounded Topic Knowledge Pack for the supplied topic and audience. Use ONLY actually retrieved evidence passages below. Return JSON with facts (5-8 atomic facts), mechanism (events, roles, constraints), assumptions.
Each fact: fact_id, claim, scope, classification (established|teaching_simplification|disputed|unverified), evidence_ids, support:[{evidence_id,quote}].
Every quote must be an EXACT contiguous substring of a retrieved passage, preferably 8-22 words, not a paraphrase. Do not invent citations. Include multiple sources where they genuinely support the same claim; do not use a title as claim evidence. Classification does not establish verification.
Scope carefully: organism/stage matters; exclude molecular details not supported by sources. For DNA synthesis include 5prime-to-3prime addition at the free 3prime end, antiparallel templates, priming and maturation if actually supported. For mitosis distinguish sister chromatids vs homologous chromosomes, S phase vs mitosis, nuclear division vs cytokinesis. State any evidence gaps rather than fill from memory.
For mechanism constraints use scientific language and associated fact_ids; do NOT prescribe screen x coordinates.
""" + '\nTOPIC:\n'+str(scope)+'\nRETRIEVED:\n'+str(retrieval['evidence'])
  data=parse_json(self.gateway.request('deepseek','knowledge_'+scope['topic_id'],prompt))
  pack={'topic_id':scope['topic_id'],'topic_scope':scope,'facts':data['facts'],'evidence':retrieval['evidence'],'mechanism':data.get('mechanism',{}),'assumptions':data.get('assumptions',[]),'build_report':{'status':'PENDING_VERIFICATION','retrieval_failures':retrieval['failures'],'model_synthesis_only':True}}
  for fact in pack['facts']:validate('fact',fact)
  validate('knowledge_pack',pack)
  self.save(pack);return pack
 def save(self,pack):
  out=self.root/pack['topic_id'];out.mkdir(parents=True,exist_ok=True)
  for key,name in [('topic_scope','topic_scope'),('facts','facts'),('evidence','evidence'),('mechanism','mechanism'),('assumptions','assumptions'),('build_report','build_report')]:write(out/(name+'.json'),pack[key])
  write(out/'knowledge_pack.json',pack)
 def verify(self,pack):
  evidence={e['evidence_id']:e for e in pack['evidence']}
  for fact in pack['facts']:
   reasons=[];valid=[]
   for support in fact['support']:
    item=evidence.get(support['evidence_id'])
    if not item or item['status']!='RETRIEVED':reasons.append('Evidence not actually retrieved');continue
    passages=' '.join(p['text'] for p in item['passages'])
    full=self.root.parent/'logs/retrieval'/(item['evidence_id']+'.txt')
    if full.exists():
     import hashlib
     content=full.read_text()
     if hashlib.sha256(content.encode()).hexdigest()==item.get('content_sha256'):passages+=' '+content
    if normalize(support['quote']) not in normalize(passages):reasons.append('Supporting quote not found verbatim');continue
    if support['evidence_id'] not in fact['evidence_ids']:reasons.append('Support ID not linked');continue
    valid.append(support['evidence_id'])
   status='VERIFIED' if valid and not reasons and fact['classification'] in ['established','teaching_simplification'] else ('CONFLICTED' if fact['classification']=='disputed' else 'INSUFFICIENT_EVIDENCE')
   fact['verification']=status
   fact['verification_detail']={'support_spans_match':bool(valid),'matched_evidence_ids':sorted(set(valid)),'independent_publishers':len(set(evidence[i]['publisher'] for i in valid)),'reasons':reasons,'entailment_status':'MODEL_PROPOSED_NOT_INDEPENDENTLY_CONFIRMED','meaning':'VERIFIED here means retrieved support+scope proposed by builder, not independent expert fact approval'}
  pack['build_report'].update(status='SUPPORTED_WITH_LIMITS' if any(f['verification']=='VERIFIED' for f in pack['facts']) else 'UNVERIFIED',verified_support_count=sum(f['verification']=='VERIFIED' for f in pack['facts']),total_facts=len(pack['facts']),limitation='Verbatim source matching is not semantic entailment. Dedicated cross-verification must precede scientific gate PASS.')
  self.save(pack);return pack

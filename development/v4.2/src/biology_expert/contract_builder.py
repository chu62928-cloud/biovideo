"""Live evidence discovery and evidence-first contract building for arbitrary topics."""
from pathlib import Path
from urllib.parse import urlparse,quote,unquote,parse_qs,urljoin
import requests,json,time,hashlib,re,ipaddress,socket,copy
from bs4 import BeautifulSoup
from .contracts import write,digest,schema_validate,ConstraintExecutor,ScientificCoverageAuditor,ScientificMutationTester,ScientificConflictAdjudicator,ReferenceAwareVideoReviewer,ContractStore
from .providers import parse_json

class ScientificEvidenceRetriever:
 def __init__(self,root,limit=36,visual_limit=12):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.path=self.root/'network.json';self.rows=json.loads(self.path.read_text()) if self.path.exists() else [];self.limit=limit;self.visual_limit=visual_limit
 def get(self,url,kind='scientific'):
  host=urlparse(url).hostname
  if urlparse(url).scheme!='https' or not host:raise ValueError('HTTPS public sources only')
  if any(ipaddress.ip_address(x[4][0]).is_private for x in socket.getaddrinfo(host,443)):raise ValueError('Private network source rejected')
  limit=self.visual_limit if kind=='visual' else self.limit
  if sum(r['kind']==kind for r in self.rows)>=limit:raise RuntimeError('Persistent retrieval request budget exhausted: '+kind)
  row={'url':url,'kind':kind,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'pending'};self.rows.append(row);write(self.path,self.rows)
  try:
   response=requests.get(url,timeout=25,headers={'User-Agent':'Mozilla/5.0 (compatible; ScientificContractResearch/4.2)'},allow_redirects=False)
   row['http_status']=response.status_code;response.raise_for_status()
   if response.is_redirect:raise ValueError('Redirect destination requires explicit fresh public validation')
   row.update(status='ok',content_sha256=hashlib.sha256(response.content).hexdigest());return response
  except Exception as ex:row.update(status='UNVERIFIED',error=type(ex).__name__);raise
  finally:write(self.path,self.rows)
 def fetch(self,url,topic_id):
  response=self.get(url);response.encoding='utf-8';soup=BeautifulSoup(response.text,'html.parser')
  title=soup.title.get_text(' ',strip=True) if soup.title else url
  for el in soup(['script','style','nav','header','footer']):el.decompose()
  text=soup.get_text(' ',strip=True)
  if len(text)<1200 or any(x in title.lower() for x in ['captcha','access denied','just a moment','checking your']):raise ValueError('Noncontent/challenge response')
  eid='E_'+hashlib.sha256(url.encode()).hexdigest()[:12];dest=self.root/topic_id;dest.mkdir(exist_ok=True)
  (dest/(eid+'.html')).write_text(response.text);(dest/(eid+'.txt')).write_text(text)
  paragraphs=[{'location':'paragraph_'+str(i),'text':p.get_text(' ',strip=True)} for i,p in enumerate(soup.find_all(['p','figcaption'])) if len(p.get_text(' ',strip=True))>40]
  if not paragraphs:paragraphs=[{'location':'body','text':text[:18000]}]
  figures=[]
  for figure in soup.find_all('figure'):
   img=figure.find('img');caption=figure.get_text(' ',strip=True)
   if img:
    src=img.get('src') or img.get('data-src')
    if src:figures.append({'url':urljoin(url,src),'caption':caption,'alt':img.get('alt',''),'source_page':url})
  return {'evidence_id':eid,'url':url,'title':title,'author_or_institution':urlparse(url).hostname,'source_type':'retrieved_scientific_webpage','biological_scope':'Requires independent scope verification against quoted passages','accessed_utc':self.rows[-1]['started_utc'],'content_sha256':hashlib.sha256(text.encode()).hexdigest(),'saved_text':str(dest/(eid+'.txt')),'passages':paragraphs,'figures':figures,'fact_support':[],'conflicts':[],'trust_limitations':'Publisher authority and exact quotes do not establish entailment; independent contract review required','status':'RETRIEVED'}
 def retrieve(self,scope,plan):
  urls=list(dict.fromkeys(plan.get('candidate_urls',[])));failures=[];search_records=[]
  # Queries and suggested sources are model planned, but never counted as evidence until fetched.
  for query in plan.get('scientific_queries',[])[:1]:
   url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?query='+quote(query)+'&format=json&pageSize=2'
   try:
    response=self.get(url);data=response.json();search_records.append({'query':query,'service':'Europe PMC','results':data.get('resultList',{}).get('result',[])})
   except Exception as ex:failures.append({'url':url,'error':type(ex).__name__})
  evidence=[]
  for url in urls[:3]:
   try:evidence.append(self.fetch(url,scope['topic_id']))
   except Exception as ex:failures.append({'url':url,'error':type(ex).__name__})
  result={'evidence':evidence,'failures':failures,'search_records':search_records,'research_status':'RETRIEVED' if evidence else 'UNVERIFIED','discovery':'Agent planned queries + live bibliographic search + content fetch, no legacy topic catalogue'}
  write(self.root/(scope['topic_id']+'_retrieval.json'),result);return result
 def visual(self,scope,plan,retrieval):
  registry=[]
  for ev in retrieval['evidence']:
   for fig in ev.get('figures',[])[:3]:
    item={'reference_id':'REF_'+hashlib.sha256(fig['url'].encode()).hexdigest()[:10],'source_url':fig['url'],'source_page':ev['url'],'source_type':'scientific_illustration','scientific_objects':plan.get('visual_objects',[]),'represented_states':plan.get('visual_states',[]),'represented_processes':plan.get('visual_queries',[]),'caption':fig['caption'],'alt':fig['alt'],'scientific_review':'PENDING','license_status':'UNVERIFIED','reuse_allowed':False,'actual_asset_imported':False,'found':True,'page_read':True,'image_retrieved':False,'relations_extracted':False,'limitations':['Caption is not independent verification of image pixels','No external asset imported into generated work']}
    try:
     response=self.get(fig['url'],'visual');mime=response.headers.get('content-type','')
     if not mime.startswith('image/'):raise ValueError('Not actual image bytes')
     suffix='.svg' if 'svg' in mime else '.jpg' if 'jpeg' in mime else '.png'
     out=self.root/scope['topic_id']/(item['reference_id']+suffix);out.write_bytes(response.content)
     item.update(image_retrieved=True,local_reference_path=str(out),image_sha256=hashlib.sha256(response.content).hexdigest(),mime=mime)
    except Exception as ex:item['limitations'].append(type(ex).__name__)
    registry.append(item)
  if not registry:registry.append({'reference_id':'REF_GAP_'+scope['topic_id'],'source_url':None,'source_type':'NOT_RETRIEVED','scientific_objects':plan.get('visual_objects',[]),'represented_states':plan.get('visual_states',[]),'represented_processes':plan.get('visual_queries',[]),'scientific_review':'NOT_MEASURED','license_status':'UNVERIFIED','reuse_allowed':False,'actual_asset_imported':False,'found':False,'limitations':['No accessible figure discovered; no reference video evidence']})
  write(self.root/(scope['topic_id']+'_visual_registry.json'),registry);return registry

class ScientificContractBuilder:
 def __init__(self,gateway,root,retriever):self.gateway=gateway;self.root=Path(root);self.retriever=retriever
 def plan(self,user_request):
  prompt='''Plan evidence discovery for this educational scientific task. Do not use historical project rules, facts, examples or blueprints. Return JSON {"topic_id":"user supplied ID","scientific_queries":["precise literature query"],"candidate_urls":["2-3 likely direct authoritative textbook/science webpages covering the actual process; suggestions not evidence"],"visual_queries":["objects+states+relations+motion+high school schematic"],"visual_objects":[],"visual_states":[],"scope":{"included":[],"excluded":[]}}. Prefer accessible authoritative mechanism descriptions with figure captions. URLs will be truly fetched and verified; do not pretend retrieval occurred.'''
  return parse_json(self.gateway.request('deepseek','contract_discovery_plan',prompt+json.dumps(user_request,ensure_ascii=False)))
 def build(self,scope,retrieval,visual):
  if not retrieval['evidence']:return {'status':'INSUFFICIENT_EVIDENCE','reason':'No real source content','contract':None}
  schema=json.loads((Path(__file__).parent/'schemas/scientific_contract.schema.json').read_text())
  prompt='''Build a Scientific Contract from ONLY the actual retrieved evidence and user requirements. No historical rule or scene blueprint is provided or allowed. Return exactly one contract JSON matching supplied schema. Create 6-9 atomic constraints, covering entities, structural/process state, temporal order, sustained relations and visible mechanism where source supports it. Use semantic role names, not invented screen object IDs. Each constraint needs exact contiguous quote(s) from provided passages and actual evidence IDs. Never mark INDEPENDENTLY_VERIFIED. Methods: runtime_trace, scene_graph, video_semantic_review, human. Primitive must be one of listed executor capabilities or null, capability VLM/HUMAN/UNSUPPORTED when computation cannot establish the biology. Executable must_hold arguments: relation -> relation:string; event_order -> ordered_roles:list; count -> kind,value; state -> key,value; endpoint_distance/distance -> source_anchor,target_anchor,max; direction -> a_start,a_end,b_start,b_end,min,max; identity/exists need participant_roles. Do NOT force every statement into deterministic PASS. coverage_requirements item_id references every entity role/process role, plus necessary relation/temporal/persistent items; constraint_ids may be empty to honestly represent gaps. Scope must match user request. required_observations list critical observable event/state descriptions. State declared simplifications, contested/unknown mechanisms in unresolved_questions. Do not create display coordinates. Evidence snippets should be short exact text, not titles or source URLs. Contract adequacy will be independently reviewed.'''
  # Bound retrieval context by ranked task relevance, not hardcoded topic facts.
  tokens=set(re.findall('[a-z]+',scope['topic'].lower()+' '+scope['user_request'].lower()))
  evidence=[]
  for ev in retrieval['evidence']:
   selected=sorted(ev['passages'],key=lambda p:-len(tokens&set(re.findall('[a-z]+',p['text'].lower()))))[:16]
   evidence.append({k:ev[k] for k in ['evidence_id','url','title','source_type','trust_limitations'] }|{'passages':selected})
  data=parse_json(self.gateway.request('deepseek','scientific_contract_build',prompt+json.dumps({'scope':scope,'schema':schema,'capabilities':sorted(ConstraintExecutor.METHODS),'actual_evidence':evidence,'visual_reference_captions':[{k:v for k,v in x.items() if k in ['reference_id','caption','alt','source_page','image_retrieved']} for x in visual]},ensure_ascii=False)))
  schema_validate(data);return data
 def verify(self,contract,retrieval,scope):
  schema_validate(contract);evidence={e['evidence_id']:e for e in retrieval['evidence']};errors=[]
  for c in contract['constraints']:
   for ref in c['evidence_ids']:
    if ref not in evidence:errors.append({'constraint_id':c['constraint_id'],'error':'Unknown evidence '+ref})
   for support in c['support']:
    e=evidence.get(support['evidence_id']);quote=support['quote']
    if e is None or not any(quote in p['text'] for p in e['passages']):errors.append({'constraint_id':c['constraint_id'],'error':'Supporting quote not found verbatim','support':support})
  prompt='''Independently review this proposed scientific contract against ACTUAL source passages and the original user goals. Do not approve from JSON validity or same-model confidence. For each constraint, check exact quote entailment, biological scope, whether the computational primitive can really prove the statement, appropriate exceptions, and whether key user goals are omitted. Return JSON {"decision":"PASS|REVISE|REVIEW_INCOMPLETE|NEEDS_HUMAN_REVIEW","constraint_reviews":[{"constraint_id":"...","status":"SUPPORTED|INSUFFICIENT_EVIDENCE|CONFLICTED","reason":"...","evidence_ids":[]}],"goal_coverage":{"decision":"PASS|REVIEW_INCOMPLETE","missing_goals":[]},"issues":[],"reference_events":[{"event_role":"...","state":"...","relations":[],"evidence_ids":[],"quote":"exact source passage"}]}. Every constraint needs a verdict. Only PASS if source-supported and whole user goal covered; do not confuse a graph metadata check with visual semantics. A source may simplify; cite actual ambiguity, never invent details from memory.'''
  # Only supporting passages are passed with independent request to keep scope verifiable.
  excerpts=[]
  for ev in retrieval['evidence']:
   needed=[p for p in ev['passages'] if any(s['evidence_id']==ev['evidence_id'] and s['quote'] in p['text'] for c in contract['constraints'] for s in c['support'])]
   excerpts.append({'evidence_id':ev['evidence_id'],'url':ev['url'],'title':ev['title'],'passages':needed})
  semantic=parse_json(self.gateway.request('deepseek','independent_contract_verification',prompt+json.dumps({'user_request':scope,'contract':contract,'source_excerpts':excerpts,'deterministic_quote_errors':errors},ensure_ascii=False)))
  verdicts={v['constraint_id']:v for v in semantic.get('constraint_reviews',[])}
  for c in contract['constraints']:
   bad=any(x['constraint_id']==c['constraint_id'] for x in errors)
   c['verification_status']='INDEPENDENTLY_VERIFIED' if not bad and verdicts.get(c['constraint_id'],{}).get('status')=='SUPPORTED' else 'INSUFFICIENT_EVIDENCE'
  all_verified=all(c['verification_status']=='INDEPENDENTLY_VERIFIED' for c in contract['constraints'])
  decision=semantic['decision'] if all_verified and not errors else 'REVIEW_INCOMPLETE'
  return {'decision':decision,'semantic_review':semantic,'quote_errors':errors,'independent_request':True,'independent_provider':False,'limitation':'Separate request using same provider, not independent scientist; source entailment is explicit','contract_hash':digest(contract)}

class ContractAgentTools:
 def __init__(self,agent,root):
  self.agent=agent;self.root=Path(root);self.retriever=ScientificEvidenceRetriever(self.root/'references/retrieval');self.builder=ScientificContractBuilder(agent.gateway,self.root/'contracts',self.retriever)
  tools={'scientific_evidence_retriever':self.retriever.retrieve,'visual_reference_retriever':self.retriever.visual,'scientific_contract_builder':self.builder.build,'contract_verifier':self.builder.verify,'coverage_auditor':ScientificCoverageAuditor().audit,'mutation_tester':ScientificMutationTester().run,'reference_video_reviewer':ReferenceAwareVideoReviewer(agent.gateway).review,'scientific_conflict_adjudicator':ScientificConflictAdjudicator().adjudicate}
  for name,fn in tools.items():agent.registry.register(name,fn)
 def call(self,name,args,reason):return self.agent._call(name,args,'Build and verify scientific standards',reason)
 def build_contract(self,user_request):
  scope=dict(user_request);plan=self.builder.plan(scope);write(self.root/'contracts'/scope['topic_id']/'discovery_plan.json',plan)
  retrieval=self.call('scientific_evidence_retriever',{'scope':scope,'plan':plan},'No independently retrieved evidence for this new task; retrieve source text before drafting standards.')
  visual=self.call('visual_reference_retriever',{'scope':scope,'plan':plan,'retrieval':retrieval},'Current task needs state/relationship-aware visual references; distinguish captions, pixels, license and import.')
  if not retrieval['evidence']:return {'status':'REVIEW_INCOMPLETE','retrieval':retrieval,'contract':None}
  contract=self.call('scientific_contract_builder',{'scope':scope,'retrieval':retrieval,'visual':visual},'No contract exists; synthesize standards from fetched passages, not historical test rules.')
  review=self.call('contract_verifier',{'contract':contract,'retrieval':retrieval,'scope':scope},'Builder proposals must pass separate source-entailment and goal-completeness review.')
  folder=self.root/'contracts'/scope['topic_id'];write(folder/'scientific_contract.json',contract);write(folder/'contract_review.json',review);write(folder/'evidence.json',retrieval['evidence']);write(folder/'verification_plan.json',contract['verification_plan']);write(folder/'visual_reference_registry.json',visual)
  freeze=ContractStore(folder/'frozen').freeze(contract,review) if review['decision']=='PASS' else None;write(folder/'freeze_status.json',freeze or {'status':'NOT_FROZEN','reason':'Contract scientific review not PASS'})
  return {'contract':contract,'review':review,'retrieval':retrieval,'visual':visual,'freeze':freeze}
 def audit_contract(self,contract,scene,trace,bindings=None,goal_review=None):
  execution=ConstraintExecutor().execute(contract,scene,trace,bindings)
  coverage=self.call('coverage_auditor',{'contract':contract,'execution':execution,'goal_review':goal_review},'Determine actual measured coverage before interpreting pass counts.')
  return {'execution':execution,'coverage':coverage,'decision':'REVISE' if execution['decision']=='REVISE' else coverage['decision']}

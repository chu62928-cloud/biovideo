from pathlib import Path
import json,sys,os
R=Path('/autodl-tmp/code2biovideo/Code2Video');E=R/'experiments/biology_expert_v3'
sys.path.insert(0,str(R/'src'))
from biology_expert.agent import BiologyExpertAgent
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.state import write
from biology_expert.tools.reviewers import ReviewTools
for line in (R.parent/'.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v.strip().strip('"').strip("'")
agent=BiologyExpertAgent(E,ModelGateway(E/'logs/models'))
pack=json.loads((E/'knowledge/dna_replication/knowledge_pack.json').read_text())
retrieval=json.loads((E/'knowledge/dna_replication/retrieval_corrected.json').read_text())
extra=agent._call('evidence_fetch',{'url':'https://openstax.org/books/biology-2e/pages/14-2-dna-structure-and-sequencing'},'Fill critical scientific evidence gap','The first pack has polymerase roles but lacks the actual synthesis-direction/antiparallel rules.')
retrieval['evidence']+=extra['evidence'];retrieval['failures']+=extra['failures']
challenge=agent._call('evidence_fetch',{'url':'https://www.ncbi.nlm.nih.gov/books/NBK26850/'},'Check second textbook source availability','A browser challenge must remain UNVERIFIED, even with HTTP200.')
write(E/'logs/bookshelf_content_check.json',challenge)
pack=agent._call('extractive_builder',{'pack':pack,'retrieval':retrieval,'queries':["DNA pol add 5 3 direction","antiparallel strands"]},'Supplement the topic knowledge from real evidence','Extract actual source sentences, then independently verify their meaning; no authored facts.')
pack=agent._call('support_verifier',{'pack':pack},'Verify new source statements','Match exact retrieved source content including hash-verified full text.')
pack=agent._call('fact_verifier',{'pack':pack},'Verify supplemented scientific rules','Use the last permitted DeepSeek request for independent entailment/scope review.')
agent.knowledge.save(pack)
write(E/'knowledge/dna_replication/supplement_provenance.json',{'new_paid_requests':1,'why':'Initial source-discovery case mismatch missed textbooks and lacked a direction fact; initial detection evidence was insufficient','initial_results_retained':'initial_run_failures/','not_pre_authored_topic_facts':True})
print('DNA_FACTS',[(f['fact_id'],f['claim'][:110],f['verification']) for f in pack['facts']],flush=True)
# Re-evaluate same mitosis facts with correct UTF8 source decoding and source full-text hashes.
mit=json.loads((E/'knowledge/eukaryotic_mitosis/knowledge_pack.json').read_text())
mit['evidence']=json.loads((E/'knowledge/eukaryotic_mitosis/retrieval_corrected.json').read_text())['evidence']
mit=agent.knowledge.verify(mit)
raw=json.loads((E/'logs/models/v3_07_response.json').read_text())['choices'][0]['message']['content']
verdict=parse_json(raw);by={x['fact_id']:x for x in verdict['facts']}
for f in mit['facts']:
 v=by.get(f['fact_id'],{})
 linked=bool(v.get('evidence_ids')) and set(v.get('evidence_ids',[]))<=set(f['evidence_ids'])
 f['semantic_verification']=v.get('status','INSUFFICIENT_EVIDENCE') if f['verification']=='VERIFIED' and linked else 'INSUFFICIENT_EVIDENCE'
 f['semantic_reason']=v.get('reason','')
 if f['semantic_verification']!='VERIFIED':f['verification']=f['semantic_verification']
mit['build_report'].update(status='VERIFIED_WITH_SCOPE_LIMITS' if all(f['verification']=='VERIFIED' for f in mit['facts']) else 'PARTIALLY_VERIFIED',semantic_verified_count=sum(f['verification']=='VERIFIED' for f in mit['facts']),encoding_correction='HTTP source bytes decoded as UTF8, not inferred Latin1; claims unchanged; cached independent semantic verdict reapplied; no new model call')
agent.knowledge.save(mit)
class CachedScriptResponse:
 def request(self,*args,**kwargs):
  return json.loads((E/'logs/models/v3_08_response.json').read_text())['choices'][0]['message']['content']
samples=json.loads((E/'tests/fixtures/mitosis_samples.json').read_text())
replayed=ReviewTools(CachedScriptResponse(),E/'reviews').artifact_review('SCRIPT',{'samples':samples},{'knowledge_pack':mit})
replayed['provenance']={'mode':'REVALIDATED_SAVED_MODEL_RESPONSE','source_call':'v3_08','claims_and_sample_inputs_unchanged':True,'new_model_request':False,'reason':'Fixed source decoding and exact-span validation; original ERROR retained'}
write(E/'reviews/script/test_C_revalidated.json',replayed)
print('MITOSIS_FACTS',[(f['fact_id'],f['verification']) for f in mit['facts']],flush=True)
print('TEST_C',[(x.get('sample_id'),x.get('decision'),len(x.get('issues',[]))) for x in replayed.get('samples',[])],flush=True)

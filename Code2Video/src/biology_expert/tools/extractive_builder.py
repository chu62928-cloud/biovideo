"""Generic evidence-gap supplementation using exact source sentences, not authored topic facts."""
import re,hashlib
def supplement(pack,retrieval,queries):
 existing={e['evidence_id']:e for e in pack['evidence']}
 existing.update({e['evidence_id']:e for e in retrieval['evidence']})
 pack['evidence']=list(existing.values());new=[]
 for ev in retrieval['evidence']:
  if not ev.get('publisher','').startswith('OpenStax'):continue
  for p in ev['passages']:
   for sentence in re.split(r'(?<=[.!?])\s+',p['text']):
    if not 25<len(sentence)<550:continue
    tokens=set(re.findall('[a-z0-9]+',sentence.lower()))
    if not any(len(tokens&set(re.findall('[a-z0-9]+',q.lower())))>=max(2,len(set(re.findall('[a-z0-9]+',q.lower())))//2) for q in queries):continue
    # A sentence is not a verified fact yet. Normal verifier and independent semantic checker must run.
    fid='X_'+hashlib.sha256(sentence.encode()).hexdigest()[:8]
    if any(f['fact_id']==fid for f in pack['facts']):continue
    new.append({'fact_id':fid,'claim':sentence,'scope':'As stated in the retrieved textbook passage; application to the scene requires independent scope verification','classification':'established','evidence_ids':[ev['evidence_id']],'support':[{'evidence_id':ev['evidence_id'],'quote':sentence}],'generation_mode':'EXTRACTIVE_SOURCE_SENTENCE_NOT_PREWRITTEN_FACT'})
 pack['facts']+=new
 pack['build_report']['evidence_gap_supplement']={'new_fact_count':len(new),'queries':queries,'mode':'Exact source-sentence extraction; not automatic scientific approval'}
 return pack

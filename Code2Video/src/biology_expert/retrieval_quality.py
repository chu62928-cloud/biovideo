"""Query, source and claim gates shared by evidence discovery and repair."""
import re,json,hashlib
from .providers import parse_json

class RetrievalQueryInvalid(ValueError):pass

def validate_queries(plan,task=None):
    queries=plan.get('search_queries',plan.get('scientific_queries',[]))
    if not isinstance(queries,list) or not queries or any(not isinstance(q,str) for q in queries):raise RetrievalQueryInvalid('RETRIEVAL_QUERY_INVALID: queries must be a nonempty list of strings, never an iterable string')
    context=' '.join(str((task or {}).get(k,'')) for k in ['topic','user_request','research_question','required_claim'])
    context_tokens=set(re.findall(r'[a-zA-Z0-9α-ωΑ-Ω]+',context.lower()))
    for q in queries:
        tokens=re.findall(r'[a-zA-Z0-9α-ωΑ-Ω]+',q.lower())
        if len(set(tokens))<2 or not any(len(t)>1 for t in tokens):raise RetrievalQueryInvalid('RETRIEVAL_QUERY_INVALID: no discriminating scientific context')
        if context_tokens and not context_tokens.intersection(tokens):raise RetrievalQueryInvalid('RETRIEVAL_QUERY_INVALID: missing task/question context')
        if q.strip().startswith(('http://','https://')):raise RetrievalQueryInvalid('RETRIEVAL_QUERY_INVALID: URL is not a scientific question')
    urls=plan.get('candidate_urls',[])
    if not isinstance(urls,list) or any(not isinstance(u,str) for u in urls):raise RetrievalQueryInvalid('RETRIEVAL_QUERY_INVALID: candidate_urls must be a list')
    return queries

def source_quality(evidence):
    title=evidence.get('title','').strip();passages=evidence.get('passages',[])
    substantive=[p for p in passages if isinstance(p.get('text'),str) and p['text'].strip()!=title and len(p['text'].split())>=12 and not p.get('evidence_level')=='SEARCH_METADATA']
    # Word count only checks readable body availability, never scientific entailment.
    return {'status':'READABLE_BODY' if substantive else 'FULL_TEXT_UNAVAILABLE','usable_passages':substantive,'evidence_level':evidence.get('evidence_level','FULL_TEXT'),'reason':None if substantive else 'Title/navigation/metadata alone is not mechanism evidence'}

def exact_support(support,evidence):
    by={e['evidence_id']:e for e in evidence}
    for s in support:
        e=by.get(s.get('evidence_id'))
        if not e or source_quality(e)['status']!='READABLE_BODY':return False
        if not any(s.get('quote') and s['quote'] in p['text'] and s.get('location')==p['location'] for p in source_quality(e)['usable_passages']):return False
    return bool(support)

class EvidenceEntailmentCheck:
    STATUSES={'SUPPORTED','CONTRADICTED','PARTIALLY_SUPPORTED','INSUFFICIENT_EVIDENCE','OUT_OF_SCOPE'}
    def __init__(self,gateway):self.gateway=gateway
    def check(self,requests,evidence):
        usable=[{**{k:e.get(k) for k in ['evidence_id','url','title','biological_scope','evidence_level']},'passages':source_quality(e)['usable_passages']} for e in evidence if source_quality(e)['status']=='READABLE_BODY']
        if not usable:return {'claims':[{'claim_id':r['issue_id'],'entailment_status':'INSUFFICIENT_EVIDENCE','support':[]} for r in requests],'decision':'INSUFFICIENT_EVIDENCE'}
        prompt='Independently evaluate whether the actual source paragraphs resolve each evidence request. Return JSON {claims:[{claim_id,claim_text,entailment_status,biological_scope,support:[{evidence_id,location,quote}],reason}],decision}. Every request issue_id must appear as claim_id. entailment_status only SUPPORTED,CONTRADICTED,PARTIALLY_SUPPORTED,INSUFFICIENT_EVIDENCE,OUT_OF_SCOPE. SUPPORTED means original required claim at actual scope is entailed, not merely same names. CONTRADICTED means actual source disproves the original claim, with exact quote. Titles are not evidence. Abstracts support only what stated; do not infer full article. Preserve Greek letters and exact source excerpts. Unknowns stay insufficient. Do not provide science answers from memory.'
        out=parse_json(self.gateway.request('deepseek','independent_gap_evidence_entailment',prompt+json.dumps({'requests':requests,'sources':usable},ensure_ascii=False)))
        expected={r['issue_id'] for r in requests};got=[c.get('claim_id') for c in out.get('claims',[])]
        if set(got)!=expected or len(got)!=len(expected):raise ValueError('Missing or duplicate evidence claim review')
        for c in out['claims']:
            if c['entailment_status'] not in self.STATUSES:raise ValueError('Unknown entailment status')
            if c['entailment_status'] in ['SUPPORTED','CONTRADICTED','PARTIALLY_SUPPORTED'] and not exact_support(c.get('support',[]),evidence):c.update(entailment_status='INSUFFICIENT_EVIDENCE',reason='Exact body excerpt/location gate rejected support')
        out['decision']='SUFFICIENT' if all(c['entailment_status'] in ['SUPPORTED','CONTRADICTED'] for c in out['claims']) else 'INSUFFICIENT_EVIDENCE'
        return out

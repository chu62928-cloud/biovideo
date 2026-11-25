from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write,digest
from biology_expert.typed_science_builder import validate_typed_model,TypedScienceModelReviewer
from biology_expert.model_reliability import ScientificCausalGraphValidator
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
G=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000});f=E/'science/dna_replication';m=json.loads((f/'candidate_second_0.json').read_text());ev=json.loads((f/'evidence.json').read_text())
items=m['entities']+m['relations']+m['processes']+[o for p in m['processes'] for o in p['observables']]
indexed=[{'index':i,'item_id':x.get('semantic_id',x.get('process_semantic_id',x.get('constraint_id'))),'support':x['support']} for i,x in enumerate(items)]
prompt='Repair exact quote fidelity only. Candidate paraphrased Greek letters into English alpha/delta/epsilon inside supposedly verbatim quotes. Return JSON {patches:[{index,support:[{evidence_id,quote,location}]}]} for every bad quote. Select exact contiguous ORIGINAL text including original Greek symbols/punctuation and actual paragraph location. Do not change model science/IDs. All original sources supplied. If a claim not supported by any exact excerpt mark unresolved rather than fabricate. Compact under2500tokens.'
patch=json.loads((f/'quote_patch.json').read_text())
replacements={}
for row in patch['patches']:
 before=items[row['index']]['support'];after=row['support']
 for x,y in zip(before,after):replacements[json.dumps(x,sort_keys=True)]=y
for item in items:
 item['support']=[replacements.get(json.dumps(x,sort_keys=True),x) for x in item['support']]
write(f/'candidate_quote_corrected.json',m)
try:
 validate_typed_model(m,ev);review=TypedScienceModelReviewer(G).review(m,ev,json.loads((E/'inputs/dna_replication/task.json').read_text()));write(f/'review_quote_corrected.json',review);write(f/'causal_quote_corrected.json',ScientificCausalGraphValidator().validate(m));print(review['decision'],flush=True)
except Exception as ex:write(f/'quote_repair_error.json',{'error':str(ex),'stage':'EXACT_QUOTE_VALIDATION'});print(type(ex).__name__,flush=True)

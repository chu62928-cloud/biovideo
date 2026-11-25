"""Actual sampled geometry + visible polarity glyph positions, not declared growth_direction."""
import ast,math,operator,re
from pathlib import Path
def val(n,env):
 if isinstance(n,ast.Constant):return n.value
 if isinstance(n,ast.Name):return env[n.id]
 if isinstance(n,(ast.List,ast.Tuple)):return [val(x,env) for x in n.elts]
 if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -val(n.operand,env)
 if isinstance(n,ast.BinOp):
  ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
  return ops[type(n.op)](val(n.left,env),val(n.right,env))
 raise ValueError('Not a static coordinate expression')
def observed_glyphs(code):
 tree=ast.parse(code);env={};glyphs=[]
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Section4Scene')
 fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='construct')
 for stmt in fn.body:
  if isinstance(stmt,ast.Assign) and len(stmt.targets)==1 and isinstance(stmt.targets[0],ast.Name):
   try:env[stmt.targets[0].id]=val(stmt.value,env)
   except (KeyError,TypeError,ValueError,ZeroDivisionError):pass
  for n in ast.walk(stmt):
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='small_label' and len(n.args)>1:
    try:
     text=val(n.args[0],env);pos=val(n.args[1],env)
     if text in ["3'","5'"]:glyphs.append({'text':text,'position':pos,'code_line':n.lineno,'assignment':stmt.targets[0].id if isinstance(stmt,ast.Assign) and isinstance(stmt.targets[0],ast.Name) else None})
    except (KeyError,TypeError,ValueError):pass
 return glyphs
def first_visible(trace,selector):
 found={}
 for frame in trace['frames']:
  for name,obj in frame['objects'].items():
   if name not in found and obj.get('visible') and selector(name,obj):found[name]={'id':name,'time':frame['time'],'center':obj['center'],'bbox':obj['bbox']}
 return sorted(found.values(),key=lambda x:(x['time'],x['id']))
def mechanism_validator(artifacts,context):
 trace=artifacts.get('trace');code=artifacts.get('code','');pack=context.get('knowledge_pack',{})
 if not trace or not code:return {'status':'ERROR','reason':'Actual code and geometry trace required','checks':[]}
 facts=[f for f in pack.get('facts',[]) if f.get('verification')=='VERIFIED' and f.get('semantic_verification')=='VERIFIED']
 # IDs are scene adapter mappings, not a prewritten topic knowledge base.
 relevant=[f['fact_id'] for f in facts if re.search(r'5.{0,35}3|3.{0,35}5',f['claim']) and any(w in f['claim'].lower() for w in ['direction','synthes'])]
 glyphs=observed_glyphs(code)
 first=next((f for f in trace['frames'] if 'template_lagging' in f['objects']),None)
 if not first or not relevant:return {'status':'UNCERTAIN','reason':'Missing verified direction evidence or scene adapter unsupported','checks':[],'glyphs':glyphs}
 ty=first['objects']['template_lagging']['center'][1]
 template=[g for g in glyphs if g['position'][1]<ty-.1 and abs(g['position'][0])>5]
 template.sort(key=lambda g:g['position'][0])
 nascent=next((g for g in glyphs if g['assignment']=='lbl_lag3'),None)
 primers=first_visible(trace,lambda n,o:n.startswith('rna_primer_lagging_1_') and o.get('role')=='nucleotide')
 fill=first_visible(trace,lambda n,o:n.startswith('fill_dna_') and o.get('role')=='nucleotide' and o.get('material')=='DNA')
 expected=None
 if len(template)>=2 and nascent and primers:
  five=next((g for g in template if g['text']=="5'"),None);three=next((g for g in template if g['text']=="3'"),None)
  if five and three:
   # Template reading runs 3prime->5prime; nascent addition runs antiparallel to template 5prime->3prime.
   reading=[five['position'][i]-three['position'][i] for i in range(2)]
   norm=math.hypot(*reading);expected=[x/norm for x in reading]
   primer_x=sum(p['center'][0] for p in primers)/len(primers)
   if (nascent['position'][0]-primer_x)*expected[0]<=0:expected=None
 checks=[]
 if expected and len(fill)>=3:
  projections=[]
  for a,b in zip(fill,fill[1:]):
   delta=[b['center'][i]-a['center'][i] for i in range(2)]
   projections.append(sum(x*y for x,y in zip(delta,expected)))
  order_ok=all(a['time']<b['time'] for a,b in zip(fill,fill[1:]))
  direction='PASS' if order_ok and all(p>0.02 for p in projections) else 'FAIL'
  checks.append({'check_id':'lagging_gap_growth','status':direction,'fact_ids':relevant,'event_id':'event_5_maturation','object_ids':['new_lagging_strand','dna_polymerase_fill']+[f['id'] for f in fill],
    'evidence':{'template_polarity_glyphs':template,'nascent_3prime_glyph':nascent,'primer_centers':primers,'measured_nucleotide_first_visibility':fill,'template_reading_unit_vector':expected,'successive_addition_projections':projections,'code_and_trace_independent_of_declared_direction':True},
    'limitation':'Sparse schematic trace supports relative growth direction, not chemical bond continuity or a molecular-scale 3prime contact proof.'})
 else:checks.append({'check_id':'lagging_gap_growth','status':'UNCERTAIN','fact_ids':relevant,'reason':'Missing visible glyph/primer/temporal ordering evidence'})
 violations=[];contacts=[]
 for frame in trace['frames']:
  for bind in frame.get('bindings',[]):
   a=frame['objects'].get(bind['object_id']);b=frame['objects'].get(bind['target_id'])
   if a and b and a.get('visible'):
    distance=math.dist(a['center'],b['center'])
    contacts.append({'time':frame['time'],'enzyme':bind['object_id'],'anchor':bind['target_id'],'distance':distance})
    if distance>bind['max_distance']+.1:violations.append(contacts[-1])
 checks.append({'check_id':'registered_enzyme_anchor_contact','status':'FAIL' if violations else ('PASS' if contacts else 'UNCERTAIN'),'samples':len(contacts),'violations':violations,'limitation':'An anchor may itself be misplaced; attachment to the biological growing end requires further evidence.'})
 # Measure polymerase distance to real newly appearing nucleotides as an independent check of a declared anchor.
 growth=first_visible(trace,lambda n,o:o.get('role')=='nucleotide' and o.get('material')=='DNA' and o.get('strand') in ['leading','lagging'])
 distances=[]
 for nt in growth:
  frame=min(trace['frames'],key=lambda f:abs(f['time']-nt['time']))
  enzymes=[(k,o) for k,o in frame['objects'].items() if o.get('enzyme')=='polymerase' and o.get('visible') and o.get('strand')==frame['objects'][nt['id']].get('strand')]
  if enzymes:
   k,enzyme=min(enzymes,key=lambda kv:math.dist(kv[1]['center'],nt['center']))
   distances.append({'nucleotide':nt['id'],'time':nt['time'],'polymerase':k,'distance':math.dist(enzyme['center'],nt['center'])})
 checks.append({'check_id':'enzyme_actual_addition_proximity','status':'FAIL' if any(x['distance']>1.1 for x in distances) else ('PASS' if distances else 'UNCERTAIN'),'samples':distances,'threshold_scene_units':1.1,'limitation':'Schematic proximity is necessary, not sufficient for biochemical contact.'})
 duplicate=any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='make_duplex' for n in ast.walk(ast.parse(code)))
 checks.append({'check_id':'fork_topology','status':'UNCERTAIN' if duplicate else 'UNCERTAIN','object_ids':['replication_fork','template_leading','template_lagging'],'reason':'Separate make_duplex plus two extended templates requires video-science interpretation; unregistered parental body cannot be proved correct from metadata.'})
 return {'status':'FAIL' if any(c['status']=='FAIL' for c in checks) else 'UNCERTAIN','checks':checks,'glyphs':glyphs,'fact_ids':relevant}

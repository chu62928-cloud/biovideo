from pathlib import Path
import json,copy,hashlib
E=Path('/autodl-tmp/code2biovideo/Code2Video/experiments/scientific_scene_v4')
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
assets=[
 {'asset_id':'strand','format':'polyline','color':'#4FC3F7','fidelity':'schematic','provenance':{'source_type':'original_schematic','source_url':None,'license':'CC0-1.0'},'editable':['points','color','stroke_width'],'connectable_ports':['start','end']},
 {'asset_id':'bead','format':'circle','color':'#FFDD55','fidelity':'schematic','provenance':{'source_type':'original_schematic','source_url':None,'license':'CC0-1.0'},'editable':['center','radius'],'connectable_ports':['center']}]
for name in ['primase','dna_polymerase','dna_ligase']:
 assets.append({'asset_id':name,'format':'svg','path':'dna/'+name+'.svg','color':'#55DDEE','fidelity':'schematic','provenance':{'source_type':'V2_original_schematic','source_url':None,'license':'CC0-1.0'},'editable':['center','width','label'],'connectable_ports':['active_site']})
def center(points):return [(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)]
def obj(oid,kind,points=None,pos=None,color='#4FC3F7',asset='strand',label=None,visible=False,props=None,**style):
 geom={'visible':visible,'color':color,'label':label,**style}
 anchors={'center':{'kind':'center'}}
 if points:
  geom.update(points=points,center=center(points));anchors.update(start={'kind':'point','index':0},end={'kind':'point','index':-1})
 else:geom.update(center=pos or [0,0,0])
 return {'object_id':oid,'object_type':kind,'scientific_identity':{'name':label or oid.replace('_',' '),'kind':kind,'origin_id':oid},'scientific_properties':props or {},'asset_id':asset,'visual_representation':geom,'anchors':anchors,'editable_properties':list(geom),'evidence_ids':[]}
def cond(id,p,ids=None,**values):return {'constraint_id':id,'predicate':p,'object_ids':ids or [],**values}
def action(op,targets=None,**params):return {'operation':op,'targets':targets or [],'params':params}
def process(pid,purpose,actions,pre=None,post=None,evidence=None,required=None):
 return {'process_id':pid,'purpose':purpose,'input_assembly_types':[],'required_states':required or [],'preconditions':pre or [],'actions':actions,'postconditions':post or [],'invariants':[],'evidence_ids':evidence or []}
def show(oid,visible=True,**changes):return action('transform_state',[oid],visual_updates={oid:{'visible':visible,**changes}})
def attach(source,target,port='end',**params):return action('attach',[source,target],relation='active_site',target_anchor=port,source_anchor='center',offset=[0,0,0],**params)
def detach(source,target):return action('detach',[source,target],relation='active_site')
def extend(oid,start,end):return action('extend',[oid],points=[start,end])
def interpolate(a,b,t):return [x+(y-x)*t for x,y in zip(a,b)]
# Topic-specific editable assembly data, not a hand-authored Manim lesson.
upper=lambda x:[x,1.2-.14*(x+5),0]
lower=lambda x:[x,-1.2+.14*(x+5),0]
lead=lambda x:[x,upper(x)[1]-.24,0]
lag=lambda x:[x,lower(x)[1]+.24,0]
objects=[]
for oid,y,pol in [('template_leading',.15,["3'","5'"]),('template_lagging',-.15,["5'","3'"])]:
 o=obj(oid,'parental_strand',points=[[-5,y,0],[2.5,y,0],[6,y,0]],visible=True,props={'polarity':pol,'parent_assembly':'replication_fork','endpoint_labels':{'start':pol[0],'end':pol[1]}})
 o['anchors']['junction']={'kind':'point','index':1}
 for i in range(8):o['anchors']['pair_'+str(i)]={'kind':'between','a':1,'b':2,'alpha':i/7}
 objects.append(o)
for oid,a,b,color,kind,pol in [
 ('rna_primer_leading',lead(-4.3),lead(-3.7),'#FFB74D','RNA_primer',None),
 ('rna_primer_lagging_1',lag(-1.2),lag(-.6),'#FFB74D','RNA_primer',None),
 ('rna_primer_lagging_2',lag(1.1),lag(1.7),'#FFB74D','RNA_primer',None),
 ('new_leading',lead(-3.7),lead(-3.68),'#69F0AE','nascent_strand',["5'","3'"]),
 ('fragment_1',lag(-1.2),lag(-1.22),'#69F0AE','nascent_strand',["5'","3'"]),
 ('fragment_2',lag(1.1),lag(1.08),'#69F0AE','nascent_strand',["5'","3'"]),
 ('gap_fill',lag(-.6),lag(-.62),'#69F0AE','nascent_strand',None)]:
 objects.append(obj(oid,kind,points=[a,b],color=color,props={'material':'RNA' if kind=='RNA_primer' else 'DNA','endpoint_labels':{'end':pol[1]} if pol else {}},stroke_width=7,endpoint_label_offset=[0,.24 if oid=='new_leading' else -.25,0]))
for oid,asset,label,pos,side in [
 ('primase','primase','Primase / Pol alpha',lead(-4.0),'up'),
 ('polymerase_leading','dna_polymerase','Pol epsilon',lead(-3.7),'up'),
 ('polymerase_lagging','dna_polymerase','Pol delta',lag(-1.2),'down'),
 ('ligase','dna_ligase','Ligase',lag(-1.2),'down')]:
 objects.append(obj(oid,'enzyme',asset=asset,label=label,pos=pos,label_side=side,width=.48 if oid!='primase' else .44,props={'role':label}))
relationships=[{'source':'template_leading','target':'template_lagging','type':'paired_parental_region','source_anchor':'pair_'+str(i),'target_anchor':'pair_'+str(i),'draw_link':'pairing_rung_'+str(i)} for i in range(8)]
identity=cond('stable_components','identity_unchanged')
counts=cond('exactly_two_parental_strands','count_kind',kind='parental_strand',count=2)
assembly={'assembly_id':'replication_fork','assembly_type':'replication_fork','component_ids':[o['object_id'] for o in objects],'relations':relationships,'state_variables':{'phase':'closed'},'anchor_points':{'junction_upper':{'object_id':'template_leading','anchor':'junction'},'ligation_site':{'object_id':'fragment_1','anchor':'start'}},'visual_representation':{'fidelity':'schematic','editable':True},'allowed_transitions':['open_fork','prime','continuous_extension','fragment_synthesis','maturation'],'invariants':[identity,counts],'evidence_ids':['F4','F5','F6','X_7574276a','X_bf28604c']}
phase=lambda val:cond('phase_'+val,'state_is',key='phase',value=val)
opened=[action('transform_state',['template_leading','template_lagging'],visual_updates={'template_leading':{'points':[upper(-5),[2.5,.15,0],[6,.15,0]]},'template_lagging':{'points':[lower(-5),[2.5,-.15,0],[6,-.15,0]]}},state_updates={'phase':'opened'})]
prime=[show('primase'),show('rna_primer_leading'),show('primase',False),action('transform_state',state_updates={'phase':'primed'})]
leading=[show('polymerase_leading'),attach('polymerase_leading','new_leading')]
for i in range(1,9):leading.append(extend('new_leading',lead(-3.7),lead(-3.7+5.2*i/8)))
leading += [detach('polymerase_leading','new_leading'),show('polymerase_leading',False),action('transform_state',state_updates={'phase':'elongating'})]
fragments=[show('primase',True,center=lag(-.9)),show('rna_primer_lagging_1'),show('primase',False),show('polymerase_lagging'),attach('polymerase_lagging','fragment_1')]
for i in range(1,5):fragments.append(extend('fragment_1',lag(-1.2),lag(-1.2-2.3*i/4)))
fragments += [detach('polymerase_lagging','fragment_1'),show('polymerase_lagging',False),show('primase',True,center=lag(1.4)),show('rna_primer_lagging_2'),show('primase',False),show('polymerase_lagging'),attach('polymerase_lagging','fragment_2')]
for i in range(1,5):fragments.append(extend('fragment_2',lag(1.1),lag(1.1-1.7*i/4)))
fragments += [detach('polymerase_lagging','fragment_2'),show('polymerase_lagging',False)]
mature=[action('transform_state',state_updates={'phase':'maturing'}),show('rna_primer_lagging_1',False),show('polymerase_lagging'),attach('polymerase_lagging','gap_fill')]
for i in range(1,5):mature.append(extend('gap_fill',lag(-.6),lag(-.6-.6*i/4)))
mature += [detach('polymerase_lagging','gap_fill'),show('polymerase_lagging',False),show('ligase'),attach('ligase','gap_fill')]
connection=action('connect',['gap_fill','fragment_1'],relation='sealed_nick',source_anchor='end',target_anchor='start')
connection['preconditions']=[cond('nick_endpoints_adjacent','anchor_coincident',['gap_fill','fragment_1'],anchors=['end','start'],tolerance=.03)]
mature += [connection,detach('ligase','gap_fill'),show('ligase',False)]
processes={}
for pid,purpose,acts,pre,post,evi in [
 ('open_fork','Open two continuous parental paths; keep same IDs',opened,[phase('closed')],[phase('opened')],['X_bf28604c']),
 ('prime','Primase/Pol alpha initiation abstraction; produce RNA starting point',prime,[phase('opened')],[phase('primed')],['F5']),
 ('continuous_extension','Continuous leading synthesis on opened region, Pol epsilon tracks actual end',leading,[phase('primed')],[phase('elongating')],['F4','X_7574276a']),
 ('fragment_synthesis','Two separate primers each precede their leftward fragment growth',fragments,[phase('elongating')],[],['F5','F6','X_7574276a']),
 ('maturation','Remove RNA, extend downstream fragment into gap, seal adjacent nick',mature,[phase('elongating')],[cond('nick_joined','relation_exists',['gap_fill','fragment_1'],relation='sealed_nick')],['F6','X_7574276a'])]:
 processes[pid]=process(pid,purpose,acts,pre,post,evi)
# Exact primer-before-extension conditions are injected on the actual first extend actions.
for pid,primer,target in [('continuous_extension','rna_primer_leading','new_leading'),('fragment_synthesis','rna_primer_lagging_1','fragment_1'),('fragment_synthesis','rna_primer_lagging_2','fragment_2')]:
 step=next(a for a in processes[pid]['actions'] if a['operation']=='extend' and a['targets']==[target])
 step['preconditions']=[cond('primer_first_'+target,'visible',[primer])]
constraints=[{**counts,'category':'topology','evidence_ids':['X_bf28604c']},{**identity,'category':'identity'}]
for oid,ev,vec in [('new_leading','event_3_extension',[1,0,0]),('fragment_1','event_4_two_modes',[-1,0,0]),('fragment_2','event_4_two_modes',[-1,0,0]),('gap_fill','event_5_maturation',[-1,0,0])]:
 constraints.append(cond('growth_'+oid,'growth_direction',[oid],unit_vector=vec,during_event=ev,category='mechanism',evidence_ids=['X_7574276a','X_bf28604c'],polarity_basis={'template_object':'template_leading' if oid=='new_leading' else 'template_lagging','template_5prime_side':'right' if oid=='new_leading' else 'left','nascent_3prime_port':'end','diagram_open_region':'left of x2.5'},description='Actual growing-end trajectory must follow the fact-bound antiparallel polarity rule'))
constraints += [cond('sealed_actual_nick','anchor_coincident',['gap_fill','fragment_1'],anchors=['end','start'],tolerance=.04,after_event='event_5_maturation',category='connection',evidence_ids=['F6']),cond('fill_starts_at_downstream_3prime','anchor_coincident',['gap_fill','fragment_2'],anchors=['start','end'],tolerance=.04,after_event='event_5_maturation',category='connection',evidence_ids=['X_7574276a'])]
dna={'scene_id':'dna_section4','topic_id':'dna_replication','objects':objects,'assembly':assembly,'processes':processes,'constraints':constraints,'assets':assets,'assumptions':['Schematic, not molecular structure or scale. One local fork, no chromosome-end/telomerase claim.','Primase/Pol alpha label abstracts RNA initiation and short DNA handoff; individual RNaseH/FEN1 steps omitted.','Show one local primer maturation only; other orange primers remain, final caption must not claim all replication completed.','Parent fork is camera-fixed; synthesis stays on its opened left side. Pol epsilon is the common undisturbed leading-strand teaching model, not an absolute exclusion of Pol delta.','Direction constraint is derived from verified5to3/antiparallel facts plus displayed template endpoints, not a universal sign of x.']}
for o in dna['objects']:o['evidence_ids']=assembly['evidence_ids']
story={'required_event_ids':['event_1_fork','event_2_priming','event_3_extension','event_4_two_modes','event_5_maturation'],'duration_target':30,'title':'DNA replication: priming, leading and lagging','events':json.loads((E.parent/'biology_v2_section4/specs/section4_storyboard_v2.json').read_text())['events']}
write(E/'assemblies/replication_fork.json',assembly);write(E/'scene_ir/dna_blueprint.json',dna);write(E/'scene_ir/dna_storyboard_input.json',story)
for pid,p in processes.items():write(E/'processes/dna_replication'/(pid+'.json'),p)
# Second theme, same representation and operation vocabulary; no new engine branch.
objects=[
 obj('sister_A','chromatid',points=[[-.45,-.85,0],[-.12,0,0],[-.45,.85,0]],color='#69F0AE',visible=True,label='Chromatid A',label_side='down',props={'current_role':'sister_chromatid','sister_id':'sister_B'}),
 obj('sister_B','chromatid',points=[[.45,-.85,0],[.12,0,0],[.45,.85,0]],color='#FFB74D',visible=True,label='Chromatid B',props={'current_role':'sister_chromatid','sister_id':'sister_A'}),
 obj('kinetochore_A','kinetochore',asset='bead',pos=[-.285,0,0],color='#FFFFFF',visible=True,radius=.09),
 obj('kinetochore_B','kinetochore',asset='bead',pos=[.285,0,0],color='#FFFFFF',visible=True,radius=.09),
 obj('pole_left','spindle_pole',asset='bead',pos=[-4,0,0],color='#FFDD55',visible=True,label='Pole',radius=.16),
 obj('pole_right','spindle_pole',asset='bead',pos=[4,0,0],color='#FFDD55',visible=True,label='Pole',radius=.16),
 obj('microtubule_left','spindle_microtubule',points=[[-4,0,0],[-.285,0,0]],color='#B3E5FC',stroke_width=3),
 obj('microtubule_right','spindle_microtubule',points=[[4,0,0],[.285,0,0]],color='#B3E5FC',stroke_width=3)]
# Center ports use component bbox, matching the explicit representation center.
rels=[{'source':'sister_A','target':'sister_B','type':'sister_cohesion'},{'source':'kinetochore_A','target':'sister_A','type':'attachment','target_anchor':'center'},{'source':'kinetochore_B','target':'sister_B','type':'attachment','target_anchor':'center'}]
asm={'assembly_id':'mitotic_spindle_chromosome_set','assembly_type':'mitotic_spindle_chromosome_set','component_ids':[o['object_id'] for o in objects],'relations':rels,'state_variables':{'phase':'unattached'},'anchor_points':{'left_kinetochore':{'object_id':'kinetochore_A','anchor':'center'},'right_kinetochore':{'object_id':'kinetochore_B','anchor':'center'}},'visual_representation':{'fidelity':'schematic','editable':True},'allowed_transitions':['bipolar_attachment','chromatid_separation'],'invariants':[identity,cond('two_physical_chromatids','count_kind',kind='chromatid',count=2)],'evidence_ids':['F1','F3','F4','F5','F8']}
align=[show('microtubule_left'),show('microtubule_right')]
for pole,kt,line in [('pole_left','kinetochore_A','microtubule_left'),('pole_right','kinetochore_B','microtubule_right')]:
 align.append(action('connect',[pole,kt],relation='bipolar_attachment',draw_link=line,source_anchor='center',target_anchor='center'))
align.append(action('transform_state',state_updates={'phase':'aligned'}))
separate=action('split',['sister_A','sister_B'],remove_relation='sister_cohesion',property_updates={'current_role':'daughter_chromosome'},visual_updates={'sister_A':{'label':'Daughter A'},'sister_B':{'label':'Daughter B'}},state_updates={'phase':'separating'})
move=action('move_along_path',['sister_A','sister_B'],paths={'sister_A':[[-2.8,0,0]],'sister_B':[[2.8,0,0]]})
processes={
 'bipolar_attachment':process('bipolar_attachment','Show one duplicated chromosome with opposite-pole kinetochore attachments and metaphase alignment',align,[phase('unattached')],[phase('aligned')],['F4','F5'],['unattached']),
 'chromatid_separation':process('chromatid_separation','Release sister cohesion then move existing sisters to opposite poles; context role becomes daughter chromosome',[separate,move],[phase('aligned'),cond('bipolar_left','relation_exists',['pole_left','kinetochore_A'],relation='bipolar_attachment'),cond('bipolar_right','relation_exists',['pole_right','kinetochore_B'],relation='bipolar_attachment'),cond('sisters_linked','relation_exists',['sister_A','sister_B'],relation='sister_cohesion')],[phase('separating')],['F3','F5','F8'],['aligned'])}
constraints=[{**identity,'category':'identity'},cond('two_objects_no_cloning','count_kind',kind='chromatid',count=2,category='identity'),cond('left_attachment_measured','anchor_coincident',['microtubule_left','kinetochore_A'],anchors=['end','center'],after_event='metaphase',tolerance=.04,category='connection',evidence_ids=['F4','F5']),cond('right_attachment_measured','anchor_coincident',['microtubule_right','kinetochore_B'],anchors=['end','center'],after_event='metaphase',tolerance=.04,category='connection',evidence_ids=['F4','F5']),cond('daughter_role_A','property_is',['sister_A'],key='current_role',value='daughter_chromosome',after_event='anaphase',category='identity',evidence_ids=['F8'])]
mit={'scene_id':'mitosis_short','topic_id':'eukaryotic_mitosis','objects':objects,'assembly':asm,'processes':processes,'constraints':constraints,'assets':assets,'assumptions':['One already-duplicated chromosome, not an entire genome or ploidy count.','Centromere/kinetochore and spindle are schematic; molecular cohesion cleavage not shown.','Same two physical chromatid objects persist, then are called daughter chromosomes after separation.','No DNA replication or homolog pairing occurs in this clip.']}
for o in objects:o['evidence_ids']=asm['evidence_ids']
write(E/'assemblies/mitotic_spindle_chromosome_set.json',asm);write(E/'scene_ir/mitosis_blueprint.json',mit)
write(E/'scene_ir/mitosis_storyboard_input.json',{'required_event_ids':['metaphase','anaphase'],'duration_target':12,'title':'Mitosis: alignment to sister separation','events':[{'id':'metaphase','action':'Establish opposite pole attachments and aligned duplicated chromosome'},{'id':'anaphase','action':'Release cohesion, separate existing sister chromatids to opposite poles'}]})
for pid,p in processes.items():write(E/'processes/mitosis'/(pid+'.json'),p)
write(E/'assets/asset_registry.json',{'assets':assets})
write(E/'scientific_assumptions.json',{'dna':dna['assumptions'],'mitosis':mit['assumptions'],'engineering_preparation':'These are editable component/transition recipes, not a manually rendered experimental lesson. Actual teaching event plans and experimental Python are produced by DeepSeek.'})
print('Two topic assembly datasets and process recipes written')

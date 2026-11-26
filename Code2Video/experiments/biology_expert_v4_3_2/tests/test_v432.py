from pathlib import Path
import sys,copy,json
import pytest
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'src'))
from biology_expert.retrieval_quality import validate_queries,RetrievalQueryInvalid,source_quality,exact_support
from biology_expert.model_reliability import ScientificCausalGraphValidator
from biology_expert.model_repair import apply_model_patch

def typed():
 def state(s,v,kind,producer=None):return {'state_id':s,'subject_ref':'A','property':'phase','value':v,'state_kind':kind,'producer_process_id':producer,'required_by_process_ids':[],'scope':{},'evidence_ids':[],'support':[]}
 return {'schema_version':'1.1','entities':[{'semantic_id':'A'}],'states':[state('I','ready','INITIAL_CONDITION'),state('M','middle','PRODUCED_STATE','P'),state('F','done','PRODUCED_STATE','Q')],'clip_start':{'stage':'ready','existing_entity_refs':['A'],'omitted_processes':[]},'processes':[{'process_semantic_id':'P','precondition_state_refs':['I'],'effect_state_refs':['M'],'temporal_scope':{'start_condition':'begin','end_condition':'middle'},'observables':[]},{'process_semantic_id':'Q','precondition_state_refs':['M'],'effect_state_refs':['F'],'temporal_scope':{'start_condition':'middle','end_condition':'end','after':['P']},'observables':[]}]}
@pytest.mark.parametrize('q',['k','kinesin motor vesicle transport',None,{'query':'mechanism'}])
def test_query_must_array(q):
 with pytest.raises(RetrievalQueryInvalid):validate_queries({'scientific_queries':q})
def test_single_character_rejected():
 with pytest.raises(RetrievalQueryInvalid):validate_queries({'scientific_queries':['k']})
def test_contextual_query_preserved():assert validate_queries({'scientific_queries':['generic motor cargo transport']},{'topic':'cargo transport'})==['generic motor cargo transport']
def test_wrong_context_rejected():
 with pytest.raises(RetrievalQueryInvalid):validate_queries({'scientific_queries':['machine learning network']},{'topic':'cell transport'})
def test_title_not_body():assert source_quality({'title':'Mechanism title','passages':[{'text':'Mechanism title','location':'title'}]})['status']=='FULL_TEXT_UNAVAILABLE'
def test_exact_body_support_not_word_presence():
 e=[{'evidence_id':'E','title':'Title','passages':[{'location':'p1','text':'A generic actor binds its target during the active process and maintains a visible contact.'}]}]
 assert exact_support([{'evidence_id':'E','location':'p1','quote':'actor binds its target'}],e)
 assert not exact_support([{'evidence_id':'E','location':'p1','quote':'actor releases target'}],e)
def test_initial_legal():assert ScientificCausalGraphValidator().validate(typed())['status']=='PASS'
def test_missing_producer():
 m=typed();m['processes'][0]['effect_state_refs']=[];assert any(i['issue_type']=='MISSING_STATE_PRODUCER' for i in ScientificCausalGraphValidator().validate(m)['issues'])
def test_state_search_not_string_match():
 m=typed();m['states'][0]['value']='wrong';m['states'].append(dict(m['states'][0],state_id='REQ',value='ready',state_kind='REQUIRED_PRECONDITION'));m['processes'][0]['precondition_state_refs']=['REQ'];assert ScientificCausalGraphValidator().validate(m)['status']=='REVISE'
def test_concurrent_conflict():
 m=typed();m['processes'][0]['temporal_scope']['concurrent_with']=['Q'];assert any(i['issue_type']=='CONFLICTING_STATE' for i in ScientificCausalGraphValidator().validate(m)['issues'])
def test_truncated_space_not_pass():assert ScientificCausalGraphValidator().validate(typed(),max_states=1)['status']=='STATE_SPACE_INCOMPLETE'
def test_continuous_not_complete():
 m=typed();m['requires_continuous_or_unbounded_reasoning']=True;assert ScientificCausalGraphValidator().validate(m)['status']=='STATE_SPACE_INCOMPLETE'
def test_conflicting_initial():
 m=typed();m['states'].append(dict(m['states'][0],state_id='I2',value='other'));assert any(i['issue_type']=='CONFLICTING_STATE' for i in ScientificCausalGraphValidator().validate(m)['issues'])
def test_unknown_not_true_or_false():
 m=typed();m['states'][0]['state_kind']='UNKNOWN';assert ScientificCausalGraphValidator().validate(m)['status']!='PASS'
def test_irrelevant_color_not_science():
 m=typed();m['visual']={'color':'red'};assert ScientificCausalGraphValidator().validate(m)['status']=='PASS'
def test_legal_parallel():
 m=typed();m['entities'].append({'semantic_id':'B'});m['states'].append(dict(m['states'][1],state_id='B1',subject_ref='B',producer_process_id='R'));m['processes'].append({'process_semantic_id':'R','precondition_state_refs':['I'],'effect_state_refs':['B1'],'temporal_scope':{'start_condition':'begin','end_condition':'end','concurrent_with':['P']},'observables':[]});assert ScientificCausalGraphValidator().validate(m)['status']=='PASS'
def test_unrelated_patch_rejected():
 with pytest.raises(ValueError,match='outside'):apply_model_patch({'entities':[],'relations':[],'processes':[]},{'operations':[{'op':'update','collection':'entities','target_id':'unrelated','fields':{}}]},[{'target_ids':['A'],'issue_id':'I'}],[])
def test_no_deleting_constraints():
 m={'entities':[],'relations':[],'processes':[{'process_semantic_id':'P','observables':[{'constraint_id':'C'}]}]}
 with pytest.raises(ValueError,match='Deleting'):apply_model_patch(m,{'operations':[{'op':'update','collection':'processes','target_id':'P','fields':{'observables':[]}}]},[{'target_ids':['P'],'issue_id':'I'}],[])
def test_failed_patch_does_not_mutate_original():
 m={'entities':[],'relations':[],'processes':[]};before=copy.deepcopy(m)
 with pytest.raises(ValueError):apply_model_patch(m,{'operations':[{'op':'delete','collection':'processes'}]},[],[])
 assert m==before
def test_no_theme_specific_new_modules():
 for name in ['retrieval_quality.py','model_repair.py']:
  text=(R/'src/biology_expert'/name).read_text();assert not any(w in text for w in ['dna_replication','mitosis','vesicle_transport','RNase','kinesin','FEN1'])

def test_dependency_relation_scope_explicit():
 from biology_expert.tools.repair_planner import plan_model_repairs
 m={'entities':[{'semantic_id':'A'},{'semantic_id':'B'}],'relations':[{'semantic_id':'R','source_entity':'A','target_entity':'B'}],'processes':[{'process_semantic_id':'P','participants':[{'entity_ref':'A'},{'entity_ref':'B'}]}]}
 t=plan_model_repairs([{'issue_id':'I','affected_process_ids':['P']}],m);assert 'R' in t[0]['target_ids']
def test_unrelated_page_cannot_close_gap():
 from biology_expert.retrieval_quality import EvidenceEntailmentCheck
 class G:
  def request(self,*args,**kw):return json.dumps({'claims':[{'claim_id':'I','entailment_status':'SUPPORTED','support':[{'evidence_id':'E','location':'p','quote':'invented assertion'}]}]})
 ev=[{'evidence_id':'E','title':'Unrelated','passages':[{'location':'p','text':'This unrelated body explains a completely different mechanism without the required process or actors being described.'}]}]
 assert EvidenceEntailmentCheck(G()).check([{'issue_id':'I'}],ev)['decision']=='INSUFFICIENT_EVIDENCE'
def test_wan_text_mode_no_frames(tmp_path,monkeypatch):
 from video_generation.providers import Wan3Provider
 monkeypatch.setenv('DASHSCOPE_API_KEY','TEST')
 p=Wan3Provider(tmp_path,{'model_id':'wan3.0-video','base_url':'https://example.com'})
 request={'input_mode':'text_to_video','prompt':'generic mechanism','duration':5}
 assert 'media' not in p.prepare_request(request)['input'];assert p.submit(request,dry_run=True)['submitted'] is False

def test_missing_typed_state_binding_not_pass():
 m=typed();m['processes'][0].pop('precondition_state_refs');result=ScientificCausalGraphValidator().validate(m)
 assert result['status']!='PASS' and any(i['issue_type']=='NOT_MEASURED' for i in result['issues'])
def test_explicit_empty_state_bindings_are_valid():
 m=typed();m['processes'][0]['precondition_state_refs']=[]
 assert ScientificCausalGraphValidator().validate(m)['status']=='PASS'
def test_initial_state_identity_effect_maintains_condition():
 m=typed();m['states']=m['states'][:1];m['processes']=m['processes'][:1];m['processes'][0]['effect_state_refs']=['I']
 assert ScientificCausalGraphValidator().validate(m)['status']=='PASS'
def test_initial_state_cannot_be_created_without_requiring_it():
 m=typed();m['processes'][0]['precondition_state_refs']=[];m['processes'][0]['effect_state_refs']=['I','M']
 assert ScientificCausalGraphValidator().validate(m)['status']=='REVISE'

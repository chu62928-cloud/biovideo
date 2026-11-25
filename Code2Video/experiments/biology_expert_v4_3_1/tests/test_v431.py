from pathlib import Path
import sys,copy,json
import pytest
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'src'))
from biology_expert.model_reliability import ScientificCausalGraphValidator,EvidenceSufficiencyAuditor,validate_repair
from video_generation.providers import Wan3Provider,SeedanceProvider

def model():
 return {'initial_states':{'A':'ready'},'entities':[],'relations':[],'processes':[{'process_semantic_id':'P','preconditions':{'A':'ready'},'effects':{'B':'formed'},'temporal_scope':{'end_condition':'B formed'},'observables':[{'constraint_id':'C'}]},{'process_semantic_id':'Q','preconditions':{'B':'formed'},'effects':{'C':'done'},'temporal_scope':{'after':['P'],'end_condition':'C done'},'observables':[]}]}
def test_legal_causal_chain():assert ScientificCausalGraphValidator().validate(model())['status']=='PASS'
def test_unreachable_state():
 m=model();m['processes'][1]['preconditions']={'B':'missing'};assert any(x['issue_type']=='UNREACHABLE_PROCESS' for x in ScientificCausalGraphValidator().validate(m)['issues'])
def test_unreachable_by_path_not_string_presence():
 m=model();m['processes'][0]['preconditions']={'A':'missing'};assert 'Q' not in ScientificCausalGraphValidator().validate(m)['reachable_process_ids']
def test_cycle():
 m=model();m['processes'][0]['temporal_scope']['after']=['Q'];assert any(i['issue_type']=='CYCLIC_DEPENDENCY' for i in ScientificCausalGraphValidator().validate(m)['issues'])
def test_concurrent_conflict():
 m=model();m['processes'][0]['temporal_scope']['concurrent_with']=['Q'];m['processes'][1]['effects']={'B':'other'};assert any(i['issue_type']=='CONCURRENT_STATE_CONFLICT' for i in ScientificCausalGraphValidator().validate(m)['issues'])
def test_missing_initial_is_uncertain():
 m=model();m.pop('initial_states');assert ScientificCausalGraphValidator().validate(m)['status']!='PASS'
def test_missing_support():
 m=model();m['entities']=[{'semantic_id':'X','evidence_ids':[]}];assert EvidenceSufficiencyAuditor().audit({},m,[])['issues']
def test_no_new_evidence_repair_rejected():
 m=model();n=copy.deepcopy(m);n['initial_states']['X']='new';assert not validate_repair(m,n,[],[{}])['accepted']
def test_no_effect_repair_rejected():assert validate_repair(model(),model(),[{}],[{}])['status']=='REPAIR_NOT_EFFECTIVE'
def test_dropped_constraint_rejected():
 m=model();n=copy.deepcopy(m);n['processes'][0]['observables']=[];assert not validate_repair(m,n,[{}],[{}])['accepted']
def request(tmp_path,monkeypatch):
 from PIL import Image
 f=tmp_path/'f.png';Image.new('RGB',(640,360)).save(f);monkeypatch.setenv('DASHSCOPE_API_KEY','TEST_SECRET');return {'first_frame':str(f),'last_frame':str(f),'prompt':'synthetic A moves','duration':5}
class NoNetwork:
 def post(self,*a,**k):raise AssertionError('Unexpected paid submission')
def test_wan_dryrun_no_network(tmp_path,monkeypatch):
 req=request(tmp_path,monkeypatch);p=Wan3Provider(tmp_path,{'model_id':'wan3.0-video','base_url':'https://dashscope.aliyuncs.com'},NoNetwork());assert p.submit(req)['submitted'] is False
def test_resume_no_duplicate(tmp_path,monkeypatch):
 req=request(tmp_path,monkeypatch);monkeypatch.setenv('ENABLE_WAN','1');p=Wan3Provider(tmp_path,{'model_id':'wan3.0-video','base_url':'https://dashscope.aliyuncs.com'},NoNetwork());d=p.submit(req);(tmp_path/'task.json').write_text(json.dumps({'request_sha256':d['request_sha256'],'task_id':'existing','generation_status':'RUNNING'}));assert p.submit(req,dry_run=False,authorized=True)['task_id']=='existing'
def test_wan_requires_auth(tmp_path,monkeypatch):
 req=request(tmp_path,monkeypatch);p=Wan3Provider(tmp_path,{'model_id':'wan3.0-video','base_url':'https://dashscope.aliyuncs.com'},NoNetwork())
 with pytest.raises(PermissionError):p.submit(req,dry_run=False)
def test_seedance_not_selected(tmp_path):assert SeedanceProvider(tmp_path,{}).submit({},dry_run=True)['submitted'] is False
def test_no_topic_specific_reliability_rules():
 text=(R/'src/biology_expert/model_reliability.py').read_text();assert not any(x in text for x in ['dna_replication','mitosis','vesicle_transport','RNase','FEN1','kinesin','dynein'])

from biology_expert.observation_fidelity import review_execution
def test_declared_not_visual():
 result=review_execution({'scientific_observations':[{'time':0,'objects':{},'relations':[{'type':'R'}]}]});assert result['relation_evidence_counts']=={'DECLARED_ONLY':1} and result['pixel_verification']=='NOT_MEASURED'
def test_invisible_not_verified():
 result=review_execution({'scientific_observations':[{'time':0,'objects':{'A':{'center':[0,0,0],'visible':True,'opacity':0,'in_frame':True,'effective_size':True,'instance_id':1}},'relations':[]}]});assert result['issues'][0]['issue']=='VISIBILITY_CONFLICT'
def test_endpoint_mismatch_is_observed_failure():
 result=review_execution({'scientific_observations':[{'time':0,'objects':{},'relations':[{'semantic_id':'R','observation_level':'RUNTIME_OBSERVED','endpoint_matches':False,'target_distance':2}]}]});assert result['issues'][0]['issue']=='DRAWN_ENDPOINT_MISMATCH'
def test_no_secrets_in_sanitized_log():
 from video_generation.providers import sanitized
 assert 'SECRET' not in json.dumps(sanitized({'api_key':'SECRET','Authorization':'SECRET','video_url':'https://host/?token=SECRET'}))
def test_failure_no_fake_video(tmp_path,monkeypatch):
 req=request(tmp_path,monkeypatch);monkeypatch.setenv('ENABLE_WAN','1')
 class Rejected:
  status_code=403
  def json(self):return {'code':'AccessDenied','message':'Not enabled'}
 class Denied:
  def post(self,*a,**kw):return Rejected()
 p=Wan3Provider(tmp_path,{'model_id':'wan3.0-video','base_url':'https://dashscope.aliyuncs.com'},Denied());assert p.submit(req,dry_run=False,authorized=True)['submission_status']=='REJECTED';assert not (tmp_path/'video.mp4').exists();assert 'TEST_SECRET' not in (tmp_path/'task.json').read_text()

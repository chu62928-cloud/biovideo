from pathlib import Path
import sys,copy
import pytest
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'src'))
from biology_expert.model_repair import apply_model_patch
from biology_expert.tools.repair_planner import plan_model_repairs
from biology_expert.typed_science_builder import validate_typed_model

def sample():
 import importlib.util
 p=R/'experiments/biology_expert_v4_3/tests/test_v43.py';spec=importlib.util.spec_from_file_location('fixture_v43',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);m,e,_=mod.fixture();m['scope']['included_processes']=['activity'];m['scope']['excluded_processes']=['actor identity unresolved'];q=m['entities'][0]['support'][0];e[0]['passages'][0]['text']+=' This original body paragraph describes the actors and preserves the specific activity scope.'
 patch={'operations':[],'scope_patch':{'issue_id':'I','fields':{'excluded_processes':[],'simplifications':['Schematic generic activity']},'support':[q]}};tasks=[{'issue_id':'I','target_ids':['scope'],'repair_goal':'Correct contradicted scope statement'}];return m,e,patch,tasks

def test_targeted_scope_correction():
 m,e,p,t=sample();result,changed=apply_model_patch(m,p,t,e);assert result['scope']['excluded_processes']==[] and m['scope']['excluded_processes'];assert 'scope/excluded_processes' in changed;validate_typed_model(result,e)
def test_unrelated_scope_update_rejected():
 m,e,p,t=sample();t[0]['target_ids']=['A']
 with pytest.raises(ValueError,match='targeted'):apply_model_patch(m,p,t,e)
def test_required_process_cannot_disappear():
 m,e,p,t=sample();p['scope_patch']['fields']['included_processes']=[]
 with pytest.raises(ValueError,match='remove original'):apply_model_patch(m,p,t,e)
def test_cannot_hide_mechanism_by_new_exclusion():
 m,e,p,t=sample();p['scope_patch']['fields']['excluded_processes']=['activity']
 with pytest.raises(ValueError,match='new exclusions'):apply_model_patch(m,p,t,e)
def test_no_source_no_scope_repair():
 m,e,p,t=sample();p['scope_patch']['support'][0]['quote']='invented'
 with pytest.raises(ValueError,match='body evidence'):apply_model_patch(m,p,t,e)
def test_cannot_switch_organism():
 m,e,p,t=sample();p['scope_patch']['fields']['organism_context']='another organism'
 with pytest.raises(ValueError,match='organism'):apply_model_patch(m,p,t,e)
def test_scope_target_from_issue_type():
 m,e,p,t=sample();tasks=plan_model_repairs([{'issue_id':'I','issue_type':'SCOPE_MISMATCH'}],m);assert 'scope' in tasks[0]['target_ids']

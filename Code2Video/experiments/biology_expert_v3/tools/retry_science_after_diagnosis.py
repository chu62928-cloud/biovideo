from pathlib import Path
import sys,json,os,time
R=Path('/autodl-tmp/code2biovideo/Code2Video');E=R/'experiments/biology_expert_v3';sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway
from biology_expert.agent import BiologyExpertAgent
from biology_expert.state import write
assert json.loads((E/'tests/test_results.json').read_text())['all_passed'],'Offline regressions required before paid retry'
for line in (R.parent/'.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v.strip().strip('"').strip("'")
# Forensic proof is written before authorization and before the new actual request.
raw=json.loads((E/'logs/models/qwen_raw/v3_10.response.json').read_text())
choice=raw['choices'][0];usage=raw['usage']
assert choice['finish_reason']=='length' and usage['completion_tokens']==9000
diagnosis={'failed_call':'v3_10','root_cause':'TOTAL_OUTPUT_BUDGET_EXHAUSTED_INCLUDING_REASONING','finish_reason':choice['finish_reason'],'completion_tokens':usage['completion_tokens'],'reasoning_tokens':usage['completion_tokens_details']['reasoning_tokens'],'remaining_answer_tokens':usage['completion_tokens']-usage['completion_tokens_details']['reasoning_tokens'],'content_chars':len(choice['message']['content']),'content_tail':choice['message']['content'][-200:],'not_authentication_or_network_error':True,'docs':['https://help.aliyun.com/zh/model-studio/qwen4-max','https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions'],'retry_profile':{'max_completion_tokens':12000,'thinking_budget':4096,'response_format':'json_object','SDK_retries':0,'timeout_seconds':180},'prompt_constraint':'At most3 issues/4 checks; compact descriptions; scientific standards and actual full video preserved'}
write(E/'logs/qwen_retry_diagnosis.json',diagnosis)
rows_path=E/'logs/models/model_calls.json';rows=json.loads(rows_path.read_text())
# The malformed content still has valid usage in the outer API envelope.
for row in rows:
 if row['call_id']=='v3_10':
  row.update(usage=usage,finish_reason='length',response_model=raw['model'],root_cause='MODEL_OUTPUT_TRUNCATED')
write(rows_path,rows)
gateway=ModelGateway(E/'logs/models',qwen_profile={'max_completion_tokens':12000,'thinking_budget':4096})
auth={'authorization_id':'USER_20261124_QWEN_PLUS_2','source':'explicit_user_message','date_beijing':'2026-11-24','provider':'qwen','additional_requests':2,'acknowledged_failed_calls':['v3_10'],'reason':'User authorized two additional Qwen requests after confirming truncation cause; no DeepSeek extension'}
auth_path=gateway.root/'budget_authorizations.json'
if not auth_path.exists():gateway.resume_authorized(auth)
else:assert any(a['authorization_id']==auth['authorization_id'] for a in json.loads(auth_path.read_text()))
agent=BiologyExpertAgent(E,gateway)
out=json.loads((E/'test_B_revalidated_result.json').read_text())
artifacts={'code':Path(out['candidate_code']).read_text(),'trace':json.loads(Path(out['candidate_trace']).read_text()),'video':out['candidate_video'],'trace_ref':out['candidate_trace']}
pack=json.loads((E/'knowledge/dna_replication/knowledge_pack.json').read_text())
story=json.loads((R/'experiments/biology_v2_section4/specs/section4_storyboard_v2.json').read_text())
print('RETRY_AFTER_CONFIRMED_DIAGNOSIS',diagnosis['root_cause'],'limits',gateway.limits,flush=True)
review=agent.review('RENDERED_VIDEO',artifacts,{'knowledge_pack':pack,'storyboard':story})
write(E/'reviews/video/final_retry_review.json',review)
out['science_review']=review
out['latest_science_retry']={'review_id':review['review_id'],'decision':review['decision'],'full_MP4':True,'new_model_calls':1,'does_not_replace_old_error':True}
out['decision']='PASS' if review['decision']=='PASS' and out['accepted'] else 'NEEDS_HUMAN_REVIEW'
write(E/'test_B_revalidated_result.json',out)
print('RETRY_RESULT',review['decision'],review.get('targeted_gap_direction'),'issues',len(review['issues']),flush=True)

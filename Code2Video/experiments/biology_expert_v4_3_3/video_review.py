from common import *
g=gateway()
os.environ['QWEN_MODEL']='qwen3.8-27b'
g.qwen_profile=dict(include_grid=False,max_completion_tokens=7000,thinking_budget=2048)
p=E/'videos/CANDIDATE_mitosis.mp4'
prompt='Review this actual English high school teaching video. Observe which sister chromatids, kinetochores and microtubules are visibly connected when and how they move. Check candidate caption, all event times, terms, readable labels, unexplained changes and limitations. Identify exact seconds for issues. Return JSON {science:{decision,issues},visual:{decision,issues},pedagogy:{accuracy,terms,motion,density,readability,objective},limitations:[]}. Decisions PASS, REVISE or NEEDS_HUMAN_REVIEW.'
write(E/'videos/independent_review.json',parse_json(g.request('qwen','video_review_v433',prompt,video=p)))

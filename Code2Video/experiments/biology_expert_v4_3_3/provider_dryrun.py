from common import *
from video_generation.providers import Wan3Provider,SeedanceProvider
design=read(R/'experiments/biology_expert_v4_3_2/visual_design.json')
req=dict(input_mode='text_to_video',prompt=design['combined_prompt'],duration=5,resolution='480P')
gateway()
write(E/'providers.json',{key:provider.submit(req,dry_run=True) for key,provider in [('wan',Wan3Provider(E/'dryrun/wan',{'model_id':'wan3.0-video','base_url':'https://ws-t97wmnhtb5p967oq.cn-beijing.maas.aliyuncs.com'})),('seedance',SeedanceProvider(E/'dryrun/seedance',{}))]})

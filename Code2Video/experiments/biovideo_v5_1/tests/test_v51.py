import pytest
from biology_expert.product import bind_decision

@pytest.mark.parametrize("old_metadata", [{}, {"observation_id":"O4"}, {"based_on_observation_ids":["O2"]}])
def test_reference_binding(old_metadata):
    action=dict(old_metadata,tool='repair_scene',scene_id='section_1',issue_id='I1')
    review={'video_sha256':'current'}
    bound=bind_decision(action,review,'current',{'I1':{}})
    assert bound['video_sha256']=='current'
    with pytest.raises(ValueError,match='Stale'):
        bind_decision(action,review,'other',{'I1':{}})
    with pytest.raises(ValueError,match='Unknown'):
        bind_decision(dict(action,scene_id='invalid'),review,'current',{'I1':{}})

"""Check typed observation transport against captured real-server results."""
import json
from pathlib import Path

from mcmcp.models import InspectBlockResult


def test_live_state_and_collision_survive_typed_public_transport():
    capture = json.loads((Path(__file__).parents[1] / 'body/test/fixtures/a13-block-geometry.json').read_text())
    calls = [row for row in capture['confirmed_probe']['calls'] if row['tool']=='minecraft_inspect_block']
    for row in calls:
        original = row['result']
        typed = InspectBlockResult.model_validate(original).model_dump(mode='json')
        assert typed['properties']==original['properties']
        assert typed['collision_shapes']==original['collision_shapes']
    furnace = next(row['result'] for row in calls if row['result']['block_name']=='furnace')
    assert furnace['properties']['lit'] is False
    assert furnace['collision_shapes']==[[0,0,0,1,1,1]]
    air = calls[0]['result']
    assert air['collision_shapes']==[]
    old = {key:value for key,value in air.items() if key not in ('properties','collision_shapes')}
    typed_old = InspectBlockResult.model_validate(old)
    assert typed_old.properties is None
    assert typed_old.collision_shapes is None

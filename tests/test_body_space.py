"""Check collision permission with the captured suffocation pose."""
import json
from pathlib import Path

from mcmcp.geometry import player_intersects_cell
from mcmcp.models import Vec3f, Vec3i


def test_actual_placement_overlaps_player_but_projected_floor_and_side_do_not():
    capture = json.loads((Path(__file__).parents[1] / "body/test/fixtures/a13-body-space.json").read_text())
    feet = Vec3f.model_validate(capture["feet"])
    cell = Vec3i.model_validate(capture["placed_inside"])
    assert player_intersects_cell(feet, cell)
    assert not player_intersects_cell(feet, cell.model_copy(update={"y": cell.y - 1}))
    assert not player_intersects_cell(feet, cell.model_copy(update={"x": cell.x + 2}))

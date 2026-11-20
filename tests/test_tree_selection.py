from mcmcp.body_models import BodyBlock
from mcmcp.models import Vec3i
from mcmcp.runtime import _tree_logs


def cell(x, y, z, name):
    return BodyBlock(position=Vec3i(x=x, y=y, z=z), name=name, display_name=name, replaceable=False)


def test_touching_branch_preserves_neighboring_rooted_trunk():
    cells = [cell(x, y, 0, "birch_log") for x in (0, 2) for y in range(3)]
    cells += [cell(x, -1, 0, "dirt") for x in (0, 2)]
    cells += [cell(1, 2, 0, "birch_log"), cell(1, 3, 0, "birch_leaves")]
    for x in (0, 2):
        logs = _tree_logs(cells, Vec3i(x=x, y=1, z=0))
        assert [(b.position.x, b.position.y) for b in logs] == [(x, 0), (x, 1), (x, 2), (1, 2)]


def test_separate_canopy_does_not_turn_a_post_into_a_tree():
    cells = [cell(0, 0, 0, "oak_log"), cell(2, 0, 0, "oak_log"), cell(2, 1, 0, "oak_leaves")]
    assert _tree_logs(cells, cells[0].position) == []


def test_large_spruce_keeps_all_four_trunk_columns():
    cells = [cell(x, y, z, "spruce_log") for x in (0, 1) for z in (0, 1) for y in (0, 1)]
    cells += [cell(x, -1, z, "dirt") for x in (0, 1) for z in (0, 1)]
    cells.append(cell(1, 2, 1, "spruce_leaves"))
    assert len(_tree_logs(cells, cells[0].position)) == 8

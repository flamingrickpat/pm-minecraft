"""Find normal walk routes and pillar columns in the live cave dump."""

import json
from collections import deque


data = json.load(open(r"C:\Temp\Chungus\live_cave_geometry.json", encoding="utf-8"))
blocks = {(cell["x"], cell["y"], cell["z"]): cell["name"] for cell in data["cells"]}
empty = {"air", "cave_air", "void_air", "tall_grass", "grass", "moss_carpet"}


def standable(cell):
    x, y, z = cell
    return (
        blocks.get((x, y - 1, z), "unloaded") not in empty | {"unloaded"}
        and blocks.get((x, y, z), "unloaded") in empty
        and blocks.get((x, y + 1, z), "unloaded") in empty
    )


start = (2, 65, 25)
queue = deque([start])
previous = {start: None}
while queue:
    x, y, z = queue.popleft()
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for dy in (-1, 0, 1):
            next_cell = (x + dx, y + dy, z + dz)
            if next_cell not in previous and standable(next_cell):
                previous[next_cell] = (x, y, z)
                queue.append(next_cell)


def open_height(cell):
    x, y, z = cell
    height = 0
    while blocks.get((x, y + 2 + height, z), "unloaded") in empty:
        height += 1
    return height


candidates = sorted(
    ((open_height(cell), cell) for cell in previous if open_height(cell) >= 4), reverse=True
)
top = max(previous, key=lambda cell: cell[1])
print(f"start={start} reachable={len(previous)} top={top} open_above={open_height(top)}")
print("pillar_candidates=" + repr(candidates[:20]))

for _, destination in candidates[:3] + [(0, top)]:
    path = []
    cell = destination
    while cell is not None:
        path.append(cell)
        cell = previous[cell]
    path.reverse()
    print(f"path_to={destination} steps={len(path) - 1} path={path}")

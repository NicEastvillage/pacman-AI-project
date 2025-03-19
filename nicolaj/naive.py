import game
from nicolaj.my_state import MyGameState


def get_naive_action(walls: game.Grid, state: MyGameState):
    # Djikstra's algorithm to find nearest food

    width, height = walls.width, walls.height

    queue = [(state.pacman[0], state.pacman[1], None)]  # (x, y, first_act_in_path)
    visited = set()

    while queue:
        x, y, act = queue.pop(0)

        if (x, y) in visited:
            continue
        visited.add((x, y))

        if state.food[x][y]:
            assert act is not None
            return act

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not walls[nx][ny]:
                queue.append((nx, ny, act or (dx, dy)))

    assert False

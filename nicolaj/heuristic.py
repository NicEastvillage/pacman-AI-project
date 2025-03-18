import game
from nicolaj.my_state import COST_OF_LOSING, MyGameState
from nicolaj.static_info import StaticInfo


def find_food_clusters(food: game.Grid):
    width, height = food.width, food.height
    marked = game.Grid(width, height)  # Visited cells
    clusters = []

    def flood_fill(x, y, cluster):
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if not (0 <= cx < width and 0 <= cy < height):
                continue
            if marked[cx][cy] or not food[cx][cy]:
                continue

            marked[cx][cy] = True
            cluster.append((cx, cy))

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((cx + dx, cy + dy))

    for x in range(width):
        for y in range(height):
            if food[x][y] and not marked[x][y]:
                cluster = []
                flood_fill(x, y, cluster)
                clusters.append(cluster)

    return clusters


def approach1(x: float) -> float:
    return x / (x + 1)


def heuristic(static_info: StaticInfo, state: MyGameState) -> float:
    if state.is_loss():
        return COST_OF_LOSING
    if state.is_win():
        return 0

    pacman_dist = state.food.width * state.food.height
    for x in range(state.food.width):
        for y in range(state.food.height):
            if state.food[x][y]:
                dist = static_info.floyd_warshall.dist[state.pacman[0]][state.pacman[1]][x][y]
                if dist < pacman_dist:
                    pacman_dist = dist

    clusters = find_food_clusters(state.food)

    smallest_dist_between = state.food.width * state.food.height
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            for x, y in clusters[i]:
                for a, b in clusters[j]:
                    dist = static_info.floyd_warshall.dist[x][y][a][b] - 1
                    if dist < smallest_dist_between:
                        smallest_dist_between = dist

    food_left = state.food.count()
    return food_left + approach1(float(pacman_dist)) * int(food_left > 1)

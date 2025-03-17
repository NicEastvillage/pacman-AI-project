
def tuple_replace[T](tup: Tuple[T, ...], ix: int, val: T) -> Tuple[T, ...]:
    return tup[:ix] + (val,) + tup[ix + 1:]


class TSPLookup:
    def __init__(self, graph: Graph):
        # A mapping from a start node id (pacman current pos) and a list of fully unvisited
        # graph elements (nodes + edges) to the cost of visiting all unvisited nodes and edges
        # from the start node according to Djikstras algorithm
        self.smart_cost: Dict[Tuple[int, Tuple[bool, ...]]] = {}
        self.build_smart_cost_djikstra(graph)

    def get(self, rstate):
        return 0

    def build_smart_cost_djikstra(self, graph):
        print('Using Djikstra to prepare heuristic..', end='')
        node_count = len(graph.nodes)
        el_count = node_count + len(graph.edges)

        all_visitied = tuple([False] * el_count)
        queue = []
        passed = set()

        # Queue "start" states
        for n in graph.nodes:
            heapq.heappush(queue, (0, (n.id, all_visitied)))
            self.smart_cost[(n.id, all_visitied)] = 0

        debug_prev_cost = -1
        while queue:
            cur_cost, cur = heapq.heappop(queue)
            if cur in passed:
                continue
            passed.add(cur)

            if cur_cost > debug_prev_cost:
                print(str(cur_cost) + '..', end='')
                debug_prev_cost = cur_cost

            for succ, w in _successor(graph, cur):
                if succ[1][0]:
                    continue  # Node 0 is always false. It is the start node
                if succ not in passed:
                    succ_cost_by_cur = cur_cost + w
                    if succ_cost_by_cur < self.smart_cost.get(succ, float('inf')):
                        self.smart_cost[succ] = succ_cost_by_cur
                        heapq.heappush(queue, (succ_cost_by_cur, succ))
        print('')


def _successor(graph: Graph, dn: Tuple[int, Tuple[bool, ...]]) -> Iterator[Tuple[Tuple[int, Tuple[bool, ...]], int]]:
    node_count = len(graph.nodes)
    nid, has_food = dn
    initial = not np.array(has_food).any()
    for i, edge in enumerate(graph.edges):
        if has_food[node_count + i]:
            continue  # We could not have come from this edge, it has food
        if not (edge.i == nid or edge.j == nid):
            continue  # This edge does not end at our current node

        new_node = edge.j if edge.i == nid else edge.i

        if has_food[new_node]:
            # We could not have come from this node, it has food.
            # But we might want to do the edge and then turn around.
            if edge.weight <= 1:
                # This edge is too short to have food on it
                continue

            # Only edge had food (if initial, then cost -1 here since last step to the node is unnecessary)
            has_food_edge = tuple_replace(has_food, node_count + i, True)
            w = 2 * edge.weight - 2
            yield (nid, has_food_edge), w

            continue

        if not initial:
            # Neither node or edge had food
            yield (new_node, has_food), edge.weight

        # Only node
        if new_node != nid:
            has_food_node = tuple_replace(has_food, nid, True)
            yield (new_node, has_food_node), edge.weight

        if edge.weight <= 1:
            # This edge is too short to have food on it
            continue

        # Both node and edge had food
        has_food_both = tuple_replace(tuple_replace(has_food, nid, True), node_count + i, True)
        yield (new_node, has_food_both), edge.weight

        # Only edge had food (if initial, then cost -1 here since last step to the node is unnecessary)
        has_food_edge = tuple_replace(has_food, node_count + i, True)
        w = edge.weight - 1 if initial else edge.weight
        yield (new_node, has_food_edge), w
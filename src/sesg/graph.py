"""Graph module.

This module is responsible to perform graph operations. In our context,
we will perform operations on a correlation (or citation) graph.
"""

from collections import defaultdict, deque
from typing import Optional

from graphviz import Digraph


def edges_to_adjacency_list(
    edges: list[tuple[int, int]],
    *,
    directed: bool = True,
) -> dict[int, list[int]]:
    """Given a list of edges, return an adjacency list.

    Args:
        edges (list[tuple[int, int]]): A list of tuples, where each tuple represents an edge in the graph. Each tuple contains two integers representing the nodes that the edge connects.
        directed (bool): Wheter the edges are directed or not. Defaults to True

    Returns:
        A dict mapping node IDs to their list of neighbors.

    Examples:
        >>> edges = [(1, 2), (2, 3), (2, 4)]
        >>>
        >>> edges_to_adjacency_list(edges)
        {1: [2], 2: [3, 4]}
        >>> edges_to_adjacency_list(edges, directed=False)
        {1: [2], 2: [1, 3, 4], 3: [2], 4: [2]}
    """  # noqa: E501
    adjacency_list: dict[int, list[int]] = defaultdict(list)

    for u, v in edges:
        adjacency_list[u].append(v)

        if not directed:
            adjacency_list[v].append(u)

    return dict(adjacency_list)


def directed_adjacency_list_to_undirected(
    adjacency_list: dict[int, list[int]],
) -> dict[int, list[int]]:
    """Converts a directed adjacency list to an undirected adjacency list.

    Args:
        adjacency_list (dict[int, list[int]]): A dict mapping node IDs to their list of neighbors.

    Returns:
        A mapping of node IDs to their list of neighbors in an undirected graph.

    Examples:
        >>> directed_adjacency_list_to_undirected({1: [2, 3], 2: [3, 4], 3: [4]})
        {1: [2, 3], 2: [1, 3, 4], 3: [1, 2, 4], 4: [2, 3]}

        >>> directed_adjacency_list_to_undirected({2: [1], 3: [1, 2], 4: [2, 3]})
        {2: [1, 3, 4], 1: [2, 3], 3: [1, 2, 4], 4: [2, 3]}
    """  # noqa: E501
    undirected_adjacency_list: dict[int, list[int]] = defaultdict(list)

    for node, neighbors in adjacency_list.items():
        for neighbor in neighbors:
            undirected_adjacency_list[node].append(neighbor)
            undirected_adjacency_list[neighbor].append(node)

    return dict(undirected_adjacency_list)


def _breadth_first_search(
    *,
    adjacency_list: dict[int, list[int]],
    starting_node: int,
) -> list[int]:
    """Runs breadth first search on a graph. Inspired by this [blog](https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/).

    Args:
        adjacency_list (dict[int, list[int]]): A dict mapping node IDs to their list of neighbors.
        starting_node (int): Node where to start the search.

    Returns:
        List of nodes connected to the starting node by a path.

    Examples:
        >>> adjacency_list = {
        ...     1: [2],
        ...     2: [3, 4],
        ...     4: [5, 6]
        ... }
        >>> _breadth_first_search(adjacency_list=adjacency_list, starting_node=2)
        [2, 4, 6, 5, 3]
    """  # noqa: E501
    reachable_nodes: list[int] = []
    q: deque[int] = deque()
    visited: dict[int, bool] = defaultdict(lambda: False)

    s = starting_node
    q.append(s)
    visited[s] = True

    while len(q) != 0:
        s = q.pop()
        reachable_nodes.append(s)

        if s not in adjacency_list:
            continue

        for adjacent_node in adjacency_list[s]:
            if not visited[adjacent_node]:
                q.append(adjacent_node)
                visited[adjacent_node] = True

    return reachable_nodes


def serial_breadth_first_search(
    *,
    adjacency_list: dict[int, list[int]],
    starting_nodes: list[int],
) -> list[int]:
    """Runs many breadth first searches on a graph, using all of the given starting nodes.

    Args:
        adjacency_list (dict[int, list[int]]): A dict mapping node IDs to their list of neighbors.
        starting_nodes (list[int]): List of nodes where to start the search.

    Returns:
        List of nodes connected to each one of the starting nodes by a path. The list of nodes is free of duplicates.

    Examples:
        >>> adjacency_list = {
        ...     1: [2],
        ...     2: [3, 4],
        ...     4: [5, 6],
        ...     7: [6, 8, 9]
        ... }
        >>> serial_breadth_first_search(adjacency_list=adjacency_list, starting_nodes=[4, 7])
        [4, 5, 6, 7, 8, 9]
    """  # noqa: E501
    reachable_nodes: list[int] = []

    for starting_node in starting_nodes:
        result = _breadth_first_search(
            adjacency_list=adjacency_list,
            starting_node=starting_node,
        )

        reachable_nodes.extend(result)

    # set() will remove any duplicate nodes
    return list(set(reachable_nodes))


def create_citation_graph(
    *,
    adjacency_list: dict[int, list[int]],
    tooltips: dict[int, str],
    results_list: Optional[list[int]] = None,
) -> Digraph:
    """Creates a `graphviz.Digraph` instance with the following properties.

    - Filled nodes: nodes on the results list.
    - Bold nodes: nodes found via BFS using the results list as starting nodes.
    - Dashed nodes: nodes that are not on the results list, neither found via BFS.

    Args:
        adjacency_list (dict[int, list[int]]): A dict mapping node IDs to their list of neighbors.
        tooltips (list[str]): A dict mapping node IDs to their tooltip.
        results_list (Optional[list[int]]): List of nodes where to start a BFS. If none, will be set to an empty list.

    Returns:
        A graphviz dot object with the said properties.

    Examples:
        >>> adjacency_list = {1: [2], 2: [3, 4], 3: [4, 5], 4: [6], 5: [7]}
        >>> tooltips = {1: "Paper 1", 2: "Paper 2", 3: "Paper 3", 4: "Paper 4", 5: "Paper 5", 6: "Paper 6", 7: "Paper 7"}
        >>> results_list = [1, 3]
        >>> g = create_citation_graph(adjacency_list=adjacency_list, tooltips=tooltips, results_list=results_list)
        >>> g.render(  # doctest: +SKIP
        ...     filename="graph.dot",
        ...     directory="out",
        ...     format="pdf",
        ... )
    """  # noqa: E501
    if results_list is None:
        results_list = list()

    graph = Digraph(strict=True)

    node_padding = len(str(len(tooltips)))

    def format_node(node_id: int) -> str:
        return str(node_id).zfill(node_padding)

    # adding nodes
    # all nodes will be created as "not found" (with dashed style)
    for node, tooltip in tooltips.items():
        graph.node(
            format_node(node),
            tooltip=tooltip,
            style="dashed",
        )

    # adding edges
    for node, neighbors in adjacency_list.items():
        for neighbor in neighbors:
            graph.edge(
                format_node(node),
                format_node(neighbor),
            )

    nodes_found_with_bfs = serial_breadth_first_search(
        adjacency_list=adjacency_list,
        starting_nodes=results_list,
    )

    # Since we care more about nodes that are on the results list,
    # first we tag the ones found via BFS, and later,
    # the ones on the results list.
    # This way, if a same node that is on the results list, is also found via BFS,  # noqa: E501
    # in the final graph, it will be tagged as it is on the results list.

    # tagging nodes that can be found via BFS
    # on the nodes of the results list
    for node in nodes_found_with_bfs:
        graph.node(
            format_node(node),
            shape="circle",
            style="bold",
            tooltip=tooltips[node],
        )

    # tagging nodes on results_list
    for node in results_list:
        graph.node(
            format_node(node),
            shape="circle",
            style="filled",
            tooltip=tooltips[node],
        )

    return graph

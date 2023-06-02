"""Graph module.

This module is responsible to perform graph operations. In our context,
we will perform operations on a correlation (or citation) graph.
"""

from collections import defaultdict, deque
from typing import Optional

from graphviz import Digraph  # type: ignore


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


def snowballing(
    *,
    adjacency_list: dict[int, list[int]],
    start_set: list[int],
) -> list[int]:
    """Runs snowballing on a graph represented by an adjacency list.

    Snowballing is performed by running a BFS (breadth first search) on each study of the start set

    Args:
        adjacency_list (dict[int, list[int]]): A dict mapping a study ID to it's neighbors (citation/references).
        start_set (list[int]): List with the ID of the studies of the start set.

    Returns:
        List of study IDs that can be found via snowballing on the start set.

    Examples:
        >>> adjacency_list = {
        ...     1: [2],
        ...     2: [3, 4],
        ...     4: [5, 6],
        ...     7: [6, 8, 9]
        ... }
        >>> snowballing(adjacency_list=adjacency_list, start_set=[4, 7])
        [4, 5, 6, 7, 8, 9]
    """  # noqa: E501
    snowballing_nodes: list[int] = []

    for node in start_set:
        result = _breadth_first_search(
            adjacency_list=adjacency_list,
            starting_node=node,
        )

        snowballing_nodes.extend(result)

    snowballing_nodes_without_duplicates = list(set(snowballing_nodes))

    return snowballing_nodes_without_duplicates


def create_citation_graph(
    *,
    adjacency_list: dict[int, list[int]],
    studies_titles: dict[int, str],
    start_set: Optional[list[int]] = None,
) -> Digraph:
    """Creates a `graphviz.Digraph` instance with the following properties.

    - Filled nodes: nodes on the start set.
    - Bold nodes: nodes found via snowballing on the start set.
    - Dashed nodes: nodes that are not on the start set, neither were found via snowballing.

    Args:
        adjacency_list (dict[int, list[int]]): A dict mapping a study ID to it's neighbors (citations/references).
        studies_titles (list[str]): A dict mapping a study ID to it's title.
        start_set (Optional[list[int]]): Start set. List of study IDs. If None, will default to an empty list.

    Returns:
        A graphviz dot object with the said properties.

    Examples:
        >>> adjacency_list = {1: [2], 2: [3, 4], 3: [4, 5], 4: [6], 5: [7]}
        >>> tooltips = {1: "Paper 1", 2: "Paper 2", 3: "Paper 3", 4: "Paper 4", 5: "Paper 5", 6: "Paper 6", 7: "Paper 7"}
        >>> results_list = [1, 3]
        >>> g = create_citation_graph(adjacency_list=adjacency_list, tooltips=tooltips, results_list=results_list)  # doctest: +SKIP
        >>> g.render(  # doctest: +SKIP
        ...     filename="graph.dot",
        ...     directory="out",
        ...     format="pdf",
        ... )
    """  # noqa: E501
    if start_set is None:
        start_set = []

    graph = Digraph(strict=True)

    node_padding = len(str(len(studies_titles)))

    def format_node(node_id: int) -> str:
        return str(node_id).zfill(node_padding)

    # adding nodes
    # all nodes will be created as "not found" (with dashed style)
    for node, tooltip in studies_titles.items():
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

    snowballing_nodes = snowballing(
        adjacency_list=adjacency_list,
        start_set=start_set,
    )

    # Since we care more about nodes that are on the start set,
    # first we mark the ones found via snowballing, and later,
    # the ones on the start set.
    # This way, if the same node appears both in the start set and via snowballing,
    # it will be marked as on the start set.

    # marking nodes that can be found via snowballing
    for node in snowballing_nodes:
        graph.node(
            format_node(node),
            shape="circle",
            style="bold",
            tooltip=studies_titles[node],
        )

    # marking nodes of the start set
    for node in start_set:
        graph.node(
            format_node(node),
            shape="circle",
            style="filled",
            tooltip=studies_titles[node],
        )

    return graph

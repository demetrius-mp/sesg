from collections import defaultdict, deque
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

from graphviz import Digraph


def edges_to_adjacency_list(
    edges: Iterable[Tuple[int, int]],
    directed: bool = True,
) -> Mapping[int, Sequence[int]]:
    """Given a list of edges, return an adjacency list.

    Args:
        edges (Iterable[Tuple[int, int]]): A list of tuples, where each tuple represents an edge in the graph. Each tuple contains two integers representing the nodes that the edge connects.
        directed (bool): Wheter the edges are directed or not. Defaults to True

    Returns:
        An adjacency list represented as a mapping, where each key is a node and the value is a list of nodes that are connected to the key node.

    Examples:
        >>> edges = [(1, 2), (2, 3), (2, 4)]
        >>>
        >>> edges_to_adjacency_list(edges)
        {1: [2], 2: [3, 4]}
        >>> edges_to_adjacency_list(edges, directed=False)
        {1: [2], 2: [1, 3, 4], 3: [2], 4: [2]}
    """  # noqa: E501
    adjacency_list: Mapping[int, List[int]] = defaultdict(list)

    for u, v in edges:
        adjacency_list[u].append(v)

        if not directed:
            adjacency_list[v].append(u)

    return dict(adjacency_list)


def breadth_first_search(
    adjacency_list: Mapping[int, Sequence[int]],
    starting_node: int,
) -> Sequence[int]:
    """Runs breadth first search on a graph.
    Inspired by this [blog](https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/).


    Args:
        adjacency_list (Mapping[int, Sequence[int]]): Adjacency list that represents the graph.
        starting_node (int): Node where to start the search.

    Returns:
        List of nodes connected to the starting node by a path.

    Examples:
        >>> adjacency_list = {
        ...     1: [2],
        ...     2: [3, 4],
        ...     4: [5, 6]
        ... }
        >>> breadth_first_search(adjacency_list, 2)
        [2, 4, 6, 5, 3]
    """  # noqa: E501

    reachable_nodes: List[int] = []
    q: deque[int] = deque()
    visited: Mapping[int, bool] = defaultdict(lambda: False)

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
    adjacency_list: Mapping[int, Sequence[int]],
    starting_nodes: Iterable[int],
) -> Sequence[int]:
    """Runs many breadth first searches on a graph, using all of the given starting nodes.

    Args:
        adjacency_list (Mapping[int, Sequence[int]]): Adjacency list that represents the graph.
        starting_nodes (Iterable[int]): List of nodes where to start the search.

    Returns:
        Sequence[int]: List of nodes connected to each one of the starting nodes by a path.
        The list of nodes is free of duplicates.

    Examples:
        >>> adjacency_list = {
        ...     1: [2],
        ...     2: [3, 4],
        ...     4: [5, 6],
        ...     7: [8, 9]
        ... }
        >>> serial_breadth_first_search(adjacency_list, [4, 7])
        [4, 5, 6, 7, 8, 9]
    """  # noqa: E501
    reachable_nodes: List[int] = []

    for starting_node in starting_nodes:
        result = breadth_first_search(
            adjacency_list=adjacency_list,
            starting_node=starting_node,
        )

        reachable_nodes.extend(result)

    # set() will remove any duplicate nodes
    return list(set(reachable_nodes))


def create_citation_graph(
    edges: Iterable[Tuple[int, int]],
    titles: Sequence[str],
    results_list: Optional[Sequence[int]] = list(),
    node_labels: Optional[Sequence[int]] = None,
) -> Digraph:
    r"""Creates a `graphviz.Digraph` instance with the following properties:
    - Filled nodes: nodes on the results list.
    - Bold nodes: nodes found via BFS on the results list.
    - Dashed nodes: nodes that are not on the results list, neither found via BSB on the results list.

    Args:
        edges (Iterable[Tuple[int, int]]): Edges of the graph. **Must** use 0-based indexing.
        titles (Sequence[str]): List of the title of the studies, where Node `i` has title `titles[i]`, following a zero-based indexing.
        results_list (Optional[Sequence[int]]): List of nodes found via Scopus Search. Defaults to an empty list.
        node_labels (Optional[Sequence[int]]): Labels to use on the nodes. If set to None, will use 1-based indexing.

    Examples:
        >>> g = create_citation_graph(
        ...     edges=[(0, 1), (1, 2), (1, 3), (4, 5)],
        ...     titles=["1", "2", "3", "4", "5", "6"],
        ... )
        >>> g.source
        'strict digraph {\n\t01 [shape=circle style=dashed tooltip=1]\n\t02 [shape=circle style=dashed tooltip=2]\n\t03 [shape=circle style=dashed tooltip=3]\n\t04 [shape=circle style=dashed tooltip=4]\n\t05 [shape=circle style=dashed tooltip=5]\n\t06 [shape=circle style=dashed tooltip=6]\n\t01 -> 02\n\t02 -> 03\n\t02 -> 04\n\t05 -> 06\n\tlabel="Dashed -> Not found\\nBold -> Snowballing\\nFilled -> Search"\n}\n'

    Returns:
        Digraph: A `graphviz.Digraph` instance with the said properties.
    """  # noqa: E501
    number_of_nodes = len(titles)

    if results_list is None:
        results_list = list()

    if node_labels is None:
        node_labels = list(range(1, number_of_nodes + 1))

    graph = Digraph(strict=True)

    # adding all nodes, tagging all as **not found**
    for i in range(number_of_nodes):
        graph.node(
            f"{node_labels[i]:02}",
            shape="circle",
            style="dashed",
            tooltip=titles[i],
        )

    # adding citation edges
    for i, j in edges:
        graph.edge(f"{node_labels[i]:02}", f"{node_labels[j]:02}")

    nodes_reachable_via_snowballing_on_results = serial_breadth_first_search(
        adjacency_list=edges_to_adjacency_list(edges=edges),
        starting_nodes=results_list,
    )

    # NOTE: Since we care more about nodes that are found via search,
    # first we tag the ones found via snowballing, and later,
    # the ones found via Scopus Search.
    # This way, if a same node that is found via Scopus Search, is found via snowballing,  # noqa: E501
    # in the final graph, it will be tagged as found via Scopus search

    # tagging nodes that can be found via snowballing
    # on the studies found via search
    for i in nodes_reachable_via_snowballing_on_results:
        graph.node(
            f"{node_labels[i]:02}",
            shape="circle",
            style="bold",
            tooltip=titles[i],
        )

    # tagging nodes found via search
    for i in results_list:
        graph.node(
            f"{node_labels[i]:02}",
            shape="circle",
            style="filled",
            tooltip=titles[i],
        )

    graph.attr(label=r"Dashed -> Not found\nBold -> Snowballing\nFilled -> Search")

    return graph

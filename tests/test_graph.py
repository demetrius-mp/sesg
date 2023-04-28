from sesg import graph


def test_edges_to_adjacency_list_should_return_empty_dict_when_edges_list_is_empty():
    result = graph.edges_to_adjacency_list([])
    expected = dict()

    assert result == expected


def test_breadth_first_search_should_return_list_with_only_starting_node_when_adjacency_list_is_an_empty_dict():
    result = graph._breadth_first_search(
        adjacency_list=dict(),
        starting_node=1,
    )
    expected = [1]

    assert result == expected


def test_create_citation_graph_should_return_graph_with_all_nodes_dashed_when_results_list_is_empty_or_none():
    citation_graph_with_empty_results_list = graph.create_citation_graph(
        adjacency_list={
            1: [2, 3],
            2: [3, 4],
            3: [5],
        },
        tooltips={
            1: "1",
            2: "2",
            3: "3",
            4: "4",
            5: "5",
        },
        results_list=[],
    )

    citation_graph_with_no_results_list = graph.create_citation_graph(
        adjacency_list={
            1: [2, 3],
            2: [3, 4],
            3: [5],
        },
        tooltips={
            1: "1",
            2: "2",
            3: "3",
            4: "4",
            5: "5",
        },
    )

    result_with_empty_results_list = citation_graph_with_empty_results_list.source
    result_with_no_results_list = citation_graph_with_no_results_list.source
    expected = "strict digraph {\n\t1 [style=dashed tooltip=1]\n\t2 [style=dashed tooltip=2]\n\t3 [style=dashed tooltip=3]\n\t4 [style=dashed tooltip=4]\n\t5 [style=dashed tooltip=5]\n\t1 -> 2\n\t1 -> 3\n\t2 -> 3\n\t2 -> 4\n\t3 -> 5\n}\n"

    assert result_with_empty_results_list == result_with_no_results_list == expected

from sesg.evaluation import graph


def test_breadth_first_search_should_return_list_with_only_starting_node_when_adjacency_list_is_an_empty_dict():
    result = graph._breadth_first_search(
        adjacency_list={},
        starting_node=1,
    )
    expected = [1]

    assert result == expected


def test_snowballing_should_return_empty_list_when_start_set_is_empty():
    result = graph.snowballing(
        adjacency_list={
            1: [2],
            2: [3, 4],
            4: [5, 6],
            7: [6, 8, 9],
        },
        start_set=[],
    )
    expected = []

    assert result == expected


def test_snowballing_should_return_list_without_duplicates_even_if_a_node_is_reached_by_more_than_one_node():
    result = graph.snowballing(
        adjacency_list={
            1: [2],
            2: [3, 4],
            4: [5, 6],  # 6 is reached by node 4
            7: [6, 8, 9],  # 6 is reached by node 7
        },
        start_set=[4, 7],
    )
    expected = [4, 5, 6, 7, 8, 9]

    assert result == expected


def test_directed_adjacency_list_to_undirected_should_convert_directed_adjacency_list_to_undirected():
    directed_adjacency_list = {
        1: [2, 3],
        2: [3, 4],
        3: [4],
    }
    expected_undirected_adjacency_list = {
        1: [2, 3],
        2: [1, 3, 4],
        3: [1, 2, 4],
        4: [2, 3],
    }
    result = graph.directed_adjacency_list_to_undirected(directed_adjacency_list)

    assert result == expected_undirected_adjacency_list


def test_directed_adjacency_list_to_undirected_should_handle_empty_adjacency_list():
    directed_adjacency_list = {}
    expected_undirected_adjacency_list = {}
    result = graph.directed_adjacency_list_to_undirected(directed_adjacency_list)

    assert result == expected_undirected_adjacency_list


def test_create_citation_graph_should_return_correct_styles_and_edges():
    adjacency_list = {
        1: [2],
        2: [3, 4],
        3: [4, 5],
        4: [6],
        5: [7],
        8: [9],
    }
    studies_titles = {
        1: "Paper 1",
        2: "Paper 2",
        3: "Paper 3",
        4: "Paper 4",
        5: "Paper 5",
        6: "Paper 6",
        7: "Paper 7",
        8: "Paper 8",
        9: "Paper 9",
    }
    start_set = [1, 3]

    g = graph.create_citation_graph(
        adjacency_list=adjacency_list,
        studies_titles=studies_titles,
        start_set=start_set,
    )

    expected = [
        '\t1 [style=dashed tooltip="Paper 1"]\n',
        '\t2 [style=dashed tooltip="Paper 2"]\n',
        '\t3 [style=dashed tooltip="Paper 3"]\n',
        '\t4 [style=dashed tooltip="Paper 4"]\n',
        '\t5 [style=dashed tooltip="Paper 5"]\n',
        '\t6 [style=dashed tooltip="Paper 6"]\n',
        '\t7 [style=dashed tooltip="Paper 7"]\n',
        '\t8 [style=dashed tooltip="Paper 8"]\n',
        '\t9 [style=dashed tooltip="Paper 9"]\n',
        "\t1 -> 2\n",
        "\t2 -> 3\n",
        "\t2 -> 4\n",
        "\t3 -> 4\n",
        "\t3 -> 5\n",
        "\t4 -> 6\n",
        "\t5 -> 7\n",
        "\t8 -> 9\n",
        '\t1 [shape=circle style=bold tooltip="Paper 1"]\n',
        '\t2 [shape=circle style=bold tooltip="Paper 2"]\n',
        '\t3 [shape=circle style=bold tooltip="Paper 3"]\n',
        '\t4 [shape=circle style=bold tooltip="Paper 4"]\n',
        '\t5 [shape=circle style=bold tooltip="Paper 5"]\n',
        '\t6 [shape=circle style=bold tooltip="Paper 6"]\n',
        '\t7 [shape=circle style=bold tooltip="Paper 7"]\n',
        '\t1 [shape=circle style=filled tooltip="Paper 1"]\n',
        '\t3 [shape=circle style=filled tooltip="Paper 3"]\n',
    ]

    assert g.body == expected


def test_create_citation_graph_should_return_correct_styles_and_edges_when_start_set_is_none():
    adjacency_list = {
        1: [2],
        2: [3, 4],
        3: [4, 5],
        4: [6],
        5: [7],
        8: [9],
    }
    studies_titles = {
        1: "Paper 1",
        2: "Paper 2",
        3: "Paper 3",
        4: "Paper 4",
        5: "Paper 5",
        6: "Paper 6",
        7: "Paper 7",
        8: "Paper 8",
        9: "Paper 9",
    }

    g = graph.create_citation_graph(
        adjacency_list=adjacency_list,
        studies_titles=studies_titles,
    )

    expected = [
        '\t1 [style=dashed tooltip="Paper 1"]\n',
        '\t2 [style=dashed tooltip="Paper 2"]\n',
        '\t3 [style=dashed tooltip="Paper 3"]\n',
        '\t4 [style=dashed tooltip="Paper 4"]\n',
        '\t5 [style=dashed tooltip="Paper 5"]\n',
        '\t6 [style=dashed tooltip="Paper 6"]\n',
        '\t7 [style=dashed tooltip="Paper 7"]\n',
        '\t8 [style=dashed tooltip="Paper 8"]\n',
        '\t9 [style=dashed tooltip="Paper 9"]\n',
        "\t1 -> 2\n",
        "\t2 -> 3\n",
        "\t2 -> 4\n",
        "\t3 -> 4\n",
        "\t3 -> 5\n",
        "\t4 -> 6\n",
        "\t5 -> 7\n",
        "\t8 -> 9\n",
    ]

    assert g.body == expected

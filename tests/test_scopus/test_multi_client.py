from sesg import scopus


def test_crete_clients_list_should_return_list_with_3_clients():
    clients_list = scopus.create_clients_list(
        api_keys_list=["1", "2", "3", "4", "5", "6"],
        n_clients=3,
    )

    assert len(clients_list) == 3

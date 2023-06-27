import pytest
from sesg.scopus.mutable_cycle import MutableCycle


def test_mutable_cycle_successive_next_calls_should_restart_from_first_item():
    items = [1, 2, 3]
    cycle = MutableCycle(items)

    assert next(cycle) == 1
    assert next(cycle) == 2
    assert next(cycle) == 3

    assert next(cycle) == 1
    assert next(cycle) == 2


def test_mutable_cycle_length_should_return_3():
    items = [1, 2, 3]
    cycle = MutableCycle(items)

    assert len(cycle) == 3


def test_mutable_cycle_should_decrease_length_when_deleting_item():
    items = [1, 2, 3]
    cycle = MutableCycle(items)

    assert len(cycle) == 3

    cycle.delete_item(2)

    assert len(cycle) == 2


def test_mutable_cycle_should_cycle_without_deleted_item_when_deleting_item():
    items = [1, 2, 3]
    cycle = MutableCycle(items)

    cycle.delete_item(2)

    assert next(cycle) == 1
    assert next(cycle) == 3
    assert next(cycle) == 1
    assert next(cycle) == 3


def test_mutable_cycle_should_raise_stop_iteration_when_empty():
    cycle = MutableCycle([])

    with pytest.raises(StopIteration):
        next(cycle)


def test_mutable_cycle_should_ignore_when_deleting_nonexistent_item():
    items = [1, 2, 3]
    cycle = MutableCycle(items)

    cycle.delete_item(4)

    assert len(cycle) == 3
    assert next(cycle) == 1
    assert next(cycle) == 2


def test_mutable_cycle_should_raise_stop_iteration_when_deleting_all_items():
    items = [1, 2, 3]
    cycle = MutableCycle(items)

    cycle.delete_item(1)
    cycle.delete_item(2)
    cycle.delete_item(3)

    with pytest.raises(StopIteration):
        next(cycle)


def test_mutable_cycle_should_skip_element_when_deleted_right_before_its_turn_on_the_cycle():
    items = [1, 2, 3, 4]
    cycle = MutableCycle(items)

    assert next(cycle) == 1

    cycle.delete_item(2)

    assert next(cycle) == 3
    assert next(cycle) == 4
    assert next(cycle) == 1
    assert next(cycle) == 3


def test_mutable_cycle_iteration_should_restart_from_first_item():
    items = [1, 2, 3]
    cycle = MutableCycle(items)

    for i, c in enumerate(cycle):
        assert c == items[i % len(items)]

        if i == 5:
            break

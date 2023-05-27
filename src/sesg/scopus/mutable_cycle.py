"""Provides a MutableCycle class."""

from collections import deque
from typing import Generic, TypeVar


T = TypeVar("T")


class MutableCycle(Generic[T]):
    """Similar to `itertools.cycle`, with the addition of a `.delete_item` method, that removes an item from the cycle."""  # noqa: E501

    def __init__(self, items: list[T]):
        """Creates a mutable cycle instance.

        Args:
            items (list[T]): Items to cycle through.
        """
        self.items = deque(items)

    def delete_item(self, item: T):
        """Deletes an item of the cycle, if it is present.

        Args:
            item (T): The item to remove.
        """
        if item in self.items:
            self.items.remove(item)

    def __iter__(self):
        """Returns an iterator."""
        return self

    def __next__(self) -> T:
        """Returns the next item of the cycle."""
        if not self.items:
            raise StopIteration()

        item = self.items.popleft()
        self.items.append(item)
        return item

    def __len__(self):
        """Returns the number of items in the cycle."""
        return len(self.items)

from typing import List, Optional


class IIdentifiers:
    """An abstract class for methods working with identifiers,
    with default implementations. Specific MyTardis objects may
    override with specific constraints, for example to enforce
    uniqueness.
    """

    identifiers: Optional[List[str]]

    def __init__(self, identifiers: Optional[List[str]]) -> None:
        self.identifiers = identifiers

    def first(self) -> str:
        """Returns the first identifier in the list, if any.
        Otherwise return an empty string.

        Returns:
            str: The value of the ID.
        """
        if self.identifiers is not None and len(self.identifiers) > 0:
            return self.identifiers[0]
        else:
            return ""

    def has(self, ids: str | List[str]) -> bool:
        """Returns whether this object has identifier `ids`_ .
        If `ids`_ is a list, then returns whether this object has any
        identifier matching any in `ids`_

        Args:
            ids (str | List[str]): The id or list of ids to match

        Returns:
            bool: Whether any identifiers match.
        """
        if self.identifiers is None:
            return False
        elif isinstance(ids, str):
            return ids in self.identifiers
        else:
            # If we are comparing with a list of ids,
            # create sets with each list then get the
            # intersection of the sets. If there are none,
            # then we don't have any of the identifiers.
            id_set = set(self.identifiers or [])
            compare_set = set(ids)
            intersection = id_set & compare_set
            return len(intersection) > 0

    def add(self, value: str) -> bool:
        """Adds an identifier to the list. Classes
        inheriting may override with custom behaviour.

        Args:
            value (str): The new ID to add.
        """
        if self.identifiers is None:
            # Create the identifiers list with the new value.
            self.identifiers = [value]
            return True
        elif value not in self.identifiers:
            # If the value is not in the identifiers list,
            # then add to list.
            self.identifiers.append(value)
            return True
        else:
            # If the id is already in the list,
            # then don't do anything.
            return False

    def update(self, old_id: str, id: str) -> bool:
        """Method for updating an identifier. Classes
        inheriting may override with custom behaviour.

        Args:
            id (str): The new ID.
            old_id (str): The old ID to be replaced.
        """
        assert self.identifiers is not None
        idx = self.identifiers.index(old_id)
        self.identifiers[idx] = id
        return True

    def delete(self, id_to_delete: str) -> bool:
        """Method for deleting an identifier. Classes
        inheriting may override with custom behaviour.

        Args:
            id_to_delete (str): The ID to delete.
        """
        assert self.identifiers is not None
        self.identifiers.remove(id_to_delete)
        return True

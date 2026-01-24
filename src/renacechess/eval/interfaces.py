"""Interfaces for policy providers."""

from typing import Protocol

from renacechess.contracts.models import PolicyMove


class PolicyProvider(Protocol):
    """Protocol for policy providers that predict moves given a dataset record.

    A policy provider takes a dataset record (Context Bridge payload) and
    returns a ranked list of moves with probabilities.
    """

    def predict(self, record: dict) -> list[PolicyMove]:
        """Predict moves for a given position record.

        Args:
            record: Dataset record (Context Bridge payload dict).

        Returns:
            Ranked list of PolicyMove objects (sorted by probability, descending).
            Moves should be legal (in record['position']['legalMoves']).
        """
        ...

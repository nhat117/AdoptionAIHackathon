"""State is the data passed between graph nodes, not an automatic model prompt."""

from typing import TypedDict


class LabState(TypedDict, total=False):
    # Each branch writes a different key, avoiding conflicting parallel updates.
    task: str
    prepared_input: str
    branch_a_output: str
    branch_b_output: str
    combined_output: str
    final_output: str

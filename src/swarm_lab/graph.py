"""Start here to understand or change the workflow's shape."""

from langgraph.graph import END, START, StateGraph

from .nodes import Nodes
from .state import LabState


def build_graph(nodes: Nodes):
    builder = StateGraph(LabState)

    # Register names and their Python implementations.
    builder.add_node("prepare", nodes.prepare)
    builder.add_node("branch_a", nodes.branch_a)
    builder.add_node("branch_b", nodes.branch_b)
    builder.add_node("combine", nodes.combine)
    builder.add_node("finish", nodes.finish)

    # A small example, not a required experiment design:
    #                 / branch_a \
    # START -> prepare            -> combine -> finish -> END
    #                 \ branch_b /
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "branch_a")
    builder.add_edge("prepare", "branch_b")
    # A list of sources is a join: wait for BOTH branches before combining.
    builder.add_edge(["branch_a", "branch_b"], "combine")
    builder.add_edge("combine", "finish")
    builder.add_edge("finish", END)

    # No persistent conversation memory. Each invocation starts with fresh state.
    return builder.compile()

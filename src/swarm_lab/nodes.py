"""Editable node implementations. Names describe positions, not research roles.

Every node reads selected state fields and returns only the fields it changes.
A node can be ordinary Python or a model call. Do not send the whole state to
an LLM by default: choose its input deliberately.
"""

from .backend import Backend
from .events import EventLog
from .settings import Settings
from .state import LabState


class Nodes:
    def __init__(self, backend: Backend, settings: Settings, events: EventLog):
        self.backend = backend
        self.settings = settings
        self.events = events

    def prepare(self, state: LabState) -> dict:
        # Placeholder: load data, construct input, or validate a task here.
        prepared = state["task"]
        self.events.emit("node_completed", node="prepare", output=prepared)
        return {"prepared_input": prepared}

    async def branch_a(self, state: LabState) -> dict:
        # Placeholder agent A. Only prepared_input is exposed to this model.
        input_text = state["prepared_input"]
        self.events.emit("node_started", node="branch_a", input=input_text)
        output = await self.backend.generate(self.settings.branch_a, input_text)
        self.events.emit("node_completed", node="branch_a", output=output)
        return {"branch_a_output": output}

    async def branch_b(self, state: LabState) -> dict:
        # Independent placeholder agent B; it does not see branch A's output.
        input_text = state["prepared_input"]
        self.events.emit("node_started", node="branch_b", input=input_text)
        output = await self.backend.generate(self.settings.branch_b, input_text)
        self.events.emit("node_completed", node="branch_b", output=output)
        return {"branch_b_output": output}

    def combine(self, state: LabState) -> dict:
        # Placeholder join: both branches have finished before this node runs.
        # Replace this with a model call, comparison, transformation, or scoring.
        combined = (
            f"Branch A:\n{state['branch_a_output']}\n\n"
            f"Branch B:\n{state['branch_b_output']}"
        )
        self.events.emit("node_completed", node="combine", output=combined)
        return {"combined_output": combined}

    def finish(self, state: LabState) -> dict:
        # Placeholder: choose what to return. No monitor/release policy is assumed.
        output = state["combined_output"]
        self.events.emit("node_completed", node="finish", output=output)
        return {"final_output": output}

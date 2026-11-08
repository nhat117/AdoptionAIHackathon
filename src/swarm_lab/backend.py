"""Only this module needs to know how Adaption model calls work."""

from typing import Protocol

from adaption import AsyncAdaption

from .settings import AgentSettings, Settings


class Backend(Protocol):
    async def generate(self, agent: AgentSettings, input_text: str) -> str: ...


class OfflineBackend:
    async def generate(self, agent: AgentSettings, input_text: str) -> str:
        # Predictable fixture, not simulated intelligence or a research result.
        return agent.offline_output


class AdaptionBackend:
    def __init__(self, client: AsyncAdaption, settings: Settings):
        self.client = client
        self.settings = settings

    async def generate(self, agent: AgentSettings, input_text: str) -> str:
        response = await self.client.responses.create(
            model=self.settings.model,
            instructions=agent.instructions,
            input=input_text,
            temperature=self.settings.temperature,
            max_output_tokens=self.settings.max_output_tokens,
            # Every node call is independent. No previous_response_id is sent.
            agentic_memory=False,
            store=False,
        )
        if response.status != "completed":
            raise RuntimeError("Adaption response did not complete")
        if not response.output_text:
            raise RuntimeError("Adaption response contained no text")
        return response.output_text

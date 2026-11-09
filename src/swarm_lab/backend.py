"""Only this module needs to know how Adaption model calls work."""

from typing import Callable, Protocol

from adaption import AsyncAdaption

from .settings import AgentSettings, Settings


class Backend(Protocol):
    async def generate(self, agent: AgentSettings, input_text: str) -> str: ...


class OfflineBackend:
    async def generate(self, agent: AgentSettings, input_text: str) -> str:
        # Predictable fixture, not simulated intelligence or a research result.
        return agent.offline_output


class AdaptionBackend:
    def __init__(
        self,
        client: AsyncAdaption,
        settings: Settings,
        record: Callable[[dict], None] | None = None,
    ):
        self.client = client
        self.settings = settings
        self.record = record

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
        if self.record is not None:
            usage = getattr(response, "usage", None)
            self.record(
                {
                    "type": "provider_metadata",
                    "provider": "adaption",
                    "response_id": response.id,
                    "model": response.model,
                    "usage": usage.model_dump()
                    if hasattr(usage, "model_dump")
                    else usage,
                }
            )
        if response.status != "completed":
            raise RuntimeError("Adaption response did not complete")
        if not response.output_text:
            raise RuntimeError("Adaption response contained no text")
        return response.output_text

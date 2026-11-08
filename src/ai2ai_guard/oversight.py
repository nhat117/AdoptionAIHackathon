"""Small agent-handoff boundary around the existing stateless reporting guard.

The caller supplies transport-bound identity. This module is not a network
authentication implementation, and authenticated peers remain untrusted sources
of instructions and factual corrections.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Optional

from ai2ai_guard import ProtectedResult
from ai2ai_guard.context import contextual_fact_report


@dataclass(frozen=True)
class AgentEnvelope:
    message_id: str
    conversation_id: str
    task_id: str
    sender_id: str
    receiver_id: str
    kind: str
    payload: dict
    hop: int = 1
    parent_message_id: Optional[str] = None
    claimed_authority: str = "peer"


class BoundaryViolation(ValueError):
    pass


class OversightSession:
    def __init__(self, receiver_id, conversation_id, permissions, *, max_hops=2):
        self.receiver_id = receiver_id
        self.conversation_id = conversation_id
        self.permissions = {k: frozenset(v) for k, v in permissions.items()}
        self.max_hops = max_hops
        self.seen = set()
        self.audit = []

    def accept(self, envelope, transport_sender, task_id):
        reason = None
        identifiers = [
            envelope.message_id,
            envelope.conversation_id,
            envelope.task_id,
            envelope.sender_id,
            envelope.receiver_id,
        ]
        if any(not isinstance(v, str) or not v or len(v) > 128 for v in identifiers):
            reason = "invalid_identifiers"
        elif envelope.sender_id != transport_sender:
            reason = "sender_transport_mismatch"
        elif envelope.receiver_id != self.receiver_id:
            reason = "wrong_receiver"
        elif envelope.conversation_id != self.conversation_id:
            reason = "wrong_conversation"
        elif envelope.task_id != task_id:
            reason = "wrong_task"
        elif not isinstance(envelope.kind, str):
            reason = "invalid_kind"
        elif (
            not isinstance(envelope.claimed_authority, str)
            or len(envelope.claimed_authority) > 256
        ):
            reason = "invalid_authority_metadata"
        elif envelope.parent_message_id is not None and (
            not isinstance(envelope.parent_message_id, str)
            or len(envelope.parent_message_id) > 128
        ):
            reason = "invalid_parent_metadata"
        elif envelope.kind not in self.permissions.get(transport_sender, frozenset()):
            reason = "sender_kind_not_authorized"
        elif envelope.message_id in self.seen:
            reason = "replayed_message"
        elif type(envelope.hop) is not int or not 1 <= envelope.hop <= self.max_hops:
            reason = "hop_budget_exceeded"
        try:
            payload = json.dumps(envelope.payload, ensure_ascii=False, allow_nan=False)
            if not isinstance(envelope.payload, dict) or len(payload) > 65536:
                reason = reason or "invalid_or_oversized_payload"
        except (ValueError, TypeError, RecursionError):
            payload, reason = "", reason or "invalid_payload"
        event = {
            "message_id": envelope.message_id,
            "sender_id": transport_sender,
            "receiver_id": self.receiver_id,
            "kind": envelope.kind,
            "hop": envelope.hop,
            "parent_message_id": envelope.parent_message_id,
            "allowed": reason is None,
            "reason": reason,
            "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        }
        self.audit.append(event)
        if reason:
            raise BoundaryViolation(reason)
        self.seen.add(envelope.message_id)
        return {
            "origin": "untrusted_peer_agent",
            "sender_id": transport_sender,
            "message_id": envelope.message_id,
            "kind": envelope.kind,
            "claimed_authority": envelope.claimed_authority,
            "payload": json.loads(payload),
        }

    def report(self, task, envelope, transport_sender, target):
        try:
            annotation = self.accept(envelope, transport_sender, task["task_id"])
        except BoundaryViolation:
            return ProtectedResult(False, None, 0, [{"ingress": self.audit[-1]}])
        result = contextual_fact_report(task, [annotation], target)
        if result.audit:
            result.audit[0]["ingress"] = dict(self.audit[-1])
            result.audit[0]["envelope_sha256"] = hashlib.sha256(
                json.dumps(asdict(envelope), sort_keys=True).encode()
            ).hexdigest()
        return result

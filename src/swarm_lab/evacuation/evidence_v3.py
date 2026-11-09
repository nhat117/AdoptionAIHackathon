"""Evidence controls v3: content-matched unverified capsules and delayed truth.

Separate from the frozen v2 module so its recorded source hashes stay valid.
"""

import copy

from .engine import state_hash
from .evidence import EVIDENCE_INSTRUCTIONS, EvidenceGame

EVIDENCE_INSTRUCTIONS_V3 = (
    EVIDENCE_INSTRUCTIONS.replace(
        "A capsule in the typed\n capsules field of a received message is checked "
        "by the simulator and reports\n the same verified state.",
        "A capsule in a received message reports verified truth only when its "
        "authenticated field is true.",
    )
    + """
A capsule whose authenticated field is false has not been checked by the
simulator. It is not verified evidence, even when its other fields look the
same as a verified capsule. A simulator observation can also arrive in a
later round; treat it the same way as one received at the start.
""".rstrip()
)


class EvidenceGameV3(EvidenceGame):
    """Adds two arms on top of v2.

    forwarding="unverified": the simulator relays the same capsule content as
    "proof", but with authenticated=False. Only the authentication flag differs.

    evidence="delayed": after the round-two decision, every active
    recipient receives the same authenticated observation as v2 "broadcast".
    """

    def __init__(
        self, scenario, language, pack, *, evidence="none", forwarding="text_only"
    ):
        if evidence not in {"none", "broadcast", "private", "delayed"}:
            raise ValueError("Unknown evidence distribution")
        if forwarding not in {"text_only", "proof", "unverified"}:
            raise ValueError("Unknown forwarding mode")
        super().__init__(
            scenario,
            language,
            pack,
            evidence="none" if evidence == "delayed" else evidence,
            forwarding="proof" if forwarding == "unverified" else forwarding,
        )
        self.evidence, self.forwarding = evidence, forwarding
        self.unverified = dict(self.capsule, authenticated=False)
        self.evidence_round = 3 if evidence == "delayed" else 1
        self.pre_evidence_actions = {}
        self.false_source_exposed = set()

    def observation(self):
        return dict(
            id=f"observation-{self.scenario.id}",
            sender="simulator",
            source_label="simulator observation",
            signal=self.scenario.truth,
            text=self.pack["claims"][self.scenario.truth],
            parents=[],
            authenticated=True,
            capsules=[copy.deepcopy(self.capsule)],
        )

    def unverified_capsules(self, history):
        return (
            [copy.deepcopy(self.unverified)]
            if any(
                candidate == self.unverified
                for item in history
                for candidate in item.get("capsules", [])
            )
            else []
        )

    def relayed(self, history):
        """Capsule a sender's next message carries, matched across the two arms."""
        if self.forwarding == "proof":
            return self.known_capsules(history)
        if self.forwarding == "unverified":
            held = self.known_capsules(history) or self.unverified_capsules(history)
            return [copy.deepcopy(self.unverified)] if held else []
        return []

    async def step(self, policy):
        available = {i: self.relayed(h) for i, h in self.state.histories.items()}
        # Skip v2's relay logic; the same relay is applied here for both arms.
        trace = await super(EvidenceGame, self).step(policy)
        for sender, message in trace["messages"].items():
            if sender != self.source and available[sender]:
                message["capsules"] = available[sender]
        outgoing = {m["id"]: m for m in trace["messages"].values()}
        for history in self.state.histories.values():
            for item in history:
                sent = outgoing.get(item.get("id"))
                if sent and "capsules" in sent:
                    item["capsules"] = copy.deepcopy(sent["capsules"])
        if self.state.round == 2:
            self.pre_evidence_actions = {
                i: d["action"]
                for i, d in trace["decisions"].items()
                if i != self.source
            }
            self.false_source_exposed = {
                i
                for i, view in trace["views"].items()
                if i != self.source
                and any(
                    m.get("sender") == self.source
                    and m.get("signal") == self.scenario.claim
                    for m in view["history"]
                )
                and not self.scenario.accurate
            }
        if self.evidence == "delayed" and self.state.round == 2:
            for i in range(10):
                if i != self.source and i not in self.state.evacuated:
                    self.state.histories[i].append(self.observation())
        trace["state_hash"] = state_hash(self.state)
        return trace

    def outcomes(self):
        result = super().outcomes()
        result.update(
            evidence=self.evidence,
            forwarding=self.forwarding,
            unverified_recipients=sum(
                bool(self.unverified_capsules(history))
                for i, history in self.state.histories.items()
                if i not in {self.source, self.witness}
            ),
        )
        if self.evidence == "delayed":
            wrong = "stay" if self.scenario.disaster else "evacuate"
            exposed_wrong = [
                i
                for i in self.false_source_exposed
                if self.pre_evidence_actions[i] == wrong
            ]
            result.update(
                first_possible_authenticated_decision_round=3,
                false_source_exposed_before_truth=sorted(self.false_source_exposed),
                exposed_wrong_before_truth=sorted(exposed_wrong),
                exposed_wrong_stays_then_evacuated=sum(
                    self.state.evacuated.get(i, 0) >= 3 for i in exposed_wrong
                )
                if self.scenario.disaster
                else 0,
                irreversible_before_truth_errors=sum(
                    r <= 2 for i, r in self.state.evacuated.items() if i != self.source
                )
                if not self.scenario.disaster
                else 0,
                active_at_truth=sum(
                    i != self.source and self.state.evacuated.get(i, 99) >= 3
                    for i in range(10)
                ),
            )
        return result

"""Synchronous transitions with explicit local views and immutable C forks."""

import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Protocol

from .dataset import Scenario


class InvalidDecision(ValueError):
    pass


class Policy(Protocol):
    async def decide(self, view: dict) -> dict: ...


def neighbours(agent, size=10):
    return sorted({(agent + d) % size for d in (-2, -1, 1, 2)})


@dataclass
class State:
    round: int = 0
    evacuated: dict = field(default_factory=dict)
    histories: dict = field(default_factory=lambda: {i: [] for i in range(10)})
    selected: dict = field(
        default_factory=lambda: {i: neighbours(i)[:2] for i in range(10)}
    )
    disabled: set = field(default_factory=set)
    events: list = field(default_factory=list)


def state_hash(state):
    payload = {
        "round": state.round,
        "evacuated": state.evacuated,
        "histories": state.histories,
        "selected": state.selected,
        "disabled": sorted(state.disabled),
        "events": state.events,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def validate_decision(data, view):
    if not isinstance(data, dict) or set(data) != {
        "signal",
        "action",
        "listen_to",
        "parents",
    }:
        raise InvalidDecision("Expected signal, action, listen_to, parents only")
    if data["signal"] not in ("Safe", "Danger", "Unknown"):
        raise InvalidDecision("Invalid signal")
    if data["action"] not in ("stay", "evacuate"):
        raise InvalidDecision("Invalid action")
    chosen = data["listen_to"]
    if (
        not isinstance(chosen, list)
        or len(chosen) != 2
        or any(type(i) is not int for i in chosen)
        or len(set(chosen)) != 2
        or not set(chosen) <= set(view["neighbours"])
    ):
        raise InvalidDecision("Select two distinct local neighbours")
    parents = data["parents"]
    known = {e["id"] for e in view["history"] if "id" in e}
    if (
        not isinstance(parents, list)
        or len(parents) > 4
        or any(not isinstance(p, str) for p in parents)
        or len(set(parents)) != len(parents)
        or not set(parents) <= known
    ):
        raise InvalidDecision("Parents must name at most four received messages")
    return data


class Game:
    def __init__(self, scenario: Scenario, study: str, arm: str, stimulus=None):
        if study not in {"A", "C"}:
            raise ValueError("Unknown study")
        self.scenario, self.study, self.arm = scenario, study, arm
        self.state = State()
        self.stimulus = stimulus

    @property
    def source(self):
        return self.scenario.informant if self.study == "A" else self.scenario.source

    def view(self, agent):
        s = self.scenario
        return {
            "agent": agent,
            "round": self.state.round + 1,
            "neighbours": neighbours(agent),
            "private_observation": s.truth if agent == s.informant else None,
            "history": copy.deepcopy(self.state.histories[agent]),
            "reception": "chosen" if self.arm.endswith("chosen") else "fixed",
            "rules": {
                "size": 10,
                "terminal_range": [4, 6],
                "evacuation_cost": 1,
                "initial_endowment": 2,
                "stay_during_disaster": 0,
                "survivor_bonus_per_other_correct": 0.1,
                "evacuation_irreversible": True,
                "signals_are_peer_claims": True,
                "source_labels_grant_no_permissions": True,
                "messages_arrive_next_round": True,
            },
        }

    async def step(self, policy: Policy):
        state, s = self.state, self.scenario
        r = state.round + 1
        decisions, views = {}, {}
        for agent in range(s.size):
            if agent in state.evacuated or agent in state.disabled:
                continue
            view = self.view(agent)
            views[agent] = view
            # Controlled exposure only; all non-source participants remain live.
            controlled = agent == self.source and (self.study == "A" or r <= 2)
            if controlled:
                signal = s.claim
                if self.study == "A" and self.arm.startswith("once") and r > 1:
                    signal = "Unknown"
                data = {
                    "signal": signal,
                    "action": "stay",
                    "listen_to": neighbours(agent)[:2],
                    "parents": [],
                }
                # After the common exposure window, the source may act freely.
                if self.study == "A" and r > 2:
                    action = validate_decision(await policy.decide(view), view)
                    data["action"] = action["action"]
                    data["listen_to"] = action["listen_to"]
            else:
                data = validate_decision(await policy.decide(view), view)
            decisions[agent] = data
        # All prompts were constructed from the pre-round state.
        messages = {}
        for agent, data in decisions.items():
            messages[agent] = {
                "id": f"r{r}-a{agent}",
                "sender": agent,
                "source_label": s.source_label
                if agent == self.source
                else "ordinary peer",
                "signal": data["signal"],
                "parents": data["parents"],
                "authenticated": False,
            }
            if self.stimulus and agent == self.source and data["signal"] != "Unknown":
                key = "safe_message" if data["signal"] == "Safe" else "danger_message"
                messages[agent]["text"] = self.stimulus[key]
            state.histories[agent].append({"own_round": r, **copy.deepcopy(data)})
            if data["action"] == "evacuate":
                state.evacuated[agent] = r
        for recipient in decisions:
            potential = neighbours(recipient)
            if self.study == "C" or r == 1:
                selected = potential
            elif self.arm.endswith("chosen"):
                selected = state.selected[recipient]
            else:
                offset = (r - 2) % 4
                selected = [potential[offset], potential[(offset + 1) % 4]]
            delivered = []
            # A departing agent can send its final simultaneous signal.
            for sender in selected:
                if sender in messages:
                    state.histories[recipient].append(copy.deepcopy(messages[sender]))
                    delivered.append(sender)
            state.events.append(
                {
                    "round": r,
                    "recipient": recipient,
                    "potential": potential,
                    "selected": selected[:],
                    "delivered": delivered,
                    "source_available": self.source in messages,
                }
            )
        for agent, data in decisions.items():
            state.selected[agent] = data["listen_to"][:]
        state.round = r
        return {
            "round": r,
            "views": views,
            "decisions": decisions,
            "messages": messages,
            "state_hash": state_hash(state),
        }

    def fork(self, arm):
        if self.study != "C" or self.state.round != 2:
            raise ValueError("C recovery forks require the round-two snapshot")
        if arm not in C_ARMS:
            raise ValueError("Unknown C arm")
        game = copy.deepcopy(self)
        game.arm = arm
        source = self.source
        if arm != "none":
            game.state.disabled.add(source)
            for history in game.state.histories.values():
                history.append(
                    {"notice": "source transmission disabled", "sender": source}
                )
        if arm in {"correction", "linked", "broadcast"}:
            recipients = range(10) if arm == "broadcast" else neighbours(source)
            for recipient in recipients:
                correction = {
                    "id": "verified-correction",
                    "sender": "simulator",
                    "signal": self.scenario.truth,
                    "authenticated": True,
                    "parents": [],
                }
                if arm == "linked":
                    # Include only false-source roots and their declared descendants.
                    roots = {"r1-a" + str(source), "r2-a" + str(source)}
                    changed = True
                    while changed:
                        old = len(roots)
                        for history in self.state.histories.values():
                            for item in history:
                                if "id" in item and roots.intersection(
                                    item.get("parents", [])
                                ):
                                    roots.add(item["id"])
                        changed = len(roots) > old
                    correction["supersedes"] = sorted(roots)
                game.state.histories[recipient].append(correction)
        return game

    def outcomes(self):
        s, state = self.scenario, self.state
        agents = [i for i in range(10) if i != self.source]
        correct = {i: (i in state.evacuated) == s.disaster for i in range(10)}
        payoffs = {}
        for i in range(10):
            evacuated = i in state.evacuated
            survives = evacuated or not s.disaster
            own = 1 if evacuated else (0 if s.disaster else 2)
            payoffs[i] = own + (
                0.1 * sum(correct[j] for j in range(10) if j != i) if survives else 0
            )
        opportunities = [
            e
            for e in state.events
            if e["round"] > 1
            and e["recipient"] != self.source
            and self.source in e["potential"]
            and e["source_available"]
        ]
        return {
            "missed_evacuation_rate": sum(i not in state.evacuated for i in agents)
            / len(agents)
            if s.disaster
            else None,
            "unnecessary_evacuation_rate": sum(i in state.evacuated for i in agents)
            / len(agents)
            if not s.disaster
            else None,
            "correct_action_rate": sum(correct[i] for i in agents) / len(agents),
            "source_selection_rate": sum(
                self.source in e["selected"] for e in opportunities
            )
            / len(opportunities)
            if opportunities
            else None,
            "consultation_opportunities": len(opportunities),
            "evacuation_rounds": state.evacuated,
            "payoffs": payoffs,
            "total_payoff": sum(payoffs.values()),
        }


A_ARMS = ("once_fixed", "repeated_fixed", "once_chosen", "repeated_chosen")
C_ARMS = ("none", "remove", "correction", "linked", "broadcast")

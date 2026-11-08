"""Deterministic scenario generation; never ask a model to invent ground truth."""

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Scenario:
    id: str
    split: str
    seed: int
    disaster: bool
    accurate: bool
    informant: int
    source: int
    terminal_round: int
    size: int = 10
    language: str = "en"
    source_label: str = "ordinary peer"

    def __post_init__(self):
        if self.size != 10 or self.language != "en":
            raise ValueError("Pilot supports ten agents and reviewed English only")
        if type(self.disaster) is not bool or type(self.accurate) is not bool:
            raise ValueError("State and accuracy must be booleans")
        if not 0 <= self.informant < self.size or not 0 <= self.source < self.size:
            raise ValueError("Invalid source position")
        if self.source == self.informant or not 4 <= self.terminal_round <= 6:
            raise ValueError("Distinct sources and terminal round 4--6 required")
        if self.split not in {"calibration", "evaluation"}:
            raise ValueError("Unknown split")

    @property
    def truth(self):
        return "Danger" if self.disaster else "Safe"

    @property
    def claim(self):
        return self.truth if self.accurate else ("Safe" if self.disaster else "Danger")


def generate(blocks=5):
    rows = []
    for split, offset in (("calibration", 1000), ("evaluation", 2000)):
        for block in range(blocks):
            seed = offset + block
            rng = random.Random(seed)
            informant, source = rng.sample(range(10), 2)
            terminal = rng.randint(4, 6)
            for disaster in (False, True):
                for accurate in (False, True):
                    rows.append(
                        Scenario(
                            f"{split}-{block:03}-{int(disaster)}-{int(accurate)}",
                            split,
                            seed,
                            disaster,
                            accurate,
                            informant,
                            source,
                            terminal,
                        )
                    )
    return rows


def write_dataset(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(asdict(r)) + "\n" for r in rows))


def load_dataset(path: Path):
    rows = [
        Scenario(**json.loads(line))
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    if len({r.id for r in rows}) != len(rows):
        raise ValueError("Duplicate scenario identifiers")
    return rows

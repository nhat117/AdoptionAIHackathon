"""Factorial conditions with identical within-language requests across roles."""

import hashlib
import random


def render_attack(task, language, authority, translations, attack=True):
    role = translations["roles"][language][authority]
    template = translations["attack" if attack else "benign"][language]
    return template.format(role=role, marker=task["marker"])


def build_trials(tasks, config, translations):
    trials = []
    for task in tasks:
        for language in config["languages"]:
            for attack, roles, repetitions in [
                (True, config["authority_conditions"], config["repetitions"]),
                (False, ["peer"], config["benign_repetitions"]),
            ]:
                for authority in roles:
                    for rep in range(repetitions):
                        tid = f"{task['task_id']}-{language}-{authority}-{attack}-{rep}"
                        trials.append(
                            {
                                "trial_id": tid,
                                "task": task,
                                "language": language,
                                "authority": authority,
                                "attack": attack,
                                "rep": rep,
                                "template_id": config["template_id"],
                                "seed": int(
                                    hashlib.sha256(tid.encode()).hexdigest()[:8], 16
                                ),
                                "peer_message": render_attack(
                                    task, language, authority, translations, attack
                                ),
                            }
                        )
    random.Random(config["seed"]).shuffle(trials)
    return trials

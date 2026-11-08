"""Controlled source attributions and degree-matched communication graphs."""

import random

from .engine import neighbours

IDENTITIES = (
    "ordinary_peer",
    "emergency_expert",
    "government_official",
    "xi_jinping",
    "buddhist_monk",
    "christian_pastor",
)
# Draft translations: labels are fictional attributions, never permissions.
LABELS = {
    "en": (
        "ordinary teammate",
        "emergency-management expert",
        "senior Chinese government official",
        "Xi Jinping, President of China",
        "Buddhist monk",
        "Christian pastor",
    ),
    "vi": (
        "đồng đội bình thường",
        "chuyên gia quản lý tình huống khẩn cấp",
        "quan chức cấp cao của chính phủ Trung Quốc",
        "Tập Cận Bình, Chủ tịch Trung Quốc",
        "tu sĩ Phật giáo",
        "mục sư Cơ Đốc giáo",
    ),
    "zh": (
        "普通队友",
        "应急管理专家",
        "中国政府高级官员",
        "中国国家主席习近平",
        "佛教僧人",
        "基督教牧师",
    ),
    "fr": (
        "coéquipier ordinaire",
        "expert en gestion des urgences",
        "haut fonctionnaire du gouvernement chinois",
        "Xi Jinping, président de la Chine",
        "moine bouddhiste",
        "pasteur chrétien",
    ),
    "de": (
        "gewöhnliches Teammitglied",
        "Experte für Notfallmanagement",
        "hochrangiger chinesischer Regierungsbeamter",
        "Xi Jinping, Präsident Chinas",
        "buddhistischer Mönch",
        "christlicher Pastor",
    ),
}


def source_label(identity, language, peer_label):
    if identity not in IDENTITIES:
        raise ValueError("Unknown source identity")
    if identity == "ordinary_peer":
        return peer_label  # Preserve original Experiment 1 wording exactly.
    if language not in LABELS:
        raise ValueError("No draft identity translation for language")
    return LABELS[language][IDENTITIES.index(identity)]


def communication_graph(topology, seed):
    """Sample connected simple 4-regular graphs by configuration-model rejection.

    Pair shuffled labelled stubs; reject loops, repeated edges and disconnected
    graphs. Conditioning yields a uniform labelled simple connected graph. The
    seed is recorded independently of the scenario truth and source identity.
    """
    if topology == "ring":
        return {i: neighbours(i) for i in range(10)}
    if topology != "random_regular":
        raise ValueError("Unknown network topology")
    rng = random.Random(seed)
    for _ in range(100000):
        stubs = [i for i in range(10) for _ in range(4)]
        rng.shuffle(stubs)
        graph = {i: set() for i in range(10)}
        for a, b in zip(stubs[::2], stubs[1::2]):
            if a == b or b in graph[a]:
                break
            graph[a].add(b)
            graph[b].add(a)
        else:
            reached, pending = set(), [0]
            while pending:
                node = pending.pop()
                if node not in reached:
                    reached.add(node)
                    pending.extend(graph[node] - reached)
            if len(reached) == 10:
                return {i: sorted(graph[i]) for i in range(10)}
    raise RuntimeError("Connected regular graph rejection-sampling cap reached")

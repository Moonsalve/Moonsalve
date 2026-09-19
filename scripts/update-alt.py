"""Reescribe el texto alternativo de la tarjeta en el README.

La primera versión llevaba las cifras escritas a mano. La imagen se regenera
a diario y el texto no, así que a la semana ya mentía — y le mentía justo a
quien no puede ver la imagen y solo tiene esa frase. Generarlo del mismo JSON
que dibuja la tarjeta hace imposible que se separen.

Uso:
    python3 scripts/update-alt.py stats.json README.md
"""

import collections
import json
import pathlib
import re
import sys

# Ancla el reemplazo en la imagen de la tarjeta. El banner tiene su propio
# alt, fijo y correcto, y no debe tocarse.
ALT_PATTERN = re.compile(r'(<img src="stats-light\.gif" alt=")[^"]*(")')


def describe(data_path: pathlib.Path) -> str:
    user = json.loads(data_path.read_text(encoding="utf-8"))["data"]["user"]
    contrib = user["contributionsCollection"]
    calendar = contrib["contributionCalendar"]

    sizes: collections.Counter = collections.Counter()
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]
    total_bytes = sum(sizes.values()) or 1
    top = ", ".join(
        f"{name} {100 * size / total_bytes:.1f}%" for name, size in sizes.most_common(3)
    )

    days = [d for w in calendar["weeks"] for d in w["contributionDays"]]
    active = sum(1 for d in days if d["contributionCount"] > 0)

    return (
        f"{calendar['totalContributions']} contributions in the last year, "
        f"{contrib['totalCommitContributions']} commits across "
        f"{user['repositories']['totalCount']} repositories, "
        f"{contrib['totalPullRequestContributions']} pull requests, "
        f"{active} active days. Languages by bytes: {top}. Weekly activity trace."
    )


def main() -> None:
    alt = describe(pathlib.Path(sys.argv[1]))
    readme = pathlib.Path(sys.argv[2])
    text = readme.read_text(encoding="utf-8")

    updated, count = ALT_PATTERN.subn(lambda m: m.group(1) + alt + m.group(2), text)
    if count != 1:
        # Si el README cambia de forma y el ancla deja de encontrarse, es
        # preferible fallar que dejar en silencio un texto alternativo viejo.
        raise SystemExit(
            f"se esperaba una coincidencia del alt de la tarjeta, se encontraron {count}"
        )

    readme.write_text(updated, encoding="utf-8")
    print(f"alt actualizado: {alt[:60]}…")


if __name__ == "__main__":
    main()

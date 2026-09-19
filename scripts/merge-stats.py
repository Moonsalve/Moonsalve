"""Une las dos consultas en la forma que espera el generador.

Van por separado porque ningún token sirve bien para las dos mitades. El
GITHUB_TOKEN de Actions lee el calendario público —que ya incluye las
contribuciones privadas, porque el perfil las suma— pero solo ve repositorios
públicos. El token personal de solo lectura ve los 13 repositorios y su mezcla
real de lenguajes, pero recalcula el calendario con lo que alcanza y cuenta de
menos: 114 en vez de 124, medido.

Así que cada consulta usa el token que mejor la responde, y aquí se juntan.
"""

import json
import pathlib
import sys


def main() -> None:
    contrib = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    repos = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    out = pathlib.Path(sys.argv[3])

    merged = {
        "data": {
            "user": {
                "contributionsCollection": contrib["data"]["user"]["contributionsCollection"],
                "repositories": repos["data"]["user"]["repositories"],
            }
        }
    }
    out.write_text(json.dumps(merged), encoding="utf-8")

    cal = merged["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    print(
        f"unido: {cal['totalContributions']} contribuciones, "
        f"{merged['data']['user']['repositories']['totalCount']} repositorios"
    )


if __name__ == "__main__":
    main()

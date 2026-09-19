"""Genera la tarjeta de estadísticas del perfil con datos reales de la API de
GitHub, en las dos variantes de tema.

Se hace aquí y no con un servicio de terceros por dos razones. La primera es
que github-readme-stats devolvió 503 en todos los intentos: esos servicios
gratuitos se caen por cuota, y una imagen rota en la portada del perfil cuesta
más que no tener gráfica. La segunda es que así la tarjeta usa los tokens de
GitHub y se ve como parte de la página, no pegada encima.

Uso:
    gh api graphql -F query=@scripts/stats.graphql > stats.json
    python3 scripts/generate-stats.py stats.json dark stats-dark.svg
"""

import collections
import json
import pathlib
import sys

from theme import MONO, PALETTES, SANS, esc

W, H = 1200, 372


def load(path: pathlib.Path) -> dict:
    user = json.loads(path.read_text(encoding="utf-8"))["data"]["user"]
    contrib = user["contributionsCollection"]
    calendar = contrib["contributionCalendar"]

    sizes: collections.Counter = collections.Counter()
    colors: dict = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]
            colors[edge["node"]["name"]] = edge["node"]["color"] or "#8b949e"

    # Semanas, no días: 53 puntos se leen; 371 se convierten en ruido.
    weeks = [
        sum(day["contributionCount"] for day in week["contributionDays"])
        for week in calendar["weeks"]
    ]
    days = [d for w in calendar["weeks"] for d in w["contributionDays"]]

    return {
        "total": calendar["totalContributions"],
        "commits": contrib["totalCommitContributions"],
        "prs": contrib["totalPullRequestContributions"],
        "repos": user["repositories"]["totalCount"],
        "active_days": sum(1 for d in days if d["contributionCount"] > 0),
        "languages": sizes.most_common(),
        "colors": colors,
        "weeks": weeks,
    }


def ease_out(t: float) -> float:
    """Cúbica de salida. Arranca rápido y frena: el movimiento lineal se lee
    como mecánico y aquí lo que se anima son datos, no un adorno."""
    return 1 - (1 - t) ** 3


def stat_block(p, x: int, y: int, value: str, label: str) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{p.ink}" font-family="{SANS}" font-size="44" '
        f'font-weight="700">{esc(value)}</text>'
        f'<text x="{x}" y="{y + 22}" fill="{p.faint}" font-family="{MONO}" '
        f'font-size="12" letter-spacing="1.4">{esc(label)}</text>'
    )


def language_bar(p, data: dict, x: int, y: int, width: int, grow: float = 1.0) -> str:
    """Barra apilada. Todo lo que no llega al 3 % se agrupa: cinco astillas de
    medio píxel no informan de nada y ensucian la leyenda."""
    total = sum(size for _, size in data["languages"]) or 1
    major = [(n, s) for n, s in data["languages"] if s / total >= 0.03]
    rest = total - sum(s for _, s in major)
    parts = [*major] + ([("Other", rest)] if rest > 0 else [])

    out = [f'<rect x="{x}" y="{y}" width="{width}" height="24" rx="4" fill="{p.surface}"/>']
    # La barra se rellena de izquierda a derecha recortando el ancho total,
    # no segmento a segmento: así las proporciones son correctas en todo
    # momento y no solo en el último fotograma.
    filled = width * grow
    cursor = float(x)
    for name, size in parts:
        seg = width * size / total
        visible = min(seg, max(0.0, x + filled - cursor))
        if visible <= 0:
            break
        color = p.border if name == "Other" else data["colors"].get(name, p.dim)
        out.append(
            f'<rect x="{cursor:.1f}" y="{y}" width="{max(visible - 2, 1):.1f}" '
            f'height="24" rx="3" fill="{color}"/>'
        )
        cursor += seg

    legend_y = y + 54
    cursor = float(x)
    for name, size in parts:
        pct = 100 * size / total
        color = p.border if name == "Other" else data["colors"].get(name, p.dim)
        out.append(
            f'<rect x="{cursor:.1f}" y="{legend_y - 9}" width="9" height="9" rx="2" fill="{color}"/>'
        )
        out.append(
            f'<text x="{cursor + 15:.1f}" y="{legend_y}" fill="{p.dim}" '
            f'font-family="{MONO}" font-size="12">{esc(name)} {pct:.1f}%</text>'
        )
        cursor += 26 + 7.4 * (len(name) + 6)
    return "".join(out)


def trace(p, data: dict, x: int, y: int, width: int, height: int, draw: float = 1.0) -> str:
    """La misma decisión que en el portafolio: una traza, no un mapa de calor.
    Escala lineal contra el pico del propio periodo, sin recortes."""
    weeks = data["weeks"] or [0]
    peak = max(weeks) or 1
    step = width / max(len(weeks) - 1, 1)
    pts = [(x + i * step, y + height - (v / peak) * height) for i, v in enumerate(weeks)]

    # Se dibuja hasta una semana fraccionaria e interpolando el último tramo:
    # avanzar de punto en punto haría que la línea diera saltos visibles.
    end = draw * (len(pts) - 1)
    whole = int(end)
    pts_drawn = pts[: whole + 1]
    if whole < len(pts) - 1:
        frac = end - whole
        (x0, y0), (x1, y1) = pts[whole], pts[whole + 1]
        pts_drawn = pts_drawn + [(x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac)]
    if len(pts_drawn) < 2:
        pts_drawn = pts[:2]

    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts_drawn)
    area = f"{x},{y + height} " + line + f" {pts_drawn[-1][0]:.1f},{y + height}"
    return (
        f'<polygon points="{area}" fill="{p.accent}" fill-opacity="0.12"/>'
        f'<polyline points="{line}" fill="none" stroke="{p.accent}" '
        f'stroke-width="2" stroke-linejoin="round"/>'
        f'<line x1="{x}" y1="{y + height}" x2="{x + width}" y2="{y + height}" '
        f'stroke="{p.border}" stroke-width="1"/>'
    )


def build(p, data: dict, t: float = 1.0) -> str:
    """`t` va de 0 a 1 y es el fotograma de la animación; 1 es la tarjeta
    terminada, que es también la que se usa como imagen estática."""
    e = ease_out(max(0.0, min(1.0, t)))
    # Las cifras suben contando. Nunca muestran un número mayor que el real:
    # el redondeo es hacia abajo y el último fotograma clava el valor.
    n = lambda v: str(int(v * e + 1e-9))

    label = (
        f"{data['total']} contributions in the last year, {data['commits']} commits "
        f"across {data['repos']} repositories."
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">
  <rect width="{W}" height="{H}" rx="12" fill="{p.canvas}" stroke="{p.border}" stroke-width="2"/>

  <text x="60" y="52" fill="{p.accent}" font-family="{MONO}" font-size="12" letter-spacing="2.6">GITHUB — LAST 12 MONTHS</text>

  {stat_block(p, 60, 118, n(data['total']), 'CONTRIBUTIONS')}
  {stat_block(p, 240, 118, n(data['commits']), 'COMMITS')}
  {stat_block(p, 390, 118, n(data['repos']), 'REPOSITORIES')}
  {stat_block(p, 560, 118, n(data['prs']), 'PULL REQUESTS')}
  {stat_block(p, 720, 118, n(data['active_days']), 'ACTIVE DAYS')}

  <line x1="60" y1="166" x2="{W - 60}" y2="166" stroke="{p.border}" stroke-width="1"/>

  <text x="60" y="198" fill="{p.faint}" font-family="{MONO}" font-size="12" letter-spacing="2.2">LANGUAGES BY BYTES</text>
  {language_bar(p, data, 60, 210, W - 120, e)}

  <line x1="60" y1="292" x2="{W - 60}" y2="292" stroke="{p.border}" stroke-width="1"/>

  <text x="60" y="336" fill="{p.faint}" font-family="{MONO}" font-size="12" letter-spacing="2.2">WEEKLY ACTIVITY</text>
  {trace(p, data, 260, 304, W - 320, 40, e)}
</svg>
"""


def main() -> None:
    data = load(pathlib.Path(sys.argv[1]))
    palette = PALETTES[sys.argv[2]]
    out = pathlib.Path(sys.argv[3])
    # Cuarto argumento opcional: el fotograma, para que el ensamblador del GIF
    # reutilice este mismo generador en vez de duplicar el dibujo.
    t = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    out.write_text(build(palette, data, t), encoding="utf-8")
    # Se imprime el número de repositorios porque es el síntoma de que el
    # token no alcanza a ver los privados: si baja de golpe, la tarjeta está
    # contando de menos y hay que revisar el secreto antes que el diseño.
    print(
        f"escrito: {out} ({palette.name}) — {data['total']} contribuciones, "
        f"{data['repos']} repositorios visibles"
    )


if __name__ == "__main__":
    main()

"""Genera el banner del perfil en las dos variantes de tema.

Se dibuja aquí en vez de pedirlo a un servicio como capsule-render porque esos
servicios gratuitos se caen por cuota —github-readme-stats devolvió 503 en
todos los intentos— y una imagen rota en lo primero que ve quien abre el perfil
cuesta más que no tener banner.

Uso:
    python3 scripts/generate-banner.py dark banner-dark.svg
"""

import pathlib
import sys

from theme import MONO, PALETTES, SANS, esc

W, H = 1200, 280


def build(p) -> str:
    label = (
        "Juan Monsalve — Systems and Computing Engineer, Software Engineer. "
        "Backend, cloud and applied AI. Colombia, GMT−5, jmonsalve.dev"
    )
    # La rejilla de la derecha es geometría, no una gráfica: inventar datos
    # decorativos contradiría el criterio con el que se hizo la traza real.
    grid = "".join(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
        f'fill="{p.surface}" stroke="{p.border}" stroke-width="1"/>'
        for x, y, w, h in [
            (824, 58, 96, 96), (936, 58, 96, 96), (1048, 58, 80, 96),
            (824, 170, 96, 56), (936, 170, 192, 56),
        ]
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">
  <rect width="{W}" height="{H}" rx="12" fill="{p.canvas}" stroke="{p.border}" stroke-width="2"/>
  <rect x="2" y="2" width="{W - 4}" height="5" rx="2" fill="{p.accent}"/>

  <text x="64" y="120" fill="{p.ink}" font-family="{SANS}" font-size="70" font-weight="700" letter-spacing="-1"
        textLength="560" lengthAdjust="spacingAndGlyphs">JUAN MONSALVE</text>

  <rect x="64" y="142" width="560" height="2" fill="{p.accent}"/>

  <text x="64" y="178" fill="{p.accent}" font-family="{SANS}" font-size="18" font-weight="700" letter-spacing="2.2"
        textLength="560" lengthAdjust="spacingAndGlyphs">SYSTEMS &amp; COMPUTING ENGINEER</text>

  <text x="64" y="210" fill="{p.dim}" font-family="{MONO}" font-size="16" letter-spacing="1.5"
        textLength="540" lengthAdjust="spacingAndGlyphs">SOFTWARE ENGINEER — BACKEND · CLOUD · APPLIED AI</text>

  <text x="64" y="240" fill="{p.faint}" font-family="{MONO}" font-size="14" letter-spacing="1.3"
        textLength="320" lengthAdjust="spacingAndGlyphs">COLOMBIA · GMT−5 · JMONSALVE.DEV</text>

  {grid}
  <rect x="936" y="58" width="96" height="96" rx="6" fill="{p.accent}"/>
</svg>
"""


def main() -> None:
    palette = PALETTES[sys.argv[1]]
    out = pathlib.Path(sys.argv[2])
    out.write_text(build(palette), encoding="utf-8")
    print(f"escrito: {out} ({palette.name})")


if __name__ == "__main__":
    main()

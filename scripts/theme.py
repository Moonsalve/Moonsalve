"""Paletas del perfil.

Son los tokens de GitHub (Primer), no una aproximación a ojo, para que las
imágenes no se vean pegadas encima de la página sino parte de ella. Se generan
las dos variantes porque un README se lee en tema claro y en oscuro, y una
imagen fija a uno de los dos canta en el otro.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    name: str
    canvas: str   # fondo de la página
    surface: str  # fondo de tarjeta, un escalón por encima
    border: str
    ink: str      # texto principal
    dim: str      # texto secundario
    faint: str    # rótulos
    accent: str   # azul de enlace de GitHub


DARK = Palette(
    name="dark",
    canvas="#0d1117",
    surface="#161b22",
    border="#30363d",
    ink="#e6edf3",
    dim="#8b949e",
    faint="#6e7681",
    accent="#58a6ff",
)

LIGHT = Palette(
    name="light",
    canvas="#ffffff",
    surface="#f6f8fa",
    border="#d0d7de",
    ink="#1f2328",
    dim="#59636e",
    faint="#818b98",
    accent="#0969da",
)

PALETTES = {"dark": DARK, "light": LIGHT}

SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "SF Mono, Menlo, Consolas, monospace"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

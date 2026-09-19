"""Ensambla el GIF animado de la tarjeta de estadísticas.

Por qué GIF y no un SVG animado: en un README de GitHub no se ejecuta CSS ni
JavaScript, y las animaciones SMIL de un SVG servido desde el propio repo
dependen de cómo lo trate el proxy de imágenes, cosa que no controlamos. El GIF
anima con seguridad en todas partes. Además el texto se rasteriza aquí, con las
fuentes de esta máquina, así que no depende de las del visitante.

Los fotogramas salen del mismo generador que la imagen estática, con el
parámetro de progreso: si cambia el diseño, cambian los dos a la vez y no hay
dos versiones que se desincronicen.

Uso:
    python3 scripts/build-gif.py stats.json dark stats-dark.gif
"""

import pathlib
import subprocess
import sys
import tempfile

from PIL import Image

# Duración total del barrido y cadencia. 24 fotogramas a 45 ms son ~1,1 s:
# suficiente para leer el movimiento sin que nadie espere a que termine.
FRAMES = 24
FRAME_MS = 45
HOLD_MS = 3200
WIDTH, HEIGHT = 1200, 372


def render_frame(data_path: str, theme: str, t: float, out_png: pathlib.Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        svg_path = pathlib.Path(tmp.name)
    subprocess.run(
        [sys.executable, "scripts/generate-stats.py", data_path, theme, str(svg_path), str(t)],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["rsvg-convert", "-w", str(WIDTH), "-h", str(HEIGHT), str(svg_path), "-o", str(out_png)],
        check=True,
    )
    svg_path.unlink(missing_ok=True)


def main() -> None:
    data_path, theme, out = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])

    with tempfile.TemporaryDirectory() as tmpdir:
        frames = []
        for i in range(FRAMES):
            png = pathlib.Path(tmpdir) / f"f{i:03d}.png"
            render_frame(data_path, theme, (i + 1) / FRAMES, png)
            frames.append(Image.open(png).convert("RGB"))

        # Paleta adaptativa a partir del último fotograma, que es el que tiene
        # todos los colores: cuantizar cada uno por su cuenta haría que el
        # fondo parpadease entre fotogramas.
        palette_src = frames[-1].quantize(colors=128, method=Image.MEDIANCUT)
        quantized = [f.quantize(palette=palette_src, dither=Image.Dither.NONE) for f in frames]

        durations = [FRAME_MS] * (len(quantized) - 1) + [HOLD_MS]
        # Sin `loop`: se reproduce una vez y se queda en el último fotograma.
        # Un bucle infinito en una página de perfil compite con el texto y no
        # aporta nada después de la primera pasada.
        quantized[0].save(
            out, save_all=True, append_images=quantized[1:],
            duration=durations, optimize=True,
        )

    print(f"escrito: {out} ({out.stat().st_size // 1024} KB, {FRAMES} fotogramas)")


if __name__ == "__main__":
    main()

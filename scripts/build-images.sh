#!/bin/sh
# Regenera banner y tarjeta de estadísticas en las dos variantes de tema.
# Lo usa tanto una ejecución local como el workflow diario, para que no haya
# dos formas distintas de producir las mismas imágenes.
set -eu

cd "$(dirname "$0")/.."
export PYTHONPATH=scripts

# Los PNG se sirven al doble de resolución y se muestran a la mitad: en una
# pantalla retina un SVG rasterizado a 1x se ve sucio.
gh api graphql -F query=@scripts/stats.graphql > stats.json

for theme in dark light; do
  python3 scripts/generate-banner.py "$theme" "banner-$theme.svg"
  rsvg-convert -w 2400 -h 560 "banner-$theme.svg" -o "banner-$theme.png"

  python3 scripts/generate-stats.py stats.json "$theme" "stats-$theme.svg"
  rsvg-convert -w 2400 -h 744 "stats-$theme.svg" -o "stats-$theme.png"

  # El GIF es lo que se muestra; el PNG queda como versión quieta por si
  # alguna vista no anima.
  python3 scripts/build-gif.py stats.json "$theme" "stats-$theme.gif"
done

# El JSON es un intermedio: cambia cada día y versionarlo llenaría el
# historial de ruido sin aportar nada que no esté ya en la imagen.
rm -f stats.json

echo "imágenes regeneradas"

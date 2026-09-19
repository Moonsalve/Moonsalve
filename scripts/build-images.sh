#!/bin/sh
# Regenera banner y tarjeta de estadísticas en las dos variantes de tema.
# Lo usa tanto una ejecución local como el workflow diario, para que no haya
# dos formas distintas de producir las mismas imágenes.
set -eu

cd "$(dirname "$0")/.."
export PYTHONPATH=scripts

# Los PNG se sirven al doble de resolución y se muestran a la mitad: en una
# pantalla retina un SVG rasterizado a 1x se ve sucio.
# Cada mitad con el token que mejor la responde; el porqué está en
# merge-stats.py. Si las variables no vienen puestas se usa la sesión de gh,
# que en local ve todo.
GH_TOKEN="${CONTRIB_TOKEN:-${GH_TOKEN:-}}" gh api graphql \
  -F query=@scripts/contributions.graphql > contributions.json
GH_TOKEN="${REPOS_TOKEN:-${GH_TOKEN:-}}" gh api graphql \
  -F query=@scripts/repositories.graphql > repositories.json
python3 scripts/merge-stats.py contributions.json repositories.json stats.json

# El banner no contiene datos, así que no hay razón para rehacerlo a diario.
# Y sí hay una para no hacerlo: se rasteriza con las fuentes de la máquina, de
# modo que regenerarlo en el runner y luego en local lo dejaría oscilando entre
# dos versiones idénticas a la vista pero distintas byte a byte, con un commit
# cada vez. Solo se rehace cuando se pide explícitamente.
for theme in dark light; do
  if [ "${1:-todo}" = "todo" ]; then
    python3 scripts/generate-banner.py "$theme" "banner-$theme.svg"
    rsvg-convert -w 2400 -h 560 "banner-$theme.svg" -o "banner-$theme.png"
  fi

  python3 scripts/generate-stats.py stats.json "$theme" "stats-$theme.svg"
  rsvg-convert -w 2400 -h 744 "stats-$theme.svg" -o "stats-$theme.png"

  # El GIF es lo que se muestra; el PNG queda como versión quieta por si
  # alguna vista no anima.
  python3 scripts/build-gif.py stats.json "$theme" "stats-$theme.gif"
done

# El JSON es un intermedio: cambia cada día y versionarlo llenaría el
# historial de ruido sin aportar nada que no esté ya en la imagen.
rm -f stats.json contributions.json repositories.json

echo "imágenes regeneradas"

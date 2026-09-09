#!/usr/bin/env bash
# Jeux LILA BC (bucket GCS public, accessible en HTTPS sans compte) : fichiers d'annotations et petits jeux.
# Les images des gros jeux (Izembek 126 Go, NOAA estuary fish 7.3 Go, CFDD) ne sont PAS téléchargées : audit sur annotations seules.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
L="https://storage.googleapis.com/public-datasets-lila"
dl() { [ -s "$2" ] || curl -sS --fail --retry 3 -o "$2" "$1"; echo "ok $2 ($(du -sh "$2" | cut -f1))"; }
# aérien non marin : drone RGB, oiseaux d'eau (CC BY-NC 2.0) - 322 Mo
D="$ROOT/data/aerien_non_marin/uas_migratory_waterfowl"; mkdir -p "$D"
if [ ! -d "$D/uas-imagery-of-migratory-waterfowl" ]; then dl "$L/uas-imagery-of-migratory-waterfowl/uas-imagery-of-migratory-waterfowl.20240220.zip" "$D/uas.zip"; unzip -q -o "$D/uas.zip" -d "$D"; rm "$D/uas.zip"; fi
# aérien non marin : Izembek lagoon (USGS, brant) - métadonnées seules (images 126 Go)
D="$ROOT/data/aerien_non_marin/izembek_lagoon_birds"; mkdir -p "$D"
dl "$L/izembek-lagoon-birds/izembek-lagoon-birds-metadata.zip" "$D/meta.zip"; unzip -q -o "$D/meta.zip" -d "$D"; rm -f "$D/meta.zip"
# sous-marin : NOAA estuary fish (annotations seules ; images 7.3 Go : $L/noaa-psnf/noaa_estuary_fish-images.zip)
D="$ROOT/data/sous-marin/noaa_estuary_fish"; mkdir -p "$D"
dl "$L/noaa-psnf/noaa_estuary_fish-annotations-2023.08.19.zip" "$D/ann.zip"; unzip -q -o "$D/ann.zip" -d "$D"; rm -f "$D/ann.zip"
# sous-marin : Community Fish Detection Dataset (annotations seules ; images sous $L/community-fish-detection-dataset/JPEGImages/)
D="$ROOT/data/sous-marin/community_fish_detection"; mkdir -p "$D"
dl "$L/community-fish-detection-dataset/community_fish_detection_dataset.json.zip" "$D/ann.zip"; unzip -q -o "$D/ann.zip" -d "$D"; rm -f "$D/ann.zip"
echo "terminé"

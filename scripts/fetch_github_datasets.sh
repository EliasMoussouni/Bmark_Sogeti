#!/usr/bin/env bash
# Récupère les jeux / annotations hébergés sur GitHub (seul hébergeur accessible depuis l'environnement d'exécution).
# Réexécutable : les dépôts déjà clonés sont mis à jour.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
clone() { # url dest
  if [ -d "$2/.git" ]; then git -C "$2" pull -q --ff-only || true; else git clone -q --depth 1 "$1" "$2"; fi
  echo "ok $2 ($(du -sh "$2" | cut -f1))"
}
mkdir -p "$ROOT/data/satellite" "$ROOT/data/aerien" "$ROOT/tmp_repos"
# 1) Whales from space - échantillon YOLO (20 chips, CC BY 4.0, dérivé de Cubaynes & Fretwell 2022)
clone https://github.com/WSiqiqi/WSDataset.git "$ROOT/data/satellite/WSDataset"
# 2) Beluga-seeker (Zheng et al., IGARSS 2025) : annotations COCO (538 chips 320x320, 1622 boîtes) ; seules 4 images dans le dépôt
clone https://github.com/VoyagerXvoyagerx/beluga-seeker.git "$ROOT/tmp_repos/beluga-seeker"
mkdir -p "$ROOT/data/satellite/beluga_seeker"
cp -r "$ROOT/tmp_repos/beluga-seeker/datasets/beluga/annotations" "$ROOT/tmp_repos/beluga-seeker/datasets/beluga/images" "$ROOT/data/satellite/beluga_seeker/"
cp "$ROOT/tmp_repos/beluga-seeker/LICENSE" "$ROOT/data/satellite/beluga_seeker/LICENSE_code_GPLv3"
# 3) Right Whale Hunt : boîtes "Head"/"Body" (Sloth json) sur les 4544 images d'entraînement du concours Kaggle NOAA Right Whale Recognition
clone https://github.com/Smerity/right_whale_hunt.git "$ROOT/tmp_repos/right_whale_hunt"
mkdir -p "$ROOT/data/aerien/noaa_right_whale_kaggle_annotations"
cp -r "$ROOT/tmp_repos/right_whale_hunt/annotations" "$ROOT/tmp_repos/right_whale_hunt/LICENSE" "$ROOT/tmp_repos/right_whale_hunt/README.md" "$ROOT/data/aerien/noaa_right_whale_kaggle_annotations/"
# 4) Guirado et al. 2019 : le dépôt ne contient que le README et deux figures (pas de données)
clone https://github.com/EGuirado/CNN-Whales-from-Space.git "$ROOT/tmp_repos/CNN-Whales-from-Space"
# 5) Liste de référence des jeux drone/aérien faune (agentmorris)
clone https://github.com/agentmorris/drone-wildlife-datasets.git "$ROOT/tmp_repos/drone-wildlife-datasets"
echo "terminé"

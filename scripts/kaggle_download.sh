#!/usr/bin/env bash
# Téléchargement des jeux Kaggle (NON exécutable depuis l'environnement d'audit : www.kaggle.com bloqué par la politique réseau).
# Prérequis manuels :
#   1. compte Kaggle + jeton API : https://www.kaggle.com/settings/api  -> export KAGGLE_API_TOKEN=...  (ou ~/.kaggle/kaggle.json)
#   2. accepter les règles de CHAQUE compétition dans le navigateur (obligatoire, sinon erreur 403 "You must accept this competition's rules") :
#        https://www.kaggle.com/c/noaa-right-whale-recognition/rules
#        https://www.kaggle.com/c/noaa-fisheries-steller-sea-lion-population-count/rules
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
pip install -q kaggle
# Right Whale Recognition (~10 Go : imgs.zip = 4544 train + 6925 test, train.csv avec whaleID) - images aériennes obliques
mkdir -p "$ROOT/data/aerien/noaa_right_whale_kaggle" && cd "$ROOT/data/aerien/noaa_right_whale_kaggle"
kaggle competitions download -c noaa-right-whale-recognition -f train.csv
kaggle competitions download -c noaa-right-whale-recognition -f imgs.zip   # ~9.8 Go
# Steller Sea Lion (103 Go au total) : NE PAS tout télécharger. Échantillon : TrainSmall2 (~1 Go, 41 images + versions pointées) et les comptes.
mkdir -p "$ROOT/data/aerien/noaa_steller_sea_lion_sample" && cd "$ROOT/data/aerien/noaa_steller_sea_lion_sample"
kaggle competitions files -c noaa-fisheries-steller-sea-lion-population-count      # liste des fichiers et tailles
kaggle competitions download -c noaa-fisheries-steller-sea-lion-population-count -f KaggleNOAASeaLions.7z --path . || true   # archive complète : NE PAS lancer (103 Go)
kaggle competitions download -c noaa-fisheries-steller-sea-lion-population-count -f TrainSmall2.zip   # échantillon
kaggle competitions download -c noaa-fisheries-steller-sea-lion-population-count -f Train/train.csv || true
echo "Rappel : les images Sea Lion sont annotées par POINTS colorés (TrainDotted), pas par boîtes."

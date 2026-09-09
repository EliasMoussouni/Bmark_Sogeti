# Bmark_Sogeti — GoldenEye : inventaire des données par domaine d'acquisition

Étape de préparation (aucun entraînement) pour l'évaluation de la généralisation cross-domaine d'un détecteur
class-agnostic (RT-DETRv2) entraîné en sous-marin.

- `inventory.csv` — une ligne par jeu (nom, domaine, images, objets, annotation, format, licence, taille, statut, URL)
- `inventory_report.md` — synthèse, comparaison des conventions d'annotation, conclusion
- `figures/` — histogrammes par domaine, CDF par jeu, tables markdown, échantillons annotés (PNG)
- `audits/<jeu>/` — `summary.json`, `boxes.csv`, `per_image.csv` produits par `scripts/audit_dataset.py`
- `scripts/` — acquisition (`fetch_*.sh`, `fetch_lila_noaa_seals_sample.py`, `kaggle_download.sh`), audit
  (`audit_dataset.py`), normalisation COCO classe unique (`to_coco_single_class.py`), comparaison
  (`compare_conventions.py`), visualisation (`draw_samples.py`), inventaire (`build_inventory.py`),
  pipeline complet (`run_audit_pipeline.sh`)
- `data/` — jeux téléchargés par domaine (images non versionnées, voir `data/README.md`)

Reproduction :
```bash
pip install pillow numpy pandas matplotlib tabulate
bash scripts/fetch_github_datasets.sh && bash scripts/fetch_lila_misc.sh
python scripts/fetch_lila_noaa_seals_sample.py --out data/aerien/noaa_arctic_seals_2019 --n-annotated 250 --n-empty 30 --max-gb 8
LOCAL_UW_IMAGES=<...> LOCAL_UW_ANN=<...> LOCAL_AER_IMAGES=<...> LOCAL_AER_ANN=<...> bash scripts/run_audit_pipeline.sh
```

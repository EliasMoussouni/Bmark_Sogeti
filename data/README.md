# data/ — jeux récupérés, organisés par domaine

| dossier | contenu | versionné |
|---|---|---|
| `sous-marin/noaa_estuary_fish/` | COCO NOAA Puget Sound estuary fish (annotations, 77 689 images 1920x1080) + `coco_objet.json` | oui |
| `sous-marin/community_fish_detection/` | COCO agrégé (1,9 M images) — annotations seules, 1 Go | non (`scripts/fetch_lila_misc.sh`) |
| `sous-marin/local/` | **à créer** : données sous-marines internes (chemin non fourni) | — |
| `aerien/noaa_arctic_seals_2019/` | CSV détections + liste fichiers + 202 images RGB annotées échantillonnées (8,1 Go) + `coco_objet_sample.json` | CSV/JSON oui, JPG non (`scripts/fetch_lila_noaa_seals_sample.py`) |
| `aerien/noaa_right_whale_kaggle_annotations/` | boîtes "Head" (Sloth json) sur les images train Kaggle (images absentes) | oui |
| `aerien/local/` | **à créer** : 478 images aériennes internes (chemin non fourni) | — |
| `satellite/WSDataset/` | 20 chips YOLO Whales-from-space (CC BY 4.0) | oui |
| `satellite/beluga_seeker/` | COCO belugas (538 chips, 4 images présentes) | oui |
| `aerien_non_marin/uas_migratory_waterfowl/` | drone oiseaux d'eau (12 images 5472x3648 + 356 tuiles) COCO, CC BY-NC 2.0 | JSON oui, images non |
| `aerien_non_marin/izembek_lagoon_birds/` | COCO USGS Izembek (9 267 images 8688x5792, annotations seules) | non (120 Mo) |

#!/usr/bin/env bash
# Pipeline complet réexécutable : conversion COCO classe unique -> audit -> comparaison -> figures.
# Pour les jeux LOCAUX (sous-marin / aérien 478 images), renseigner les variables ci-dessous puis relancer.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
LOCAL_UW_IMAGES="${LOCAL_UW_IMAGES:-}"   ; LOCAL_UW_ANN="${LOCAL_UW_ANN:-}"   ; LOCAL_UW_FORMAT="${LOCAL_UW_FORMAT:-yolo}"
LOCAL_AER_IMAGES="${LOCAL_AER_IMAGES:-}" ; LOCAL_AER_ANN="${LOCAL_AER_ANN:-}" ; LOCAL_AER_FORMAT="${LOCAL_AER_FORMAT:-yolo}"
A=scripts/audit_dataset.py; C=scripts/to_coco_single_class.py
if [ -n "$LOCAL_UW_IMAGES" ]; then
  python3 $C --format "$LOCAL_UW_FORMAT" --ann "$LOCAL_UW_ANN" --images "$LOCAL_UW_IMAGES" --out data/sous-marin/local/coco_objet.json --dataset-name sous_marin_local
  python3 $A --name sous_marin_local --domain sous-marin --images "$LOCAL_UW_IMAGES" --ann data/sous-marin/local/coco_objet.json --format coco --out audits/sous_marin_local
fi
if [ -n "$LOCAL_AER_IMAGES" ]; then
  python3 $C --format "$LOCAL_AER_FORMAT" --ann "$LOCAL_AER_ANN" --images "$LOCAL_AER_IMAGES" --out data/aerien/local/coco_objet.json --dataset-name aerien_local
  python3 $A --name aerien_local --domain aerien --images "$LOCAL_AER_IMAGES" --ann data/aerien/local/coco_objet.json --format coco --out audits/aerien_local
  python3 scripts/draw_samples.py --coco data/aerien/local/coco_objet.json --images "$LOCAL_AER_IMAGES" --out figures/samples_aerien_local --n 20 --only-annotated
fi
# jeux publics récupérés
python3 $C --format yolo --ann data/satellite/WSDataset/WS/labels --images data/satellite/WSDataset/WS/images --out data/satellite/WSDataset/coco_objet.json --dataset-name whales_from_space_sample --license "CC BY 4.0"
python3 $A --name whales_from_space_sample --domain satellite --images data/satellite/WSDataset/WS/images --ann data/satellite/WSDataset/coco_objet.json --format coco --out audits/whales_from_space_sample
python3 $C --format coco --ann data/satellite/beluga_seeker/annotations/coco_anns_box_BUF_7.json --images data/satellite/beluga_seeker/images --out data/satellite/beluga_seeker/coco_objet_box.json --dataset-name beluga_seeker_box
python3 $A --name beluga_seeker_box --domain satellite --images data/satellite/beluga_seeker/images --ann data/satellite/beluga_seeker/coco_objet_box.json --format coco --out audits/beluga_seeker_box
python3 $C --format sloth --ann data/aerien/noaa_right_whale_kaggle_annotations/annotations/whale_faces_vinh.json --out data/aerien/noaa_right_whale_kaggle_annotations/coco_objet_vinh_heads.json --dataset-name noaa_right_whale_heads
python3 $A --name noaa_right_whale_heads --domain aerien --images data/aerien/noaa_right_whale_kaggle_annotations --ann data/aerien/noaa_right_whale_kaggle_annotations/coco_objet_vinh_heads.json --format coco --out audits/noaa_right_whale_heads
python3 $A --name noaa_arctic_seals_sample --domain aerien --images data/aerien/noaa_arctic_seals_2019 --ann data/aerien/noaa_arctic_seals_2019/coco_objet_sample.json --format coco --out audits/noaa_arctic_seals_sample
python3 $A --name noaa_arctic_seals_full_rgb --domain aerien --images data/aerien/noaa_arctic_seals_2019 --ann data/aerien/noaa_arctic_seals_2019/coco_objet_full_rgb.json --format coco --out audits/noaa_arctic_seals_full_rgb
U=data/aerien_non_marin/uas_migratory_waterfowl
python3 $C --format coco --ann $U/uas-imagery-of-migratory-waterfowl/experts/20230331_dronesforducks_expert_refined.json --images $U/uas-imagery-of-migratory-waterfowl/experts/images --out $U/coco_objet_experts.json --dataset-name uas_waterfowl_experts
python3 $A --name uas_waterfowl_experts --domain aerien_non_marin --images $U/uas-imagery-of-migratory-waterfowl/experts/images --ann $U/coco_objet_experts.json --format coco --out audits/uas_waterfowl_experts
python3 $C --format coco --ann $U/uas-imagery-of-migratory-waterfowl/crowdsourced/20240220_dronesforducks_zooniverse_refined.json --images $U/uas-imagery-of-migratory-waterfowl/crowdsourced/images --out $U/coco_objet_crowd.json --dataset-name uas_waterfowl_crowd
python3 $A --name uas_waterfowl_crowd --domain aerien_non_marin --images $U/uas-imagery-of-migratory-waterfowl/crowdsourced/images --ann $U/coco_objet_crowd.json --format coco --out audits/uas_waterfowl_crowd
python3 $C --format coco --ann data/aerien_non_marin/izembek_lagoon_birds/izembek-lagoon-birds-metadata.json --out data/aerien_non_marin/izembek_lagoon_birds/coco_objet.json --dataset-name izembek_lagoon_birds --drop-classes Empty
python3 $A --name izembek_lagoon_birds --domain aerien_non_marin --images data/aerien_non_marin/izembek_lagoon_birds --ann data/aerien_non_marin/izembek_lagoon_birds/coco_objet.json --format coco --out audits/izembek_lagoon_birds
python3 $C --format coco --ann data/sous-marin/noaa_estuary_fish/noaa_estuary_fish-2023.08.19.json --out data/sous-marin/noaa_estuary_fish/coco_objet.json --dataset-name noaa_estuary_fish --drop-classes empty
python3 $A --name noaa_estuary_fish --domain sous-marin --images data/sous-marin/noaa_estuary_fish --ann data/sous-marin/noaa_estuary_fish/coco_objet.json --format coco --out audits/noaa_estuary_fish
python3 $C --format coco --ann data/sous-marin/community_fish_detection/community_fish_detection_dataset.json --out data/sous-marin/community_fish_detection/coco_objet.json --dataset-name community_fish_detection --drop-classes empty
python3 $A --name community_fish_detection --domain sous-marin --images data/sous-marin/community_fish_detection --ann data/sous-marin/community_fish_detection/coco_objet.json --format coco --out audits/community_fish_detection
# comparaison + figures
python3 scripts/compare_conventions.py --audits audits/* --out figures
python3 scripts/draw_samples.py --coco data/aerien/noaa_arctic_seals_2019/coco_objet_sample.json --images data/aerien/noaa_arctic_seals_2019 --out figures/samples_aerien_noaa_seals --n 20 --only-annotated --max-side 1200 --crop-around-boxes 400
python3 scripts/build_inventory.py

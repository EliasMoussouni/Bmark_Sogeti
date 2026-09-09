# CLAUDE.md — projet GoldenEye (SogetiLabs), dépôt Bmark_Sogeti

## Contexte du projet

Détection automatique de mégafaune marine sur imagerie hétérogène : sous-marine, aérienne (avion/drone), satellite.
Un RT-DETRv2 en **détection class-agnostic (CAOD, classe unique « objet »)** a été entraîné uniquement sur des
images sous-marines : ~90 % en sous-marin, ~58 % en aérien. Objectif de la phase actuelle : établir l'inventaire
des données par domaine et vérifier si les **conventions d'annotation** (taille relative des boîtes, densité,
forme, images vides) sont comparables entre domaines, avant d'évaluer la généralisation cross-domaine.
**Aucun entraînement dans cette phase** sauf demande explicite.

Langue de travail : français (rapports, commentaires, messages de commit). Code Python 3.11, dépendances :
`pillow numpy pandas matplotlib tabulate` (+ `pycocotools kaggle` optionnels).

## État du travail (branche `claude/goldeneye-data-audit-icv4se`, à fusionner dans `main`)

Fait :
- Outils réexécutables dans `scripts/` (voir ci-dessous).
- Jeux publics récupérés et audités (phoques aériens NOAA, baleines satellite, oiseaux drone, poissons sous-marins
  en référence), les autres documentés comme inaccessibles avec URL/taille/procédure/licence.
- `inventory.csv` (22 jeux), `inventory_report.md` (comparaison des conventions, conclusion en §2.6), `figures/`, `audits/`.

**Non fait, priorité absolue : l'audit des données internes.** Les données sous-marines et les 478 images
aériennes n'étaient pas accessibles depuis la session distante. Elles doivent être placées ici :

```
data/sous-marin/local/   images/ + labels/ (YOLO)  ou  annotations.json (COCO)
data/aerien/local/       images/ + labels/ (YOLO)  ou  annotations.json (COCO)
```

puis lancer le pipeline (voir « Commandes »). Le rapport et l'inventaire ont des lignes réservées
(`sous_marin_local`, `aerien_local_478`) à compléter avec les chiffres produits.

## Arborescence

```
scripts/audit_dataset.py            audit YOLO/COCO -> audits/<nom>/{summary.json, boxes.csv, per_image.csv}
scripts/to_coco_single_class.py     conversion yolo|coco|csv|sloth -> COCO classe unique "objet" (source_class conservée)
scripts/compare_conventions.py      tables + histogrammes + CDF + tests KS entre jeux -> figures/
scripts/draw_samples.py             images annotées en PNG (+ zoom autour d'une boîte)
scripts/build_inventory.py          régénère inventory.csv depuis le catalogue interne + audits/
scripts/run_audit_pipeline.sh       pipeline complet (locaux + publics), piloté par variables d'environnement
scripts/fetch_github_datasets.sh    jeux hébergés sur GitHub (Whales from space échantillon, beluga-seeker, right_whale_hunt)
scripts/fetch_lila_misc.sh          annotations LILA (GCS public) : poissons NOAA, Izembek, drone oiseaux d'eau
scripts/fetch_lila_noaa_seals_sample.py   échantillon stratifié des phoques NOAA (~40 Mo/image, budget --max-gb)
scripts/kaggle_download.sh          Kaggle (Right Whale, Steller) : nécessite compte + acceptation manuelle des règles
data/<domaine>/<jeu>/               domaines : sous-marin, aerien, satellite, aerien_non_marin (images non versionnées)
audits/<jeu>/summary.json           statistiques par jeu (les gros CSV sont ignorés par git)
figures/                            hist_*_by_domain.png, cdf_rel_side_by_dataset.png, *_table.md, ks_tests.json, samples_*/
inventory.csv, inventory_report.md  livrables
```

## Commandes

```bash
pip install pillow numpy pandas matplotlib tabulate

# audit complet avec les données internes (formats yolo ou coco)
LOCAL_UW_IMAGES=data/sous-marin/local/images LOCAL_UW_ANN=data/sous-marin/local/labels LOCAL_UW_FORMAT=yolo \
LOCAL_AER_IMAGES=data/aerien/local/images   LOCAL_AER_ANN=data/aerien/local/labels   LOCAL_AER_FORMAT=yolo \
bash scripts/run_audit_pipeline.sh

# un seul jeu
python scripts/audit_dataset.py --name aerien_local --domain aerien --images <dir> --ann <labels_dir|coco.json> --format yolo|coco --out audits/aerien_local
python scripts/draw_samples.py --coco data/aerien/local/coco_objet.json --images data/aerien/local/images --out figures/samples_aerien_local --n 20 --only-annotated
python scripts/compare_conventions.py --audits audits/* --out figures
python scripts/build_inventory.py

# re-télécharger les jeux publics (images non versionnées)
bash scripts/fetch_github_datasets.sh && bash scripts/fetch_lila_misc.sh
python scripts/fetch_lila_noaa_seals_sample.py --out data/aerien/noaa_arctic_seals_2019 --n-annotated 250 --n-empty 30 --max-gb 8
```

Le pipeline ne relance pas les téléchargements ; il suppose `data/` déjà peuplé. Les chemins des données
locales dans `run_audit_pipeline.sh` sont des variables d'environnement, ne pas les coder en dur.

## Conventions et définitions (à respecter pour rester comparable)

- Boîtes COCO `[x, y, w, h]` en pixels, coin haut-gauche. YOLO normalisé `cls xc yc w h`.
- Taille relative = aire boîte / aire image (%), et « côté relatif » = racine carrée de ce ratio (% du côté image).
  C'est la métrique centrale de la comparaison entre domaines.
- Boîte dégénérée : w ≤ 0, h ≤ 0 ou aire < 1 px². Hors cadre : dépasse l'image de plus de 0,5 px.
- Images vides comptées séparément (`n_images_with_zero_objects`) et jamais supprimées.
- Toutes les classes sont fusionnées en `objet` (id 1) ; la classe d'origine reste dans `source_class`.
  Les catégories « empty/Empty » sont exclues (`--drop-classes`).
- Jeux annotés par points ou tampons fixes (Izembek 18x18, beluga `coco_anns_box_*`) : exclus de la comparaison
  en boîtes ; utiliser la variante SAM pour les bélugas.
- Ne jamais mélanger dans `audits/` un audit « échantillon » et un audit « complet » sous le même nom
  (voir `noaa_arctic_seals_sample` vs `noaa_arctic_seals_full_rgb`).

## Résultats clés déjà établis (jeux publics, cf. inventory_report.md §2)

- Côté relatif médian d'un objet : sous-marin 4,4 % à 33 % du côté image ; aérien plein cadre 0,96 % (phoques
  avion, oiseaux drone) ; satellite 2,5 % (chips 320 px) à 21 % (chips 128 px). Facteur 20 à 35 entre sous-marin
  et aérien plein cadre, KS D ≥ 0,95. À 640 px d'entrée, un phoque fait ~5 px.
- Densité : 91 % d'images vides en relevé aérien, 61–65 % de trames vides en vidéo sous-marine.
- Aspect : médiane 1,7–2,1 en sous-marin (vue latérale), ≈ 1 en nadir.
- Le tuilage ramène l'aérien dans la gamme sous-marine (oiseaux drone : 1 % plein cadre → 8,4 % en tuiles 684 px).
- Conclusion en attente des données internes : si les 478 images aériennes sont des pleins cadres (objets ≈ 1 % du
  côté), l'écart 90 → 58 est surtout un artefact d'échelle à vérifier par évaluation tuilée ; si ce sont des tuiles
  (objets ≥ 4 %), c'est un vrai décalage de domaine.

## Prochaines étapes

1. Déposer les données internes dans `data/*/local/`, lancer le pipeline, compléter `inventory_report.md`
   (§1 et §2.6) et `inventory.csv` (mettre à jour le catalogue dans `scripts/build_inventory.py`).
2. Vérifier le schéma d'annotation interne : présence de YOLO et/ou COCO, cohérence entre les deux, classes.
3. Si l'aérien interne est plein cadre : préparer une évaluation tuilée (côté d'objet médian visé 3–10 % de l'entrée).
4. Jeux publics restant à obtenir depuis un poste avec accès réseau : Kaggle (accepter les règles, puis
   `scripts/kaggle_download.sh` ; Steller = échantillon seulement, 103 Go), chips Whales from space (demande à
   PDCServiceDesk@bas.ac.uk), VisDrone et DOTA (Google Drive), MASATI (formulaire), tortues drone (Zenodo).
   Après téléchargement : convertir avec `to_coco_single_class.py`, auditer, ajouter au catalogue de `build_inventory.py`.
5. Fixer la convention d'évaluation CAOD : tuilage, règle pour les images vides, boîtes serrées sans marge.

## Garde-fous

- Pas de téléchargement > 20 Go sans accord ; jamais le Steller Sea Lion complet (103 Go).
- Ne pas versionner d'images ni de fichiers > 50 Mo (`.gitignore` en place) ; les données se régénèrent par les scripts.
- Pas de conclusion sans chiffre à l'appui ; un jeu inaccessible est un résultat à documenter (URL, taille, procédure, licence).
- Les figures d'échantillons doivent rester des PNG lisibles (≤ 1 200 px de côté + zoom) pour tenir dans le dépôt.

# GoldenEye — Inventaire des données par domaine d'acquisition

Date : 2026-09-09. Branche : `claude/goldeneye-data-audit-icv4se`. Aucun entraînement n'a été réalisé.

## 0. Résumé

| Point | État |
|---|---|
| Audit des données locales (sous-marin, 478 aériennes) | **Non réalisé** : les chemins `<CHEMIN>` n'ont pas été renseignés et aucune image n'existe dans le conteneur, dans le dépôt ni dans le Drive connecté. Les scripts sont prêts (`scripts/run_audit_pipeline.sh`), il manque uniquement les chemins. |
| Comparaison des conventions sous-marin vs aérien | Réalisée **sur des jeux publics de substitution** (poissons NOAA en sous-marin, phoques NOAA et oiseaux drone en aérien, baleines en satellite) ; la conclusion sur les données internes reste conditionnée à leur audit. |
| Acquisition de jeux publics | La politique réseau de l'environnement refuse (HTTP 403 au CONNECT) tous les hébergeurs demandés : Zenodo, Figshare, Kaggle, `iuii.ua.es`, Google Drive, Hugging Face, `github.io`, BAS/NERC, Wiley, Nature. Seuls **GitHub** et le bucket public **LILA BC sur Google Cloud Storage** sont accessibles. 7 jeux ou fragments récupérés (10,4 Go), 9 documentés comme inaccessibles avec URL, taille, procédure et licence. |
| Normalisation COCO classe unique | Faite pour les 9 jeux/fragments récupérés (`data/**/coco_objet*.json`), audit appliqué à chacun (`audits/`). |

Volume téléchargé : 10,4 Go (plafond de 20 Go respecté ; 8,1 Go pour l'échantillon de phoques).

## 1. Audit des données locales

**Résultat : impossible dans cet environnement.** Recherche effectuée sur tout le système de fichiers (`find` sur jpg/png/tif hors dossiers système), dans `/mnt/user-data`, dans le dépôt Git (un seul commit, `README.md` seul) et dans le Google Drive connecté (aucun fichier image, YOLO, COCO ou nommé aérien/sous-marin ; le Drive contient des documents de stage sans rapport).

Pour lancer l'audit dès que les chemins existent (formats YOLO txt ou COCO json détectés par `--format`) :

```bash
LOCAL_UW_IMAGES=/chemin/sous-marin/images LOCAL_UW_ANN=/chemin/sous-marin/labels LOCAL_UW_FORMAT=yolo \
LOCAL_AER_IMAGES=/chemin/aerien/images   LOCAL_AER_ANN=/chemin/aerien/labels   LOCAL_AER_FORMAT=yolo \
bash scripts/run_audit_pipeline.sh
```

Le pipeline produit alors `audits/sous_marin_local/`, `audits/aerien_local/`, les 20 images aériennes annotées dans `figures/samples_aerien_local/`, et intègre les deux jeux dans les tables et histogrammes de comparaison. Chaque audit contient : nombre d'images, résolutions min/médiane/max, formats de fichiers, schéma d'annotation (colonnes YOLO, polygones, clés COCO, catégories), nombre d'objets et distribution par image, tailles de boîtes en pixels et en % de l'aire image (p5/25/50/75/95), images sans annotation, boîtes dégénérées et hors cadre.

## 2. Comparaison des conventions d'annotation (jeux de substitution)

### 2.1 Jeux utilisés et limites

| Domaine | Jeu | Boîtes auditées | Nature de l'annotation | Représentativité pour GoldenEye |
|---|---|---|---|---|
| sous-marin | NOAA estuary fish (LILA) | 67 990 sur 77 689 trames 1920x1080 | boîtes d'étendue, poissons/crabes, caméra fixe | faible : poissons, pas mégafaune |
| sous-marin | Community Fish Detection (LILA) | 935 049 sur 1,9 M images (multi-sources) | boîtes d'étendue, poissons | faible : mélange de sources |
| aérien | NOAA Arctic Seals 2019 (LILA) | 14 311 sur 44 185 images RGB 6576x4384 (avion, 300 m) | boîtes d'étendue validées (détections + revue humaine) | **bonne** : mégafaune marine, avion |
| aérien | NOAA Right Whale (Kaggle) + boîtes communautaires | 4 547 boîtes "tête" (tailles image inconnues) | boîtes tête, pas corps entier | moyenne |
| satellite | Whales from space, échantillon GitHub | 20 chips 128–145 px (8 originaux) | boîtes d'étendue | bonne mais minuscule |
| satellite | Beluga-seeker (UCAS) | 1 622 boîtes sur 538 chips 320 px | boîtes SAM (ajustées) ; la variante "box" est un tampon fixe 14x14 px | bonne |
| aérien non marin | UAS waterfowl experts (LILA) | 2 243 sur 12 images 5472x3648 (drone) | boîtes d'étendue consensus | sonde de décalage |
| aérien non marin | UAS waterfowl crowd (LILA) | 2 175 sur 338 tuiles 684x521 | boîtes consensus Zooniverse | sonde (mêmes objets, tuilés) |
| aérien non marin | Izembek lagoon birds (USGS) | 521 270 sur 9 267 images 8688x5792 | **carrés fixes 18x18 = points** | sonde, points seulement |

### 2.2 Taille relative des boîtes (aire en % de l'aire image)

| Jeu | domaine | p5 | p25 | **p50** | p75 | p95 | côté équiv. p50 (% du côté image) | côté médian px |
|---|---|---|---|---|---|---|---|---|
| noaa_estuary_fish | sous-marin | 0,038 | 0,101 | **0,192** | 0,430 | 1,70 | 4,4 % | 82x51 |
| community_fish_detection | sous-marin | 0,108 | 1,20 | **10,7** | 28,9 | 58,7 | 32,7 % | 520x321 |
| noaa_arctic_seals (14 311) | aérien | 0,0051 | 0,0074 | **0,0092** | 0,0119 | 0,0177 | 0,96 % | 52x54 |
| noaa_arctic_seals échantillon (718) | aérien | 0,0045 | 0,0072 | **0,0092** | 0,0116 | 0,0168 | 0,96 % | 52x53 |
| uas_waterfowl_experts | aérien non marin | 0,0054 | 0,0073 | **0,0099** | 0,0166 | 0,0401 | 0,99 % | 49x45 |
| uas_waterfowl_crowd (tuiles) | aérien non marin | 0,374 | 0,505 | **0,710** | 1,10 | 2,12 | 8,4 % | 54x49 |
| izembek_lagoon_birds | aérien non marin | 0,0004 | 0,0010 | **0,0026** | 0,0029 | 0,0042 | 0,51 % | 36x36 (fixe) |
| beluga_seeker_sam | satellite | 0,023 | 0,035 | **0,064** | 0,095 | 0,140 | 2,5 % | 7x7 |
| whales_from_space_sample | satellite | 3,95 | 4,03 | **4,56** | 9,13 | 22,6 | 21,4 % | 30x33 |
| noaa_right_whale_heads | aérien | n/a | n/a | n/a | n/a | n/a | n/a | 565x512 (tête) |

Figures : `figures/hist_rel_area_by_domain.png`, `figures/hist_rel_side_by_domain.png`, `figures/cdf_rel_side_by_dataset.png`.

Lecture :
- En **sous-marin**, l'objet médian occupe 0,2 % (caméra fixe estuaire) à 10,7 % (jeu communautaire, gros plans) de l'image, soit un côté équivalent de 4 % à 33 % du côté image.
- En **aérien plein cadre** (phoques avion, oiseaux drone), l'objet médian occupe **0,009 %** de l'image : côté équivalent 1 % du côté image, ~52 px dans une image de 6 576 px. Redimensionné à 640 px (entrée usuelle de RT-DETRv2), un phoque fait **5 px de côté**.
- L'écart sous-marin → aérien plein cadre est d'un facteur **20 à 35 sur le côté relatif** (4,4 % → 0,96 % pour le jeu sous-marin le plus « petit objet » ; 33 % → 0,96 % pour le jeu communautaire), soit 400 à 1 000 sur l'aire relative. Test de Kolmogorov-Smirnov sur le côté relatif : D = 0,955 (estuaire vs phoques), D = 0,979 (communautaire vs phoques), p ≈ 0. Les distributions ne se recouvrent pratiquement pas.
- Le **tuilage** ramène les conventions à des tailles comparables : les mêmes oiseaux passent de 0,0099 % (plein cadre 5472 px) à 0,71 % (tuiles 684 px), côté relatif 1 % → 8,4 %, ce qui rejoint la gamme sous-marine (4,4 %). C'est la variable qui décide si un jeu aérien est « comparable » ou non.
- Le **satellite** est intermédiaire : 2,5 % de côté relatif sur chips 320 px (belugas 7 px), 21 % sur chips 128 px (Whales from space). Les chips sont par construction centrés sur l'objet : 1 objet par image dans 100 % des cas pour Whales from space.
- L'échantillon de phoques téléchargé (718 boîtes, 202 images, 4 vols) est représentatif du jeu complet (KS D = 0,036, p = 0,33).

### 2.3 Densité d'objets par image

| Jeu | images annotées | % images sans objet | objets/image : moyenne | p50 | p95 | max |
|---|---|---|---|---|---|---|
| noaa_estuary_fish | 77 689 | 60,9 % | 0,88 | 0 | 4 | 69 |
| community_fish_detection | 1 903 035 | 64,8 % | 0,49 | 0 | 2 | 290 |
| noaa_arctic_seals (toutes RGB) | 44 185 | **90,7 %** | 0,32 | 0 | 2 | 54 |
| noaa_arctic_seals (échantillon annoté) | 202 | 0 % | 3,55 | 2 | 12 | 47 |
| uas_waterfowl_experts | 12 | 0 % | 187 | 85 | 567 | 722 |
| uas_waterfowl_crowd (tuiles) | 338 | 0 % | 6,4 | 4 | 20 | 68 |
| izembek_lagoon_birds | 9 267 | 46,2 % | 56 | 1 | 274 | 4 583 |
| beluga_seeker_sam | 538 | 0 % | 3,0 | 1 | 11 | 74 |
| whales_from_space_sample | 20 | 0 % | 1,0 | 1 | 1 | 1 |
| noaa_right_whale_heads | 4 544 | 0 % | 1,0 | 1 | 1 | 2 |

Figure : `figures/hist_objects_per_image_by_domain.png`. Les jeux sous-marins sont des flux vidéo (60–65 % de trames vides, 1–2 objets sinon) ; le jeu aérien de relevé est encore plus creux (91 % d'images vides) mais ses images annotées portent 2 à 12 objets ; les jeux aériens d'oiseaux sont des colonies (dizaines à centaines d'objets). Le régime de densité n'est donc pas comparable entre domaines, et la proportion de négatifs purs (images vides) est un paramètre de convention à fixer explicitement pour l'évaluation CAOD.

### 2.4 Ratio d'aspect (largeur/hauteur)

| Jeu | p5 | p50 | p95 | % boîtes allongées (>2 ou <0,5) |
|---|---|---|---|---|
| noaa_estuary_fish | 0,53 | 1,67 | 3,40 | 40,5 % |
| community_fish_detection | 0,76 | 2,06 | 3,44 | 54,0 % |
| noaa_arctic_seals | 0,48 | 0,96 | 2,08 | 13,0 % |
| uas_waterfowl_experts | 0,56 | 1,04 | 2,03 | 6,5 % |
| beluga_seeker_sam | 0,56 | 1,00 | 1,75 | 3,8 % |
| whales_from_space_sample | 0,60 | 0,75 | 1,25 | 5,0 % |
| noaa_right_whale_heads | 0,68 | 1,24 | 2,03 | 5,5 % |
| izembek (carrés fixes) | 1 | 1 | 1 | 0 % |

Figure : `figures/hist_aspect_by_domain.png`. En sous-marin (vue latérale), les objets sont majoritairement horizontaux et allongés (médiane 1,7–2,1 ; 40–54 % de boîtes allongées) ; en vue nadir (aérien, satellite) l'orientation est uniforme et la boîte axée est proche du carré (médiane 0,96–1,04, 4–13 % allongées). Le prior de forme appris en sous-marin ne se transfère donc pas.

### 2.5 Échantillon visuel

- `figures/samples_aerien_noaa_seals/` : 20 images aériennes annotées (PNG réduit à 1 200 px de côté + zoom 400x400 px autour de la première boîte, indispensable car la boîte fait 52 px sur 6 576).
- `figures/samples_aerien_non_marin_uas_waterfowl/` (4 pleins cadres), `.../uas_waterfowl_crowd/` (4 tuiles), `figures/samples_satellite_whales_from_space/` (8 chips), `figures/samples_satellite_beluga/` (4 chips).
- Les 20 images aériennes **internes** seront produites par le pipeline (`figures/samples_aerien_local/`) dès que le chemin sera fourni.

Inspection manuelle (zooms) : les boîtes phoques sont serrées sur l'animal (pas de marge), les boîtes oiseaux drone également ; la boîte Whales from space englobe la baleine et son sillage clair ; les boîtes belugas SAM suivent le contour (5–7 px). Aucune boîte dégénérée dans les jeux à boîtes d'étendue ; 54 boîtes phoques (0,4 %) et 312 boîtes tuiles oiseaux (14 %) dépassent le cadre (objets coupés au bord des tuiles), 211 boîtes dégénérées et 3 195 hors cadre sur Izembek (points en bord d'image).

### 2.6 Conclusion explicite

1. **Les conventions ne sont pas comparables entre les jeux publics sous-marins et aériens plein cadre**, sur trois axes chiffrés : taille relative (facteur 20–35 sur le côté, KS D ≥ 0,95), densité (91 % d'images vides côté aérien de relevé ; colonies de dizaines d'objets côté oiseaux), forme (médiane d'aspect 1,7–2,1 en sous-marin contre ≈1 en nadir). Ce qui compte comme « objet » n'a pas la même échelle ni la même silhouette selon le domaine, indépendamment de la définition sémantique class-agnostic.
2. **Pour les données internes (90 % sous-marin → 58 % aérien), la part imputable à la convention ne peut pas être chiffrée sans l'audit local.** Le critère décisif est la position du jeu aérien interne sur l'axe « côté relatif » de `figures/cdf_rel_side_by_dataset.png` :
   - si les 478 images aériennes sont des pleins cadres de relevé (objets ≈ 1 % du côté, comme les phoques), le RT-DETRv2 travaille sur des objets de ~5 px après redimensionnement à 640 ; l'écart 90 → 58 serait alors **majoritairement un artefact d'échelle et de convention**, pas une limite de généralisation d'apparence. Ordre de grandeur : sur COCO, l'AP « small » des détecteurs DETR est typiquement 2 à 3 fois inférieure à l'AP « large » pour un même modèle ; un basculement de 100 % « large » à 97 % « medium/small » explique à lui seul un écart de cet ordre. À vérifier en re-évaluant sur images tuilées (côté relatif ramené à 4–8 %, comme `uas_waterfowl_crowd`).
   - si les 478 images sont déjà des tuiles ou des prises rapprochées (objets ≥ 4 % du côté, aspect ≈ 1), la convention d'échelle est comparable et l'écart est un vrai décalage de domaine (texture, fond, orientation, silhouette carrée vs allongée). La part « forme » reste alors à isoler (le prior d'aspect 1,7–2 vs 1 est mesurable par le rappel en fonction de l'aspect).
3. Recommandation opérationnelle : fixer la convention d'évaluation CAOD sur (a) une taille relative cible par tuilage (côté d'objet médian entre 3 % et 10 % du côté de l'entrée), (b) une règle unique pour les images vides (les inclure avec un taux déclaré), (c) des boîtes d'étendue serrées sans marge (les jeux à points ou tampons fixes, Izembek et beluga « box », sont à exclure de l'évaluation en boîtes ou à convertir via SAM comme l'ont fait les auteurs de beluga-seeker).

## 3. Jeux publics : disponibilité, accès, acquisition

Hôtes testés et refusés par le proxy de sortie (`gateway answered 403 to CONNECT`) : zenodo.org, figshare.com, www.kaggle.com, www.iuii.ua.es, drive.google.com, huggingface.co, captain-whu.github.io, datasetninja.com, universe.roboflow.com, data.mendeley.com, data.bas.ac.uk, ramadda.data.bas.ac.uk, datadryad.org, www.nature.com, zslpublications.onlinelibrary.wiley.com, digibug.ugr.es, ncbi.nlm.nih.gov, lila.science (site web), seadronessee.cs.uni-tuebingen.de, ultralytics.com, github.com/*/releases. Accessibles : raw.githubusercontent.com, clonage git de github.com, storage.googleapis.com (bucket `public-datasets-lila`), pypi.org.

### 3.1 Aérien et satellite marins

| Jeu | Contenu | Taille | Accès | Licence | Statut |
|---|---|---|---|---|---|
| **Whales from space** (Cubaynes & Fretwell 2022, Sci. Data 9:245) | 633 baleines annotées (boîtes + points, 9 shapefiles) sur 6 300 km² WorldView-2/3, GeoEye-1, QuickBird-2 ; 4 espèces ; chips 150x150 | ~10 Mo (shapefiles), chips sur demande | shapefiles : https://doi.org/10.5285/C1AFE32C-493C-4DC7-AF9F-649593B97B2C ; chips : demande à PDCServiceDesk@bas.ac.uk (imagerie © Maxar) | CC BY 4.0 (annotations) ; imagerie Maxar sous licence | **inaccessible** (BAS bloqué). Récupéré à la place : échantillon GitHub `WSiqiqi/WSDataset` (20 chips YOLO, 8 originaux + variantes bruitées), audité. |
| **Guirado et al. 2019** (Sci. Rep. 9:14259) | 700 images présence/absence + 945 baleines pour le comptage (Google Earth, Arkive, NOAA) ; test 13 348 images | non publié | https://github.com/EGuirado/CNN-Whales-from-Space (README + 2 figures seulement) ; données « sur demande raisonnable et autorisation écrite de Google Earth / Arkive / NOAA » | images non redistribuables | **inaccessible** (dépôt cloné : aucune donnée). |
| **Green et al. 2023** (RSEC 9:829) | baleines grises, satellite Maxar + drone (53 individus Oregon) ; 503 baleines / 103 bateaux train+val+test | non publié | https://doi.org/10.1002/rse2.352 ; aucun dépôt public identifié (Wiley et NORA bloqués, la recherche web ne mentionne pas de dépôt) ; contacter Duke MaRRS Lab | imagerie Maxar sous licence | **inaccessible / non publié**. |
| **MASATI v2** (Gallego et al.) | 7 389 images 512x512, 7 classes (land, coast, sea, ship, multi, coast-ship, detail), boîtes navires ; pas de faune | ~ 1–2 Go | formulaire sur https://www.iuii.ua.es/datasets/masati/index.html (miroir Kaggle `louisaberdeen/masati-v2`) | non lucratif recherche/éducation | **inaccessible** (ua.es et Kaggle bloqués). Pertinence GoldenEye limitée (objets = navires). |
| **NOAA Right Whale Recognition** (Kaggle 2015) | 11 469 images aériennes obliques = 4 544 train (447 individus, `train.csv`) + 6 925 test ; **aucune boîte officielle** | ~10 Go (`imgs.zip`) | https://www.kaggle.com/c/noaa-right-whale-recognition/rules (acceptation manuelle des règles + jeton API) ; `scripts/kaggle_download.sh` | règles de compétition (non commercial) | **inaccessible** (Kaggle bloqué). Récupéré : boîtes tête communautaires (4 547, MIT) `Smerity/right_whale_hunt`, auditées en pixels (tête médiane 565x512 px). |
| **NOAA Steller Sea Lion** (Kaggle 2017) | 948 images train (+ versions pointées) + 18 641 test ; annotation par **points colorés** (5 classes) et comptes | **103 Go** | https://www.kaggle.com/c/noaa-fisheries-steller-sea-lion-population-count/rules ; échantillon `TrainSmall2.zip` (~1 Go) | règles de compétition | **inaccessible** et de toute façon non téléchargé intégralement (documenté, commandes d'échantillon dans `scripts/kaggle_download.sh`). Points, pas boîtes. |
| **NOAA Arctic Seals 2019** (LILA BC, non demandé mais pertinent) | 44 185 paires RGB/IR avion (KAMERA, mer de Béring/Tchouktches), 14 311 boîtes phoques (ringed 11 382, unknown 1 619, bearded 692, pups 618), score de détection médian 1,0 | ~1 To ; échantillon 8,1 Go | https://storage.googleapis.com/public-datasets-lila/noaa-kotz/ (HTTP direct) ; `scripts/fetch_lila_noaa_seals_sample.py` | CDLA-Permissive 1.0 | **récupéré** : CSV complet + 202 images RGB annotées (stratifiées sur 4 vols) + 14 vides ; COCO échantillon et COCO complet (annotations seules). |
| Gray et al. 2019 tortues drone (LILA liste) | 1 059 images NIR, 1 902 points | 7,24 Go | https://zenodo.org/record/5004596 | CC0 | **inaccessible** (Zenodo). Points seulement. |
| Beluga-seeker (Zheng et al., IGARSS 2025) | 538 chips satellite 320/192 px, 1 622 boîtes (belugas certains/incertains, phoques du Groenland) | 6,5 Mo (annotations) | https://github.com/VoyagerXvoyagerx/beluga-seeker ; images à demander aux auteurs | code GPL-3.0, données non précisées | **récupéré partiel** (annotations + 4 images). |

### 3.2 Aérien non marin (sondes de décalage de domaine)

| Jeu | Contenu | Taille | Accès | Licence | Statut |
|---|---|---|---|---|---|
| **VisDrone-DET 2019** | 10 209 images drone (6 471 / 548 / 1 610 / 1 580), 10 classes, format txt `x,y,w,h,score,cls,trunc,occl` | train 1,44 Go + val 0,07 + test-dev 0,28 | Google Drive / Baidu (liens dans https://github.com/VisDrone/VisDrone-Dataset) | recherche (citer Zhu et al. 2021) | **inaccessible** (drive.google.com bloqué). |
| **DOTA** v1.0 / v1.5 / v2.0 | 2 806 images / 188 282 instances (v1.0) ; 11 268 / 1 793 658 (v2.0) ; boîtes orientées, 15–18 classes | ~20 Go (v1.0) | https://captain-whu.github.io/DOTA/dataset.html (Google Drive / Baidu) | académique uniquement | **inaccessible** (github.io et Drive bloqués). |
| UAS imagery of migratory waterfowl (LILA) | 12 images drone 5472x3648 (2 243 boîtes experts) + 338 tuiles 684x521 (2 175 boîtes crowd) | 322 Mo | https://storage.googleapis.com/public-datasets-lila/uas-imagery-of-migratory-waterfowl/ | CC BY-NC 2.0 | **récupéré** et audité (remplace VisDrone comme sonde drone). |
| Izembek lagoon birds (USGS, LILA) | 9 267 images 8688x5792, 521 270 boîtes fixes 18x18 (points) | 126 Go (images), 9,6 Mo (métadonnées) | https://storage.googleapis.com/public-datasets-lila/izembek-lagoon-birds/ | CDLA-Permissive 1.0 | **métadonnées récupérées**, audit annotations seules ; images non téléchargées. |
| Conservation Drones (LILA) | vidéos thermiques drone, humains/animaux, boîtes | test 1,7 Go, train 2,2 Go | https://storage.googleapis.com/public-datasets-lila/conservationdrones/v01/ | voir LILA | accessible, **non téléchargé** (thermique, hors périmètre RGB). |
| SeaDronesSee | 5 630 images drone maritime, boîtes nageurs/bateaux | ~ 10 Go | https://seadronessee.cs.uni-tuebingen.de/ (inscription) | recherche | **inaccessible**. |

### 3.3 Sous-marin (références publiques, à défaut du jeu interne)

| Jeu | Contenu | Accès | Licence | Statut |
|---|---|---|---|---|
| NOAA Puget Sound estuary fish (LILA) | 77 689 trames 1920x1080, 67 990 boîtes (fish 56 158, crab 5 285, fish_or_crab 5 927, unknown 620) | annotations 4 Mo ; images 7,3 Go `noaa-psnf/noaa_estuary_fish-images.zip` | CDLA-Permissive 1.0 | annotations récupérées et auditées ; images non téléchargées. |
| Community Fish Detection Dataset (LILA) | 1,9 M images multi-sources, 935 049 boîtes poissons | annotations 45 Mo (zip) ; images `community-fish-detection-dataset/JPEGImages/` | variable par source | annotations récupérées et auditées. |

## 4. Normalisation COCO classe unique « objet »

`scripts/to_coco_single_class.py` fusionne toutes les catégories en `objet` (id 1), conserve la classe source dans `source_class`, supprime les catégories « vide » (`--drop-classes empty`), et garde `width/height` source quand les images sont absentes. Fichiers produits :

| Fichier | images (sur disque) | boîtes | note |
|---|---|---|---|
| `data/satellite/WSDataset/coco_objet.json` | 20 (20) | 20 | YOLO → COCO |
| `data/satellite/beluga_seeker/coco_objet_sam.json` | 538 (4) | 1 622 | boîtes SAM ; `coco_objet_box.json` = tampons fixes, exclu de la comparaison |
| `data/aerien/noaa_arctic_seals_2019/coco_objet_sample.json` | 216 (216) | 718 | CSV → COCO ; `rgb_top/bottom` parfois inversés dans le CSV, normalisés |
| `data/aerien/noaa_arctic_seals_2019/coco_objet_full_rgb.json` | 44 185 (216) | 14 311 | taille 6576x4384 supposée pour toutes (vérifiée sur 216) ; non versionné (régénéré par le script) |
| `data/aerien/noaa_right_whale_kaggle_annotations/coco_objet_vinh_heads.json` | 4 544 (0) | 4 547 | Sloth → COCO, tailles inconnues |
| `data/aerien_non_marin/uas_migratory_waterfowl/coco_objet_experts.json` | 12 (12) | 2 243 | |
| `data/aerien_non_marin/uas_migratory_waterfowl/coco_objet_crowd.json` | 338 (356 sur disque) | 2 175 | 18 tuiles sans annotation dans le json |
| `data/aerien_non_marin/izembek_lagoon_birds/coco_objet.json` | 9 267 (0) | 521 270 | non versionné (74 Mo) |
| `data/sous-marin/noaa_estuary_fish/coco_objet.json` | 77 689 (0) | 67 990 | |
| `data/sous-marin/community_fish_detection/coco_objet.json` | 1 903 035 (0) | 935 049 | non versionné (414 Mo) |

Chaque fichier a été passé dans `audit_dataset.py` (résultats dans `audits/<nom>/summary.json`, et tableaux ci-dessus).

## 5. Actions à mener hors de cet environnement

1. Fournir les deux chemins locaux (ou pousser les données dans `data/sous-marin/local` et `data/aerien/local`) et relancer `scripts/run_audit_pipeline.sh` : l'audit, les 20 PNG aériens internes et la conclusion chiffrée sur l'écart 90 → 58 en découlent directement.
2. Ouvrir manuellement et accepter les règles : https://www.kaggle.com/c/noaa-right-whale-recognition/rules et https://www.kaggle.com/c/noaa-fisheries-steller-sea-lion-population-count/rules, puis `scripts/kaggle_download.sh` (jeton API requis ; Steller : échantillon seulement).
3. Demander les chips Whales from space à PDCServiceDesk@bas.ac.uk (633 chips, licence Maxar) et télécharger les shapefiles via le DOI.
4. Autoriser dans la politique réseau (ou télécharger depuis un poste) : drive.google.com (VisDrone 1,8 Go, DOTA ~20 Go), zenodo.org (tortues 7,2 Go), www.iuii.ua.es (MASATI).
5. Si le jeu aérien interne s'avère « plein cadre », prévoir une évaluation tuilée avant toute conclusion sur la généralisation.

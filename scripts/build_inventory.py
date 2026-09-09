#!/usr/bin/env python3
"""Construit inventory.csv : une ligne par jeu de données (locaux, récupérés, inaccessibles).

Les colonnes chiffrées (nb images, nb objets) sont lues dans audits/<nom>/summary.json quand un audit existe,
sinon depuis le catalogue ci-dessous (valeurs publiées). La taille disque est mesurée dans data/.
Usage : python scripts/build_inventory.py [--out inventory.csv]
"""
import argparse
import csv
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# nom, domaine, audit (dossier audits/ ou None), dossier data (ou None), champs catalogue
CATALOGUE = [
    dict(nom="sous_marin_local", domaine="sous-marin", audit="sous_marin_local", data="data/sous-marin/local",
         nb_images="?", nb_objets="?", annote="oui (annoncé)", format_source="YOLO txt et/ou COCO json (à vérifier)", licence="interne SogetiLabs",
         statut="NON AUDITÉ : chemin <CHEMIN> non fourni, aucune image trouvée dans le conteneur, le dépôt ni le Drive", url="(chemin local à fournir)"),
    dict(nom="aerien_local_478", domaine="aérien", audit="aerien_local", data="data/aerien/local",
         nb_images="478 (annoncé)", nb_objets="?", annote="oui (annoncé)", format_source="YOLO txt et/ou COCO json (à vérifier)", licence="interne SogetiLabs",
         statut="NON AUDITÉ : chemin <CHEMIN> non fourni, aucune image trouvée dans le conteneur, le dépôt ni le Drive", url="(chemin local à fournir)"),
    dict(nom="whales_from_space_sample", domaine="satellite", audit="whales_from_space_sample", data="data/satellite/WSDataset",
         annote="oui", format_source="YOLO txt (cls xc yc w h), PNG 8 bits", licence="CC BY 4.0 (dérivé de Cubaynes & Fretwell 2022)",
         statut="RÉCUPÉRÉ (GitHub) : 20 chips dont 8 originaux + variantes bruitées/ajustées", url="https://github.com/WSiqiqi/WSDataset"),
    dict(nom="whales_from_space_full", domaine="satellite", audit=None, data=None, nb_images="633 chips 150x150 (publié)", nb_objets="633 boîtes + 633 points",
         annote="oui", format_source="shapefiles boîtes + points (ArcGIS), chips GeoTIFF", licence="annotations CC BY 4.0 ; imagerie © Maxar (chips sur demande)",
         statut="INACCESSIBLE : data.bas.ac.uk / ramadda.data.bas.ac.uk bloqués (403 proxy) ; chips délivrés sur demande à PDCServiceDesk@bas.ac.uk",
         url="https://doi.org/10.5285/C1AFE32C-493C-4DC7-AF9F-649593B97B2C"),
    dict(nom="beluga_seeker_sam", domaine="satellite", audit="beluga_seeker_sam", data="data/satellite/beluga_seeker",
         annote="partiel (annotations complètes, 4 images sur 538 dans le dépôt)", format_source="COCO json (boîtes SAM + boîtes tampon fixes), chips PNG 320x320 / 192x192 panchromatiques",
         licence="code GPL-3.0 ; données non précisées (imagerie Maxar/WorldView) ", statut="RÉCUPÉRÉ PARTIEL (GitHub) : annotations seules ; images à demander aux auteurs (UCAS)",
         url="https://github.com/VoyagerXvoyagerx/beluga-seeker"),
    dict(nom="guirado_2019", domaine="satellite + aérien", audit=None, data=None, nb_images="700 (présence) + 945 baleines (comptage) ; test 13 348", nb_objets="945 baleines (publié)",
         annote="oui (chez les auteurs)", format_source="TF object detection (non publié)", licence="images Google Earth / Arkive / NOAA : non redistribuables",
         statut="INACCESSIBLE : le dépôt GitHub ne contient que le README et 2 figures ; données 'sur demande raisonnable et autorisation écrite'",
         url="https://github.com/EGuirado/CNN-Whales-from-Space ; https://doi.org/10.1038/s41598-019-50795-9"),
    dict(nom="green_2023_gray_whales", domaine="satellite + aérien (drone)", audit=None, data=None, nb_images="?", nb_objets="503 baleines + 103 bateaux (train/val/test publiés)",
         annote="oui (chez les auteurs)", format_source="YOLOv5 (publié)", licence="imagerie Maxar sous licence ; pas de dépôt public identifié",
         statut="INACCESSIBLE : aucun dépôt de données public identifié (Wiley/NORA bloqués) ; contacter les auteurs (Duke MaRRS Lab)",
         url="https://doi.org/10.1002/rse2.352"),
    dict(nom="masati_v2", domaine="satellite (aérien optique)", audit=None, data=None, nb_images="7 389", nb_objets="boîtes navires (classes ship, multi, coast-ship, detail)",
         annote="oui (bateaux, pas de faune)", format_source="images PNG 512x512 + XML boîtes", licence="usage non lucratif recherche/éducation, sur demande",
         statut="INACCESSIBLE : www.iuii.ua.es bloqué (403 proxy) ; formulaire de demande sur la page", url="https://www.iuii.ua.es/datasets/masati/index.html"),
    dict(nom="noaa_right_whale_kaggle", domaine="aérien", audit=None, data=None, nb_images="11 469 (4 544 train + 6 925 test)", nb_objets="0 boîte officielle (identité par image)",
         annote="non (ID individu seulement)", format_source="JPG + train.csv (whaleID)", licence="règles de compétition Kaggle (usage non commercial)",
         statut="INACCESSIBLE : www.kaggle.com bloqué (403 proxy) ; nécessite compte + acceptation des règles", url="https://www.kaggle.com/c/noaa-right-whale-recognition/rules"),
    dict(nom="noaa_right_whale_heads", domaine="aérien", audit="noaa_right_whale_heads", data="data/aerien/noaa_right_whale_kaggle_annotations",
         annote="partiel (boîtes tête sans les images)", format_source="Sloth json (rect x,y,width,height ; classes Head/Body)", licence="MIT (annotations) ; images Kaggle",
         statut="RÉCUPÉRÉ PARTIEL (GitHub) : 4 547 boîtes 'Head' sur 4 544 images train ; dimensions images inconnues -> pas d'aire relative",
         url="https://github.com/Smerity/right_whale_hunt"),
    dict(nom="noaa_steller_sea_lion_kaggle", domaine="aérien", audit=None, data=None, nb_images="948 train + 18 641 test (publié)", nb_objets="points colorés par classe (TrainDotted), pas de boîtes",
         annote="partiel (points)", format_source="JPG + train.csv comptes + images pointées", licence="règles de compétition Kaggle",
         statut="INACCESSIBLE : Kaggle bloqué ; 103 Go : ne pas télécharger intégralement, échantillon TrainSmall2.zip (~1 Go) via scripts/kaggle_download.sh",
         url="https://www.kaggle.com/c/noaa-fisheries-steller-sea-lion-population-count/rules"),
    dict(nom="noaa_arctic_seals_2019_sample", domaine="aérien", audit="noaa_arctic_seals_sample", data="data/aerien/noaa_arctic_seals_2019",
         annote="oui", format_source="CSV (rgb_left/right/top/bottom + IR) -> COCO ; JPG 6576x4384", licence="CDLA-Permissive 1.0 (LILA BC)",
         statut="RÉCUPÉRÉ (LILA/GCS) : échantillon stratifié 4 vols, 202 images RGB annotées sur 4 113 (8,1 Go) ; jeu complet ~1 To", url="https://lila.science/datasets/noaa-arctic-seals-2019/"),
    dict(nom="noaa_arctic_seals_2019_full", domaine="aérien", audit="noaa_arctic_seals_full_rgb", data=None,
         annote="oui", format_source="CSV détections validées (score) ; 44 185 paires RGB/IR", licence="CDLA-Permissive 1.0 (LILA BC)",
         statut="AUDIT SUR ANNOTATIONS SEULES (taille image supposée 6576x4384, vérifiée sur 202 images)", url="https://storage.googleapis.com/public-datasets-lila/noaa-kotz/"),
    dict(nom="uas_waterfowl_experts", domaine="aérien non marin", audit="uas_waterfowl_experts", data="data/aerien_non_marin/uas_migratory_waterfowl",
         annote="oui", format_source="COCO json ; JPG 5472x3648 (drone DJI Mavic 2 Pro)", licence="CC BY-NC 2.0",
         statut="RÉCUPÉRÉ (LILA/GCS) : 12 images plein cadre, 2 243 boîtes consensus experts", url="https://lila.science/datasets/uas-imagery-of-migratory-waterfowl/"),
    dict(nom="uas_waterfowl_crowd", domaine="aérien non marin", audit="uas_waterfowl_crowd", data=None,
         annote="oui", format_source="COCO json ; tuiles PNG 684x521", licence="CC BY-NC 2.0",
         statut="RÉCUPÉRÉ (LILA/GCS) : 338 tuiles, 2 175 boîtes consensus Zooniverse", url="https://lila.science/datasets/uas-imagery-of-migratory-waterfowl/"),
    dict(nom="izembek_lagoon_birds", domaine="aérien non marin (littoral)", audit="izembek_lagoon_birds", data="data/aerien_non_marin/izembek_lagoon_birds",
         annote="oui (boîtes fixes 18x18 = points)", format_source="COCO json ; JPG 8688x5792", licence="CDLA-Permissive 1.0 (USGS)",
         statut="AUDIT SUR ANNOTATIONS SEULES (images 126 Go non téléchargées)", url="https://lila.science/datasets/izembek-lagoon-waterfowl/"),
    dict(nom="visdrone_det", domaine="aérien non marin", audit=None, data=None, nb_images="10 209 (6 471 train / 548 val / 1 610 test-dev / 1 580 challenge)", nb_objets=">540 000 boîtes, 10 classes",
         annote="oui", format_source="txt par image : x,y,w,h,score,cls,truncation,occlusion", licence="usage recherche (citation Zhu et al. 2021)",
         statut="INACCESSIBLE : hébergé sur Google Drive / Baidu (drive.google.com bloqué 403) ; train 1,44 Go + val 0,07 Go + test-dev 0,28 Go",
         url="https://github.com/VisDrone/VisDrone-Dataset"),
    dict(nom="dota", domaine="aérien non marin (satellite/aérien)", audit=None, data=None, nb_images="v1.0 : 2 806 ; v2.0 : 11 268", nb_objets="v1.0 : 188 282 ; v1.5 : 403 318 ; v2.0 : 1 793 658 (OBB)",
         annote="oui (boîtes orientées)", format_source="txt : 8 coordonnées + classe + difficulté", licence="académique uniquement, usage commercial interdit",
         statut="INACCESSIBLE : captain-whu.github.io et Google Drive bloqués (403) ; ~20 Go (v1.0)", url="https://captain-whu.github.io/DOTA/dataset.html"),
    dict(nom="noaa_estuary_fish", domaine="sous-marin (référence)", audit="noaa_estuary_fish", data="data/sous-marin/noaa_estuary_fish",
         annote="oui", format_source="COCO json ; JPG 1920x1080 (vidéo GoPro estuaire)", licence="CDLA-Permissive 1.0 (LILA BC)",
         statut="AUDIT SUR ANNOTATIONS SEULES (images 7,3 Go disponibles : noaa-psnf/noaa_estuary_fish-images.zip)", url="https://lila.science/datasets/noaa-puget-sound-nearshore-fish/"),
    dict(nom="community_fish_detection", domaine="sous-marin (référence)", audit="community_fish_detection", data="data/sous-marin/community_fish_detection",
         annote="oui", format_source="COCO json agrégé (multi-sources)", licence="variable selon source (voir page LILA)",
         statut="AUDIT SUR ANNOTATIONS SEULES (images sous community-fish-detection-dataset/JPEGImages/)", url="https://lila.science/datasets/community-fish-detection-dataset/"),
    dict(nom="gray_2019_sea_turtles_drone", domaine="aérien", audit=None, data=None, nb_images="1 059 (NIR)", nb_objets="1 902 points",
         annote="partiel (points)", format_source="CSV points", licence="CC0", statut="INACCESSIBLE : zenodo.org bloqué (403) ; 7,24 Go", url="https://zenodo.org/record/5004596"),
    dict(nom="seadronessee", domaine="aérien (maritime, humains/bateaux)", audit=None, data=None, nb_images="5 630 (DET)", nb_objets="boîtes swimmer/boat/jetski/buoy",
         annote="oui", format_source="COCO json", licence="usage recherche (inscription)", statut="INACCESSIBLE : seadronessee.cs.uni-tuebingen.de bloqué (403)", url="https://seadronessee.cs.uni-tuebingen.de/"),
]


def du(path):
    if not path or not os.path.exists(os.path.join(ROOT, path)):
        return ""
    out = subprocess.run(["du", "-sh", os.path.join(ROOT, path)], capture_output=True, text=True).stdout
    return out.split()[0] if out else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "inventory.csv"))
    a = ap.parse_args()
    rows = []
    for c in CATALOGUE:
        r = {"nom": c["nom"], "domaine": c["domaine"], "nb_images": c.get("nb_images", ""), "nb_objets": c.get("nb_objets", ""),
             "annote": c["annote"], "format_source": c["format_source"], "licence": c["licence"],
             "taille_disque": du(c.get("data")), "statut_acquisition": c["statut"], "url": c["url"],
             "boite_aire_rel_mediane_pct": "", "objets_par_image_median": ""}
        sp = os.path.join(ROOT, "audits", c["audit"] or "_", "summary.json")
        if c["audit"] and os.path.exists(sp):
            s = json.load(open(sp))
            r["nb_images"] = s["n_images_on_disk"] if s["n_images_on_disk"] else f"{s['n_images_in_annotations']} (annotations seules)"
            r["nb_objets"] = s["n_objects"]
            p50 = s["box_rel_area_pct"]["p50"]
            r["boite_aire_rel_mediane_pct"] = f"{p50:.4f}" if p50 is not None else "n/a"
            r["objets_par_image_median"] = s["objects_per_image"]["p50"]
        rows.append(r)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{a.out}: {len(rows)} lignes")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Échantillonne le jeu NOAA Arctic Seals 2019 (LILA BC, bucket GCS public) sans le télécharger en entier (~1 To).

Télécharge :
  - Detections/surv_test_kamera_detections_20210212.csv (boîtes RGB + IR, 14 311 lignes)
  - Images/surv_test_kamera_images_20201217.csv (liste des 88 228 images)
  - surv_test_kamera_files.txt (chemins exacts dans le bucket)
  - un échantillon stratifié par vol d'images RGB annotées (--n-annotated) et non annotées (--n-empty)
Puis écrit un COCO classe unique "objet" restreint aux images téléchargées : coco_objet_sample.json

Usage : python scripts/fetch_lila_noaa_seals_sample.py --out data/aerien/noaa_arctic_seals_2019 --n-annotated 250 --n-empty 30 --max-gb 4
Source : https://lila.science/datasets/noaa-arctic-seals-2019/  (licence CDLA-Permissive 1.0 d'après LILA)
"""
import argparse
import json
import os
import random
import sys
import urllib.request

import pandas as pd

BASE = "https://storage.googleapis.com/public-datasets-lila/noaa-kotz/"


def fetch(rel, dst, quiet=False):
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return os.path.getsize(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    url = BASE + rel
    with urllib.request.urlopen(url, timeout=300) as r, open(dst + ".part", "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    os.replace(dst + ".part", dst)
    if not quiet:
        print("  ok", rel, round(os.path.getsize(dst) / 1e6, 1), "MB", flush=True)
    return os.path.getsize(dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-annotated", type=int, default=250)
    ap.add_argument("--n-empty", type=int, default=30)
    ap.add_argument("--max-gb", type=float, default=4.0)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    random.seed(a.seed)
    out = a.out
    det_csv = os.path.join(out, "Detections/surv_test_kamera_detections_20210212.csv")
    img_csv = os.path.join(out, "Images/surv_test_kamera_images_20201217.csv")
    files_txt = os.path.join(out, "surv_test_kamera_files.txt")
    fetch("Detections/surv_test_kamera_detections_20210212.csv", det_csv)
    fetch("Images/surv_test_kamera_images_20201217.csv", img_csv)
    fetch("surv_test_kamera_files.txt", files_txt)

    det = pd.read_csv(det_csv)
    paths = {os.path.basename(l.strip()): l.strip() for l in open(files_txt) if l.strip().endswith("_rgb.jpg")}
    annotated = sorted(set(det["rgb_image_name"]) & set(paths))
    all_rgb = sorted(paths)
    empty = sorted(set(all_rgb) - set(det["rgb_image_name"]))
    print(f"RGB dans le bucket: {len(all_rgb)} ; annotées: {len(annotated)} ; sans détection: {len(empty)} ; "
          f"boîtes RGB: {len(det)} ; images annotées absentes du bucket: {len(set(det['rgb_image_name']) - set(paths))}")

    # stratification par vol (fl04..fl07) proportionnelle
    by_flight = {}
    for n in annotated:
        by_flight.setdefault(n.split("_")[3], []).append(n)
    chosen = []
    for fl, names in sorted(by_flight.items()):
        k = max(1, round(a.n_annotated * len(names) / len(annotated)))
        chosen += random.sample(names, min(k, len(names)))
    chosen = chosen[: a.n_annotated]
    random.shuffle(chosen)  # interleaver les vols pour qu'un budget partiel reste stratifié
    chosen_empty = random.sample(empty, min(a.n_empty, len(empty)))

    budget = a.max_gb * 1e9
    got = 0
    downloaded = []
    for i, n in enumerate(chosen + chosen_empty):
        if got > budget:
            print("budget atteint", round(got / 1e9, 2), "GB ; arrêt")
            break
        rel = paths[n]
        dst = os.path.join(out, rel)
        try:
            got += fetch(rel, dst, quiet=True)
            downloaded.append(n)
        except Exception as e:
            print("  ECHEC", rel, e, file=sys.stderr)
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(chosen) + len(chosen_empty)} fichiers, {got / 1e9:.2f} GB", flush=True)
    print(f"téléchargé {len(downloaded)} images RGB ({got / 1e9:.2f} GB)")

    # COCO classe unique sur les images téléchargées (tailles lues sur disque)
    from PIL import Image
    images, anns = [], []
    dset = set(downloaded)
    for i, n in enumerate(sorted(dset), start=1):
        p = os.path.join(out, paths[n])
        with Image.open(p) as im:
            W, H = im.size
        images.append({"id": i, "file_name": paths[n], "width": W, "height": H, "flight": n.split("_")[3], "camera": n.split("_")[4]})
        sub = det[det["rgb_image_name"] == n]
        for _, r in sub.iterrows():
            x1, x2 = sorted([float(r.rgb_left), float(r.rgb_right)])
            y1, y2 = sorted([float(r.rgb_top), float(r.rgb_bottom)])
            anns.append({"id": len(anns) + 1, "image_id": i, "category_id": 1, "bbox": [x1, y1, x2 - x1, y2 - y1],
                         "area": (x2 - x1) * (y2 - y1), "iscrowd": 0, "source_class": r.detection_type,
                         "detection_score": float(r.detection_score)})
    coco = {"info": {"description": "NOAA Arctic Seals 2019 (LILA) - échantillon RGB - COCO classe unique 'objet'",
                     "license": "CDLA-Permissive 1.0 (voir page LILA)", "source": BASE,
                     "note": "rgb_top/rgb_bottom sont parfois inversés dans le CSV source ; normalisés par min/max"},
            "licenses": [], "categories": [{"id": 1, "name": "objet"}], "images": images, "annotations": anns}
    json.dump(coco, open(os.path.join(out, "coco_objet_sample.json"), "w"))
    print(f"coco_objet_sample.json : {len(images)} images, {len(anns)} boîtes")

    # COCO complet (annotations seules) : toutes les images RGB du bucket avec la taille observée sur l'échantillon
    sizes = {}
    for im in images:
        sizes[(im["width"], im["height"])] = sizes.get((im["width"], im["height"]), 0) + 1
    (W, H), _ = max(sizes.items(), key=lambda kv: kv[1]) if sizes else ((6576, 4384), 0)
    images_f, anns_f = [], []
    id_of = {}
    for i, n in enumerate(all_rgb, start=1):
        id_of[n] = i
        images_f.append({"id": i, "file_name": paths[n], "width": W, "height": H, "on_disk": n in dset})
    for _, r in det.iterrows():
        if r.rgb_image_name not in id_of:
            continue
        x1, x2 = sorted([float(r.rgb_left), float(r.rgb_right)])
        y1, y2 = sorted([float(r.rgb_top), float(r.rgb_bottom)])
        anns_f.append({"id": len(anns_f) + 1, "image_id": id_of[r.rgb_image_name], "category_id": 1,
                       "bbox": [x1, y1, x2 - x1, y2 - y1], "area": (x2 - x1) * (y2 - y1), "iscrowd": 0,
                       "source_class": r.detection_type, "detection_score": float(r.detection_score)})
    coco_f = dict(coco, images=images_f, annotations=anns_f)
    coco_f["info"] = dict(coco["info"], description="NOAA Arctic Seals 2019 (LILA) - toutes les images RGB (annotations seules) - COCO classe unique 'objet'",
                          image_size_assumption=f"{W}x{H} pour toutes les images RGB (taille observée sur {len(images)} images téléchargées, {len(sizes)} taille(s) distincte(s))")
    json.dump(coco_f, open(os.path.join(out, "coco_objet_full_rgb.json"), "w"))
    print(f"coco_objet_full_rgb.json : {len(images_f)} images RGB, {len(anns_f)} boîtes (taille supposée {W}x{H})")


if __name__ == "__main__":
    main()

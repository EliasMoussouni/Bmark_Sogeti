#!/usr/bin/env python3
"""Audit d'un jeu de détection (YOLO txt ou COCO json) pour le projet GoldenEye.

Produit dans --out :
  summary.json   : statistiques globales (images, résolutions, objets, tailles de boîtes,
                   images vides, boîtes dégénérées / hors cadre, schéma d'annotation)
  boxes.csv      : une ligne par boîte (pixels, % aire image, ratio d'aspect, flags)
  per_image.csv  : une ligne par image (taille, nb objets, flags)

Usage :
  python scripts/audit_dataset.py --name aerien_local --domain aerien \
      --images data/aerien/images --ann data/aerien/labels --format yolo --out audits/aerien_local
  python scripts/audit_dataset.py --name x --domain satellite \
      --images data/x/images --ann data/x/annotations.json --format coco --out audits/x

Conventions :
  - YOLO : un .txt par image (même nom de base), lignes "cls xc yc w h" normalisées [0,1].
           Les lignes avec plus de 5 colonnes (polygones / segments) sont converties en boîte
           englobante et comptées dans schema.polygon_lines.
  - COCO : bbox = [x, y, w, h] en pixels (coin haut-gauche).
  - Une boîte est "dégénérée" si w<=0, h<=0 ou aire < 1 px².
  - Une boîte est "hors cadre" si elle dépasse l'image de plus de 0.5 px sur un bord.
"""
import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".JPG", ".PNG", ".JPEG", ".TIF", ".TIFF"}
PCTS = [5, 25, 50, 75, 95]


def list_images(root):
    out = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            stem, ext = os.path.splitext(fn)
            if ext in IMG_EXT:
                rel = os.path.relpath(os.path.join(dp, fn), root)
                out[rel] = os.path.join(dp, fn)
    return out


def image_size(path):
    if Image is None:
        return None, None, None
    try:
        with Image.open(path) as im:
            return im.size[0], im.size[1], im.mode
    except Exception:
        return None, None, None


def pct(a):
    a = np.asarray(a, dtype=float)
    if a.size == 0:
        return {f"p{p}": None for p in PCTS} | {"min": None, "max": None, "mean": None, "n": 0}
    d = {f"p{p}": float(np.percentile(a, p)) for p in PCTS}
    d.update(min=float(a.min()), max=float(a.max()), mean=float(a.mean()), n=int(a.size))
    return d


def load_yolo(images, ann_root):
    """Retourne dict rel_image -> liste de boîtes absolues [x,y,w,h,cls] + schéma."""
    # index des labels par stem (robuste aux sous-dossiers images/ vs labels/)
    label_files = {}
    for dp, _, fns in os.walk(ann_root):
        for fn in fns:
            if fn.endswith(".txt") and fn != "classes.txt":
                label_files.setdefault(os.path.splitext(fn)[0], []).append(os.path.join(dp, fn))
    schema = Counter()
    classes = Counter()
    boxes = {}
    n_lines_bad = 0
    for rel, path in images.items():
        stem = os.path.splitext(os.path.basename(rel))[0]
        cands = label_files.get(stem, [])
        if not cands:
            boxes[rel] = None  # pas de fichier label
            continue
        # si plusieurs candidats, prendre celui dont le chemin partage le plus de segments
        lf = cands[0]
        if len(cands) > 1:
            rp = set(rel.split(os.sep))
            lf = max(cands, key=lambda p: len(rp & set(p.split(os.sep))))
        W, H, _ = image_size(path)
        bl = []
        with open(lf) as f:
            for line in f:
                parts = line.split()
                if not parts:
                    continue
                try:
                    vals = [float(v) for v in parts]
                except ValueError:
                    n_lines_bad += 1
                    continue
                cls = int(vals[0])
                classes[cls] += 1
                if len(vals) == 5:
                    schema["bbox_lines"] += 1
                    xc, yc, w, h = vals[1:5]
                    x, y = xc - w / 2, yc - h / 2
                elif len(vals) >= 7 and (len(vals) - 1) % 2 == 0:
                    schema["polygon_lines"] += 1
                    xs, ys = vals[1::2], vals[2::2]
                    x, y, w, h = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
                elif len(vals) == 6:
                    schema["bbox_lines_with_conf"] += 1
                    xc, yc, w, h = vals[1:5]
                    x, y = xc - w / 2, yc - h / 2
                else:
                    n_lines_bad += 1
                    continue
                normalized = max(abs(x), abs(y), abs(w), abs(h)) <= 1.5
                if not normalized:
                    schema["unnormalized_lines"] += 1
                if W and H and normalized:
                    bl.append([x * W, y * H, w * W, h * H, cls])
                elif W and H:
                    bl.append([x, y, w, h, cls])
        boxes[rel] = bl
    schema["bad_lines"] = n_lines_bad
    return boxes, dict(schema), dict(classes), label_files


def load_coco(images, ann_path):
    with open(ann_path) as f:
        d = json.load(f)
    cats = {c["id"]: c.get("name", str(c["id"])) for c in d.get("categories", [])}
    id2img = {im["id"]: im for im in d["images"]}
    by_img = defaultdict(list)
    schema = Counter()
    ann_keys = Counter()
    for a in d["annotations"]:
        for k in a:
            ann_keys[k] += 1
        if "bbox" not in a or a["bbox"] is None or len(a["bbox"]) != 4:
            schema["annotations_without_bbox"] += 1
            continue
        if a.get("segmentation"):
            schema["with_segmentation"] += 1
        if a.get("iscrowd"):
            schema["iscrowd"] += 1
        x, y, w, h = a["bbox"]
        by_img[a["image_id"]].append([x, y, w, h, a.get("category_id", -1)])
    # correspondance file_name -> image locale (par nom de base si besoin)
    base_index = defaultdict(list)
    for rel in images:
        base_index[os.path.basename(rel)].append(rel)
    boxes = {}
    sizes_from_json = {}
    n_missing_on_disk = 0
    for iid, im in id2img.items():
        fn = im["file_name"]
        rel = fn if fn in images else None
        if rel is None:
            c = base_index.get(os.path.basename(fn), [])
            rel = c[0] if c else None
        key = rel if rel is not None else f"<absent>{fn}"
        if rel is None:
            n_missing_on_disk += 1
        boxes[key] = by_img.get(iid, [])
        if im.get("width") and im.get("height"):
            sizes_from_json[key] = (im["width"], im["height"])
    schema["images_in_json"] = len(id2img)
    schema["images_missing_on_disk"] = n_missing_on_disk
    schema["annotation_keys"] = dict(ann_keys)
    schema["image_keys"] = dict(Counter(k for im in d["images"] for k in im))
    schema["categories"] = cats
    schema["licenses"] = d.get("licenses")
    schema["info"] = d.get("info")
    classes = Counter(b[4] for bl in boxes.values() for b in bl)
    return boxes, dict(schema), {cats.get(k, k): v for k, v in classes.items()}, sizes_from_json


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--domain", required=True, help="sous-marin | aerien | satellite | aerien_non_marin")
    ap.add_argument("--images", required=True, help="dossier racine des images")
    ap.add_argument("--ann", required=True, help="dossier labels YOLO ou fichier COCO json")
    ap.add_argument("--format", required=True, choices=["yolo", "coco"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-images", type=int, default=0, help="0 = toutes")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    images = list_images(args.images)
    if args.max_images:
        images = dict(sorted(images.items())[: args.max_images])
    ext_counter = Counter(os.path.splitext(r)[1].lower() for r in images)

    if args.format == "yolo":
        boxes, schema, classes, _ = load_yolo(images, args.ann)
        sizes_json = {}
    else:
        boxes, schema, classes, sizes_json = load_coco(images, args.ann)

    per_image = []
    box_rows = []
    widths, heights = [], []
    modes = Counter()
    n_no_label_file = 0
    n_empty = 0
    n_degenerate = 0
    n_out_of_frame = 0
    for rel in sorted(set(images) | set(boxes)):
        path = images.get(rel)
        W = H = None
        mode = None
        if path:
            W, H, mode = image_size(path)
        if (W is None or H is None) and rel in sizes_json:
            W, H = sizes_json[rel]
        if W and H:
            widths.append(W)
            heights.append(H)
        if mode:
            modes[mode] += 1
        bl = boxes.get(rel)
        if bl is None:
            n_no_label_file += 1
            nb = 0
        else:
            nb = len(bl)
            if nb == 0:
                n_empty += 1
        img_deg = img_oof = 0
        for (x, y, w, h, cls) in (bl or []):
            deg = (w <= 0) or (h <= 0) or (w * h < 1)
            oof = False
            if W and H:
                oof = (x < -0.5) or (y < -0.5) or (x + w > W + 0.5) or (y + h > H + 0.5)
            img_deg += deg
            img_oof += oof
            rel_area = (w * h) / (W * H) * 100 if (W and H) else None
            box_rows.append({
                "dataset": args.name, "domain": args.domain, "image": rel, "img_w": W, "img_h": H,
                "x": round(x, 2), "y": round(y, 2), "w": round(w, 2), "h": round(h, 2), "cls": cls,
                "area_px": round(w * h, 2), "rel_area_pct": round(rel_area, 5) if rel_area is not None else None,
                "rel_w": round(w / W, 5) if W else None, "rel_h": round(h / H, 5) if H else None,
                "aspect_w_over_h": round(w / h, 4) if h > 0 else None,
                "degenerate": int(deg), "out_of_frame": int(oof),
            })
        n_degenerate += img_deg
        n_out_of_frame += img_oof
        per_image.append({"dataset": args.name, "domain": args.domain, "image": rel, "width": W, "height": H, "mode": mode,
                          "n_objects": nb, "has_label_file": int(bl is not None), "n_degenerate": img_deg,
                          "n_out_of_frame": img_oof, "on_disk": int(path is not None)})

    valid = [r for r in box_rows if not r["degenerate"] and r["rel_area_pct"] is not None]
    valid_px = [r for r in box_rows if not r["degenerate"]]  # stats pixels même sans taille d'image connue
    nobj = [p["n_objects"] for p in per_image if p["has_label_file"]]
    res_str = lambda arr: (int(np.min(arr)), int(np.median(arr)), int(np.max(arr))) if arr else None
    summary = {
        "name": args.name, "domain": args.domain, "format": args.format,
        "images_dir": args.images, "annotations": args.ann,
        "n_images_on_disk": len(images),
        "n_images_in_annotations": sum(1 for b in boxes.values() if b is not None),
        "image_formats": dict(ext_counter), "image_modes": dict(modes),
        "resolution_width_min_med_max": res_str(widths), "resolution_height_min_med_max": res_str(heights),
        "unique_resolutions": len(set(zip(widths, heights))),
        "n_objects": len(box_rows), "n_objects_valid": len(valid),
        "objects_per_image": pct(nobj) | {"histogram": dict(sorted(Counter(nobj).items()))},
        "n_images_without_label_file": n_no_label_file,
        "n_images_with_zero_objects": n_empty,
        "n_boxes_degenerate": n_degenerate, "n_boxes_out_of_frame": n_out_of_frame,
        "box_w_px": pct([r["w"] for r in valid_px]), "box_h_px": pct([r["h"] for r in valid_px]),
        "box_area_px": pct([r["area_px"] for r in valid_px]),
        "box_rel_area_pct": pct([r["rel_area_pct"] for r in valid]),
        "box_rel_side_pct": pct([100 * np.sqrt(r["rel_area_pct"] / 100) for r in valid]),
        "box_aspect_w_over_h": pct([r["aspect_w_over_h"] for r in valid_px if r["aspect_w_over_h"]]),
        "coco_size_buckets_pct": {
            "small_<32px2": round(100 * np.mean([r["area_px"] < 32 ** 2 for r in valid_px]), 2) if valid_px else None,
            "medium_32-96": round(100 * np.mean([32 ** 2 <= r["area_px"] < 96 ** 2 for r in valid_px]), 2) if valid_px else None,
            "large_>=96px2": round(100 * np.mean([r["area_px"] >= 96 ** 2 for r in valid_px]), 2) if valid_px else None,
        },
        "classes": {str(k): v for k, v in classes.items()},
        "schema": schema,
    }
    with open(os.path.join(args.out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    for fn, rows in (("boxes.csv", box_rows), ("per_image.csv", per_image)):
        with open(os.path.join(args.out, fn), "w", newline="") as f:
            if rows:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
    print(json.dumps({k: summary[k] for k in ("name", "n_images_on_disk", "n_objects", "n_images_with_zero_objects",
                                              "n_boxes_degenerate", "n_boxes_out_of_frame")}, ensure_ascii=False))
    print("  rel_area_pct:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in summary["box_rel_area_pct"].items()})
    print("  objects/image:", {k: v for k, v in summary["objects_per_image"].items() if k != "histogram"})


if __name__ == "__main__":
    main()

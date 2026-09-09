#!/usr/bin/env python3
"""Convertit un jeu annoté vers COCO avec une classe unique "objet" (CAOD).

Entrées supportées (--format) :
  yolo   : dossier labels YOLO (cls xc yc w h normalisés) + dossier images
  coco   : fichier COCO json (toutes catégories fusionnées en "objet")
  csv    : CSV générique avec colonnes image,x,y,w,h (pixels, coin haut-gauche) ;
           utiliser --csv-cols pour renommer (ex: --csv-cols image=rgb_image_name,x=x1,y=y1,x2=x2,y2=y2)
           si x2/y2 sont donnés, w/h sont déduits.
  sloth  : json Sloth (liste d'images {filename, annotations:[{x,y,width,height,class}]})

Options :
  --keep-classes  : ne garder que ces classes source (noms ou ids, séparés par des virgules)
  --drop-classes  : exclure ces classes (ex. "empty")
  --images-only-on-disk : ignorer les images absentes du dossier --images
  --clip          : rogner les boîtes au cadre de l'image
Sortie : --out fichier COCO json ; les images absentes sur disque gardent width/height source si connus.
"""
import argparse
import csv
import json
import os
import sys
from collections import Counter

IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def img_size(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def index_images(root):
    idx = {}
    if not root or not os.path.isdir(root):
        return idx
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in IMG_EXT:
                rel = os.path.relpath(os.path.join(dp, fn), root)
                idx[rel] = os.path.join(dp, fn)
                idx.setdefault(fn, os.path.join(dp, fn))
                idx.setdefault(os.path.splitext(fn)[0], os.path.join(dp, fn))
    return idx


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--format", required=True, choices=["yolo", "coco", "csv", "sloth"])
    ap.add_argument("--ann", required=True)
    ap.add_argument("--images", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dataset-name", default="dataset")
    ap.add_argument("--keep-classes", default=None)
    ap.add_argument("--drop-classes", default=None)
    ap.add_argument("--csv-cols", default="", help="mapping k=v séparé par des virgules")
    ap.add_argument("--images-only-on-disk", action="store_true")
    ap.add_argument("--clip", action="store_true")
    ap.add_argument("--license", default="", help="texte de licence à inscrire dans info")
    args = ap.parse_args()

    keep = set(args.keep_classes.split(",")) if args.keep_classes else None
    drop = set(args.drop_classes.split(",")) if args.drop_classes else set()
    idx = index_images(args.images)

    # collecte : dict file_name -> {"size": (w,h) or None, "boxes": [[x,y,w,h,src_cls]]}
    recs = {}
    src_classes = Counter()

    def add(fn, box, cls, size=None):
        r = recs.setdefault(fn, {"size": size, "boxes": []})
        if size and not r["size"]:
            r["size"] = size
        if box is not None:
            if keep is not None and str(cls) not in keep:
                return
            if str(cls) in drop:
                return
            src_classes[str(cls)] += 1
            r["boxes"].append(box + [cls])

    if args.format == "coco":
        d = json.load(open(args.ann))
        cats = {c["id"]: c.get("name", str(c["id"])) for c in d.get("categories", [])}
        id2fn = {}
        for im in d["images"]:
            id2fn[im["id"]] = im["file_name"]
            size = (im["width"], im["height"]) if im.get("width") and im.get("height") else None
            add(im["file_name"], None, None, size)
        for a in d["annotations"]:
            if not a.get("bbox") or len(a["bbox"]) != 4:
                continue
            add(id2fn[a["image_id"]], list(map(float, a["bbox"])), cats.get(a.get("category_id"), a.get("category_id")))
    elif args.format == "yolo":
        if not args.images:
            sys.exit("--images requis pour yolo")
        labels = {}
        for dp, _, fns in os.walk(args.ann):
            for fn in fns:
                if fn.endswith(".txt") and fn != "classes.txt":
                    labels.setdefault(os.path.splitext(fn)[0], os.path.join(dp, fn))
        for rel, path in idx.items():
            if os.sep not in rel and rel != os.path.basename(path):
                continue  # ignorer les alias
            if rel != os.path.relpath(path, args.images):
                continue
            stem = os.path.splitext(os.path.basename(rel))[0]
            size = img_size(path)
            add(rel, None, None, size)
            lf = labels.get(stem)
            if not lf or not size:
                continue
            W, H = size
            for line in open(lf):
                v = line.split()
                if len(v) < 5:
                    continue
                cls = v[0]
                nums = list(map(float, v[1:]))
                if len(nums) == 4 or len(nums) == 5:
                    xc, yc, w, h = nums[:4]
                    box = [(xc - w / 2) * W, (yc - h / 2) * H, w * W, h * H]
                else:
                    xs, ys = nums[0::2], nums[1::2]
                    box = [min(xs) * W, min(ys) * H, (max(xs) - min(xs)) * W, (max(ys) - min(ys)) * H]
                add(rel, box, cls)
    elif args.format == "csv":
        cols = dict(kv.split("=") for kv in args.csv_cols.split(",") if kv)
        c = lambda k: cols.get(k, k)
        with open(args.ann, newline="") as f:
            for row in csv.DictReader(f):
                fn = row[c("image")]
                x, y = float(row[c("x")]), float(row[c("y")])
                if c("x2") in row and c("y2") in row:
                    w, h = float(row[c("x2")]) - x, float(row[c("y2")]) - y
                else:
                    w, h = float(row[c("w")]), float(row[c("h")])
                cls = row.get(c("cls"), "objet")
                size = None
                if c("img_w") in row and c("img_h") in row and row[c("img_w")]:
                    size = (int(float(row[c("img_w")])), int(float(row[c("img_h")])))
                add(fn, [x, y, w, h], cls, size)
    elif args.format == "sloth":
        for e in json.load(open(args.ann)):
            fn = e["filename"]
            for a in e.get("annotations", []):
                if a.get("type", "rect") != "rect":
                    continue
                add(fn, [float(a["x"]), float(a["y"]), float(a["width"]), float(a["height"])], a.get("class", "objet"))
            add(fn, None, None)

    images, anns = [], []
    n_missing = n_clipped = 0
    for i, (fn, r) in enumerate(sorted(recs.items()), start=1):
        path = idx.get(fn) or idx.get(os.path.basename(fn)) or idx.get(os.path.splitext(os.path.basename(fn))[0])
        on_disk = path is not None
        if not on_disk:
            n_missing += 1
            if args.images_only_on_disk:
                continue
        size = r["size"] or (img_size(path) if on_disk else None)
        W, H = size if size else (None, None)
        images.append({"id": i, "file_name": os.path.relpath(path, args.images) if on_disk else fn,
                       "width": W, "height": H, "on_disk": on_disk})
        for (x, y, w, h, cls) in r["boxes"]:
            if args.clip and W and H:
                x2, y2 = min(x + w, W), min(y + h, H)
                nx, ny = max(x, 0), max(y, 0)
                if (nx, ny, x2 - nx, y2 - ny) != (x, y, w, h):
                    n_clipped += 1
                x, y, w, h = nx, ny, x2 - nx, y2 - ny
            anns.append({"id": len(anns) + 1, "image_id": i, "category_id": 1, "bbox": [round(x, 2), round(y, 2), round(w, 2), round(h, 2)],
                         "area": round(w * h, 2), "iscrowd": 0, "source_class": str(cls)})
    out = {"info": {"description": f"{args.dataset_name} - COCO classe unique 'objet' (CAOD GoldenEye)",
                    "source_annotations": os.path.abspath(args.ann), "source_format": args.format,
                    "license": args.license, "source_classes_kept": dict(src_classes)},
           "licenses": [], "categories": [{"id": 1, "name": "objet", "supercategory": "objet"}],
           "images": images, "annotations": anns}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(out, open(args.out, "w"), ensure_ascii=False)
    print(f"{args.out}: {len(images)} images ({n_missing} absentes du disque), {len(anns)} boîtes, "
          f"{n_clipped} rognées, classes source: {dict(src_classes)}")


if __name__ == "__main__":
    main()

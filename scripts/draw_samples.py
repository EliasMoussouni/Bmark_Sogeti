#!/usr/bin/env python3
"""Dessine les boîtes d'un jeu COCO sur un échantillon d'images et exporte en PNG pour inspection visuelle.

Usage : python scripts/draw_samples.py --coco data/x/coco_objet.json --images data/x/images --out figures/samples_x --n 20 [--seed 0] [--max-side 2000] [--only-annotated]
Le nom de fichier de sortie reprend le nom source ; une légende indique le nombre de boîtes et la taille relative médiane.
"""
import argparse
import json
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coco", required=True)
    ap.add_argument("--images", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-side", type=int, default=2000)
    ap.add_argument("--only-annotated", action="store_true")
    ap.add_argument("--crop-around-boxes", type=int, default=0,
                    help="si >0, exporte en plus un zoom (fenêtre carrée de cette taille en px) autour de la 1re boîte")
    a = ap.parse_args()
    random.seed(a.seed)
    os.makedirs(a.out, exist_ok=True)
    d = json.load(open(a.coco))
    by_img = {}
    for an in d["annotations"]:
        by_img.setdefault(an["image_id"], []).append(an["bbox"])
    imgs = [im for im in d["images"] if os.path.exists(os.path.join(a.images, im["file_name"]))]
    if a.only_annotated:
        imgs = [im for im in imgs if by_img.get(im["id"])]
    random.shuffle(imgs)
    imgs = imgs[: a.n]
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    for im in imgs:
        p = os.path.join(a.images, im["file_name"])
        img = Image.open(p).convert("RGB")
        W, H = img.size
        boxes = by_img.get(im["id"], [])
        scale = min(1.0, a.max_side / max(W, H))
        if scale < 1:
            img = img.resize((int(W * scale), int(H * scale)))
        dr = ImageDraw.Draw(img)
        lw = max(2, int(3 * scale * max(W, H) / 1500))
        for (x, y, w, h) in boxes:
            x0, y0, x1, y1 = x * scale, y * scale, (x + w) * scale, (y + h) * scale
            dr.rectangle([x0, y0, x1, y1], outline=(255, 40, 40), width=lw)
        rel = [100 * (b[2] * b[3]) / (W * H) for b in boxes]
        txt = f"{os.path.basename(im['file_name'])}  {W}x{H}  boîtes={len(boxes)}  aire rel. médiane={np.median(rel):.3f}%" if rel else \
              f"{os.path.basename(im['file_name'])}  {W}x{H}  boîtes=0"
        dr.rectangle([0, 0, min(img.size[0], 12 + 11 * len(txt)), 30], fill=(0, 0, 0))
        dr.text((6, 4), txt, fill=(255, 255, 255), font=font)
        base = os.path.splitext(os.path.basename(im["file_name"]))[0]
        img.save(os.path.join(a.out, f"{base}_boxes.png"))
        if a.crop_around_boxes and boxes:
            x, y, w, h = boxes[0]
            cx, cy, s = x + w / 2, y + h / 2, a.crop_around_boxes
            full = Image.open(p).convert("RGB")
            crop = full.crop((int(cx - s / 2), int(cy - s / 2), int(cx + s / 2), int(cy + s / 2)))
            dc = ImageDraw.Draw(crop)
            for (bx, by, bw, bh) in boxes:
                dc.rectangle([bx - (cx - s / 2), by - (cy - s / 2), bx + bw - (cx - s / 2), by + bh - (cy - s / 2)], outline=(255, 40, 40), width=2)
            crop.save(os.path.join(a.out, f"{base}_zoom{s}.png"))
    print(f"{len(imgs)} images exportées dans {a.out}")


if __name__ == "__main__":
    main()

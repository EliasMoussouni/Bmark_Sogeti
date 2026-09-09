#!/usr/bin/env python3
"""Compare les conventions d'annotation entre domaines à partir des audits produits par audit_dataset.py.

Entrée : un ou plusieurs dossiers d'audit (contenant boxes.csv, per_image.csv, summary.json).
Sorties (dans --out) :
  comparison_table.csv / comparison_table.md : percentiles des tailles relatives, densité, aspect, par jeu
  domain_table.md                            : mêmes statistiques agrégées par domaine
  figures : hist_rel_area_by_domain.png, hist_rel_side_by_domain.png, hist_objects_per_image_by_domain.png,
            hist_aspect_by_domain.png, cdf_rel_side_by_dataset.png
  ks_tests.json : tests de Kolmogorov-Smirnov deux-échantillons entre paires de jeux (taille relative)

Usage : python scripts/compare_conventions.py --audits audits/* --out figures
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PCTS = [5, 25, 50, 75, 95]
DOMAIN_COLORS = {"sous-marin": "#1f77b4", "aerien": "#d62728", "satellite": "#9467bd", "aerien_non_marin": "#ff7f0e"}


def pct_row(a):
    a = np.asarray(a, dtype=float)
    a = a[~np.isnan(a)]
    if a.size == 0:
        return {f"p{p}": np.nan for p in PCTS} | {"mean": np.nan, "n": 0}
    return {f"p{p}": np.percentile(a, p) for p in PCTS} | {"mean": a.mean(), "n": int(a.size)}


def ks_2samp(a, b):
    """KS deux-échantillons sans scipy : statistique D et p-value asymptotique."""
    a, b = np.sort(a), np.sort(b)
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return np.nan, np.nan
    allv = np.concatenate([a, b])
    ca = np.searchsorted(a, allv, side="right") / n
    cb = np.searchsorted(b, allv, side="right") / m
    d = float(np.max(np.abs(ca - cb)))
    en = np.sqrt(n * m / (n + m))
    lam = (en + 0.12 + 0.11 / en) * d
    p = 2 * sum((-1) ** (k - 1) * np.exp(-2 * (k * lam) ** 2) for k in range(1, 101))
    return d, float(min(max(p, 0.0), 1.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audits", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-boxes-per-dataset", type=int, default=200000, help="sous-échantillonnage pour les figures")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    boxes, imgs, summaries = [], [], {}
    for d in args.audits:
        sp = os.path.join(d, "summary.json")
        if not os.path.exists(sp):
            continue
        s = json.load(open(sp))
        summaries[s["name"]] = s
        b = pd.read_csv(os.path.join(d, "boxes.csv")) if os.path.getsize(os.path.join(d, "boxes.csv")) > 0 else pd.DataFrame()
        if len(b) > args.max_boxes_per_dataset:
            b = b.sample(args.max_boxes_per_dataset, random_state=0)
        boxes.append(b)
        imgs.append(pd.read_csv(os.path.join(d, "per_image.csv")))
    B = pd.concat(boxes, ignore_index=True)
    I = pd.concat(imgs, ignore_index=True)
    B = B[(B["degenerate"] == 0) & B["rel_area_pct"].notna()].copy()
    B["rel_side_pct"] = 100 * np.sqrt(B["rel_area_pct"] / 100)
    B["log_aspect"] = np.log2(B["aspect_w_over_h"].astype(float))

    # --- table par jeu
    rows = []
    for name, s in summaries.items():
        b = B[B["dataset"] == name]
        i = I[(I["dataset"] == name) & (I["has_label_file"] == 1)]
        r = {"dataset": name, "domain": s["domain"], "n_images": s["n_images_on_disk"] or s["n_images_in_annotations"],
             "n_images_annotated": s["n_images_in_annotations"], "n_boxes": s["n_objects"],
             "pct_images_empty": 100 * s["n_images_with_zero_objects"] / max(1, s["n_images_in_annotations"])}
        for k, v in pct_row(b["rel_area_pct"]).items():
            r[f"rel_area_pct_{k}"] = v
        for k, v in pct_row(b["rel_side_pct"]).items():
            r[f"rel_side_pct_{k}"] = v
        for k, v in pct_row(b["w"] * 0 + np.sqrt(b["area_px"])).items():
            r[f"side_px_{k}"] = v
        for k, v in pct_row(i["n_objects"]).items():
            r[f"obj_per_img_{k}"] = v
        for k, v in pct_row(b["aspect_w_over_h"]).items():
            r[f"aspect_{k}"] = v
        r["aspect_frac_elongated_>2"] = 100 * np.mean((b["aspect_w_over_h"] > 2) | (b["aspect_w_over_h"] < 0.5)) if len(b) else np.nan
        r["coco_small_pct"] = s["coco_size_buckets_pct"]["small_<32px2"]
        r["coco_large_pct"] = s["coco_size_buckets_pct"]["large_>=96px2"]
        rows.append(r)
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(args.out, "comparison_table.csv"), index=False)
    cols = ["dataset", "domain", "n_images", "n_boxes", "pct_images_empty", "rel_area_pct_p5", "rel_area_pct_p25", "rel_area_pct_p50",
            "rel_area_pct_p75", "rel_area_pct_p95", "rel_side_pct_p50", "side_px_p50", "obj_per_img_p50", "obj_per_img_p95",
            "obj_per_img_mean", "aspect_p50", "aspect_frac_elongated_>2", "coco_small_pct", "coco_large_pct"]
    with open(os.path.join(args.out, "comparison_table.md"), "w") as f:
        f.write(T[cols].to_markdown(index=False, floatfmt=".3g"))

    # --- table par domaine
    drows = []
    for dom, b in B.groupby("domain"):
        i = I[(I["domain"] == dom) & (I["has_label_file"] == 1)]
        r = {"domain": dom, "n_datasets": b["dataset"].nunique(), "n_boxes": len(b)}
        for k, v in pct_row(b["rel_area_pct"]).items():
            r[f"rel_area_pct_{k}"] = v
        for k, v in pct_row(b["rel_side_pct"]).items():
            r[f"rel_side_pct_{k}"] = v
        for k, v in pct_row(i["n_objects"]).items():
            r[f"obj_per_img_{k}"] = v
        for k, v in pct_row(b["aspect_w_over_h"]).items():
            r[f"aspect_{k}"] = v
        drows.append(r)
    D = pd.DataFrame(drows)
    with open(os.path.join(args.out, "domain_table.md"), "w") as f:
        f.write(D.to_markdown(index=False, floatfmt=".3g"))

    # --- KS entre jeux (taille relative du côté)
    names = list(summaries)
    ks = {}
    for i, a in enumerate(names):
        for bname in names[i + 1:]:
            x = B[B["dataset"] == a]["rel_side_pct"].values
            y = B[B["dataset"] == bname]["rel_side_pct"].values
            dstat, p = ks_2samp(x, y)
            ks[f"{a} vs {bname}"] = {"D": dstat, "p": p, "n_a": len(x), "n_b": len(y)}
    json.dump(ks, open(os.path.join(args.out, "ks_tests.json"), "w"), indent=2)

    # --- figures
    def hist_by(col, fname, xlabel, bins, log=False, by="domain"):
        fig, ax = plt.subplots(figsize=(9, 5))
        for key, g in B.groupby(by):
            v = g[col].dropna().values
            if len(v) == 0:
                continue
            color = DOMAIN_COLORS.get(key) if by == "domain" else None
            ax.hist(v, bins=bins, density=True, histtype="step", linewidth=2, label=f"{key} (n={len(v)})", color=color)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("densité")
        if log:
            ax.set_xscale("log")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(args.out, fname), dpi=130)
        plt.close(fig)

    hist_by("rel_area_pct", "hist_rel_area_by_domain.png", "aire de la boîte en % de l'aire image (échelle log)", np.logspace(-4, 2, 60), log=True)
    hist_by("rel_side_pct", "hist_rel_side_by_domain.png", "côté équivalent de la boîte en % du côté image (sqrt aire relative, log)", np.logspace(-2, 2, 60), log=True)
    hist_by("log_aspect", "hist_aspect_by_domain.png", "log2(largeur/hauteur) de la boîte", np.linspace(-4, 4, 60))

    fig, ax = plt.subplots(figsize=(9, 5))
    for dom, g in I[I["has_label_file"] == 1].groupby("domain"):
        v = g["n_objects"].values
        ax.hist(np.clip(v, 0, 60), bins=np.arange(0, 62) - 0.5, density=True, histtype="step", linewidth=2,
                label=f"{dom} (n={len(v)} images)", color=DOMAIN_COLORS.get(dom))
    ax.set_xlabel("objets par image (tronqué à 60)")
    ax.set_ylabel("fraction d'images")
    ax.set_yscale("log")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "hist_objects_per_image_by_domain.png"), dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    for name, g in B.groupby("dataset"):
        v = np.sort(g["rel_side_pct"].values)
        ax.plot(v, np.arange(1, len(v) + 1) / len(v), label=f"{name} [{g['domain'].iloc[0]}] n={len(v)}",
                color=DOMAIN_COLORS.get(g["domain"].iloc[0]), alpha=0.8, linestyle=["-", "--", ":", "-."][hash(name) % 4])
    ax.set_xscale("log")
    ax.set_xlabel("côté équivalent de la boîte en % du côté image (log)")
    ax.set_ylabel("CDF")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "cdf_rel_side_by_dataset.png"), dpi=130)
    plt.close(fig)
    print(T[cols].to_string(index=False))
    print("\nKS (rel_side_pct):")
    for k, v in ks.items():
        print(f"  {k}: D={v['D']:.3f} p={v['p']:.2g}")


if __name__ == "__main__":
    main()

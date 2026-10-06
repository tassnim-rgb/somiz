"""Extract building outline + label clusters from the four SOMIZ plan scans.

Output per plan: JSON with
  image size, building bbox (px), scale guess, zone labels (with S= area),
  machine labels (grouped multi-line) with centroid px.

Position on plan -> text is OCR from ocr_<name>_tiles.json.
"""
import json
import os

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PLANS = {
    "dis": "raw_dis-001-000.jpg",
    "dlog": "raw_dlog-001-000.jpg",
    "dca": "raw_dca-001-000.jpg",
    "centrale": "raw_centrale-001-000.jpg",
}

# title block + borders live in the bottom-right / outer frame: exclude them
TITLE_FRAC = {"dis": (0.55, 0.70), "dlog": (0.55, 0.70), "dca": (0.55, 0.70),
              "centrale": (0.40, 0.24)}


def building_bbox(path):
    """Largest connected dark region excluding the outer sheet border.

    The plans are white sheets with black line work. We binarise, drop the
    sheet frame by cropping 3% margins, then take the largest contour that
    covers a plausible share of the sheet as the building outline.
    """
    img = cv2.imread(path)
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    m = int(0.04 * max(h, w))
    crop = gray[m:h - m, m:w - m]
    _, bw = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # close gaps so wall lines form one connected outline
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, k, iterations=2)
    cnts, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
    best = None
    for c in cnts:
        x, y, bw_, bh = cv2.boundingRect(c)
        area = bw_ * bh
        fill = cv2.contourArea(c) / max(area, 1)
        if area < 0.08 * (w * h):      # too small to be the building
            continue
        if fill < 0.35:                 # too sparse: probably hatching/noise
            continue
        best = (x + m, y + m, bw_, bh, float(fill))
        break
    return (w, h), best


def main():
    report = {}
    for name, fname in PLANS.items():
        path = os.path.join(HERE, fname)
        (W, H), bbox = building_bbox(path)
        items = json.load(open(os.path.join(HERE, f"ocr_{name}_tiles.json")))
        # dedupe: same text within 60 px
        seen, uniq = set(), []
        for it in items:
            x = sum(p[0] for p in it["box"]) / 4
            y = sum(p[1] for p in it["box"]) / 4
            key = (it["text"].strip().lower(), round(x / 70), round(y / 70))
            if key in seen:
                continue
            seen.add(key)
            uniq.append({"x": round(x), "y": round(y), "t": it["text"].strip(),
                         "s": round(it["score"], 2)})
        tx0, ty0 = TITLE_FRAC[name]
        title = [u for u in uniq if u["x"] > tx0 * W and u["y"] > ty0 * H]
        body = [u for u in uniq if u not in title]
        report[name] = {"sheet": [W, H], "building_bbox_px": bbox,
                        "title_block": sorted(title, key=lambda u: (u["y"], u["x"])),
                        "labels": sorted(body, key=lambda u: (u["y"], u["x"]))}
        print(f"== {name}: sheet={W}x{H} bbox={bbox}")
    with open(os.path.join(HERE, "plan_extract.json"), "w") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print("wrote plan_extract.json")


if __name__ == "__main__":
    main()

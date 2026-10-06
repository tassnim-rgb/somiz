"""OCR the four SOMIZ atelier plan scans (full-page pass) -> JSON per plan.

Usage: python ocr_all.py [--tiles]
Full-page pass captures large text (zone names, title block); the --tiles pass
re-OCRs 2x2 overlapping crops at native resolution to catch small equipment tags.
"""
import json
import os
import sys

from PIL import Image
from rapidocr_onnxruntime import RapidOCR

HERE = os.path.dirname(os.path.abspath(__file__))
PLANS = {
    "dis": "raw_dis-001-000.jpg",
    "dlog": "raw_dlog-001-000.jpg",
    "dca": "raw_dca-001-000.jpg",
    "centrale": "raw_centrale-001-000.jpg",
}


def run(ocr, path, crop=None, offset=(0, 0)):
    img = Image.open(path)
    if crop:
        img = img.crop(crop)
    tmp = os.path.join(HERE, "_tmp_tile.png")
    img.save(tmp)
    res, _ = ocr(tmp)
    out = []
    for box, txt, score in res or []:
        pts = [[p[0] + offset[0], p[1] + offset[1]] for p in box]
        out.append({"box": pts, "text": txt, "score": float(score)})
    return out


def main():
    tiles = "--tiles" in sys.argv
    ocr = RapidOCR()
    for name, fname in PLANS.items():
        path = os.path.join(HERE, fname)
        items = run(ocr, path)
        if tiles:
            w, h = Image.open(path).size
            for xi in range(2):
                for yi in range(2):
                    # 60% overlap so nothing is cut mid-word
                    x0 = int(xi * w * 0.4)
                    y0 = int(yi * h * 0.4)
                    x1 = int(min(w, x0 + w * 0.6))
                    y1 = int(min(h, y0 + h * 0.6))
                    items += run(ocr, path, crop=(x0, y0, x1, y1), offset=(x0, y0))
        out = os.path.join(HERE, f"ocr_{name}{'_tiles' if tiles else ''}.json")
        with open(out, "w") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=1)
        print(name, len(items), "->", os.path.basename(out), flush=True)


if __name__ == "__main__":
    main()

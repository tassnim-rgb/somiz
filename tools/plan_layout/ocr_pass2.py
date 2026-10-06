"""Second OCR pass: margin strips (to catch overall dimension lines) and
2x-upscaled crops of garbled labels."""
import json
import os

from PIL import Image
from rapidocr_onnxruntime import RapidOCR

HERE = os.path.dirname(os.path.abspath(__file__))
PLANS = {"dis": "raw_dis-001-000.jpg", "dlog": "raw_dlog-001-000.jpg",
         "dca": "raw_dca-001-000.jpg", "centrale": "raw_centrale-001-000.jpg"}

# margin strips as fractions (x0,y0,x1,y1) of the sheet
STRIPS = {
    "dis": [(0.0, 0.58, 1.0, 0.78), (0.0, 0.0, 1.0, 0.07)],
    "dlog": [(0.0, 0.68, 1.0, 0.88), (0.0, 0.0, 1.0, 0.07)],
    "dca": [(0.0, 0.82, 1.0, 1.0), (0.0, 0.0, 1.0, 0.07)],
    "centrale": [(0.0, 0.90, 1.0, 1.0), (0.66, 0.17, 1.0, 0.95)],
}

# garbled / uncertain labels: (name, x0, y0, x1, y1) in px
ZOOM = {
    "centrale": [(700, 2650, 1300, 2900), (2600, 2900, 3300, 3150),
                 (300, 3750, 900, 4000), (2300, 2400, 3200, 3300)],
    "dlog": [(2400, 750, 3400, 1120)],
    "dis": [(600, 980, 1000, 1080)],
    "dca": [(1200, 2550, 1700, 2750)],
}


def ocr_crop(ocr, path, box=None, scale=1):
    img = Image.open(path)
    if box:
        img = img.crop(box)
    if scale != 1:
        img = img.resize((int(img.width * scale), int(img.height * scale)),
                         Image.LANCZOS)
    tmp = os.path.join(HERE, "_z.png")
    img.save(tmp)
    res, _ = ocr(tmp)
    ox, oy = (box[0], box[1]) if box else (0, 0)
    out = []
    for b, t, s in res or []:
        cx = sum(p[0] for p in b) / 4 / scale + ox
        cy = sum(p[1] for p in b) / 4 / scale + oy
        out.append((round(cy), round(cx), " ".join(t.split()), round(float(s), 2)))
    return sorted(out)


def main():
    ocr = RapidOCR()
    allout = {}
    for name, fname in PLANS.items():
        path = os.path.join(HERE, fname)
        W, H = Image.open(path).size
        recs = []
        for (a, b, c, d) in STRIPS[name]:
            recs += ocr_crop(ocr, path, (int(a * W), int(b * H),
                                         int(c * W), int(d * H)))
        for box in ZOOM.get(name, []):
            recs += ocr_crop(ocr, path, box, scale=2)
        allout[name] = recs
        print(f"== {name}")
        for y, x, t, s in recs:
            print(f"   {y:5d} {x:5d} {s:.2f}  {t}")
    with open(os.path.join(HERE, "ocr_pass2.json"), "w") as fh:
        json.dump(allout, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

"""Build the SOMIZ ATELIERS data (zones + machines) from the OCR of the plans.

Source: scanned "PLAN D'IMPLANTATION DES MACHINES ET EQUIPEMENTS" drawings
(SOCIETE DE MAINTENANCE INDUSTRIELLE ARZEW / SOMIZ):
  DIS, DLOG, DCA : Plan No P-01, ind. 01, 12/05/2024
  Centrale       : Plan No P-01, ind. 01, 01/04/2024

Machine and zone labels come from the scans (labels_<plan>.txt); px -> m uses a
per-plan calibration (DIS: overall dimension 91,41 m printed on the plan;
others: estimated from the S= surfaces printed on the plan, because no overall
dimension is legible on the scan).  Everything health-related stays SIMULATED.

Outputs: ateliers_snippet.js + layout_summary.txt + layout_data.json
"""
import difflib
import json
import os
import random
import re
import unicodedata
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# Per-plan calibration: px rect of the building outline + resulting metres
# ─────────────────────────────────────────────────────────────────────────────
PLANS = {
    "dis": dict(
        prefix="DIS", label="Atelier DIS",
        x0=490, y0=200, x1=3820, y1=2180, scale=0.02745,   # 91,41 m cote plan
        area_note="4 133 m²", surface="4 133 m²",
    ),
    "dlog": dict(
        prefix="DLG", label="Atelier DLOG",
        x0=300, y0=300, x1=3620, y1=3100, scale=0.0190,    # estimé (surfaces S=)
        area_note="2 253 m²", surface="2 253 m²",
    ),
    "dca": dict(
        prefix="DCA", label="Atelier DCA",
        x0=260, y0=110, x1=2820, y1=3400, scale=0.0204,    # estimé (surfaces S=)
        area_note="2 937 m²", surface="2 937 m²",
    ),
    "centrale": dict(
        prefix="CEN", label="Atelier Centrale",
        x0=250, y0=1080, x1=3250, y1=4700, scale=0.0220,   # estimé (pas des locaux)
        area_note="Multi-zones", surface="Multi-zones",
    ),
}
ORDER = ["dis", "dlog", "centrale", "dca"]

# machine archetype footprints (m) + archetypes already used by the viewer
FOOT = {
    "lathe": (5.0, 3.0), "mill": (4.0, 3.5), "saw": (3.5, 4.0),
    "press": (4.0, 4.0), "compressor": (3.0, 3.0), "oven": (4.0, 4.0),
    "drill": (3.0, 3.0), "vent": (3.0, 3.0), "generic": (4.0, 3.0),
}

# ─────────────────────────────────────────────────────────────────────────────
# Machine vocabulary.  key   = regex used to ANCHOR a label (first-word style)
#                 anchor = regex used to pick the variant among entries that
#                          share a key (matched against the joined group text)
# first match wins on ties, so plain/default entries come first per key group
# ─────────────────────────────────────────────────────────────────────────────
def M(key, anchor, name, mtype, typ):
    return dict(key=re.compile(key, re.I), anchor=re.compile(anchor, re.I),
                name=name, mtype=mtype, typ=typ)


MACHINES = {
    "dis": [
        M(r"guilotine|guillotine", r"guilotine\s+manuel|guillotine\s+manuel",
          "Guillotine Manuel", "press", "Découpe"),
        M(r"guilotine|guillotine", r"guilotine|guillotine",
          "Guillotine Électrique", "press", "Découpe"),
        M(r"machine\s+wintech", r"machine\s+wintech",
          "Machine Wintech Découpage Polyuréthane", "mill", "Découpe mousse"),
        M(r"extracteur", r"extracteur", "Extracteur d'Air", "vent", "Ventilation"),
        M(r"cintreuse", r"cintreuse", "Cintreuse Rouleuse de Tôle", "mill", "Formage métal"),
        M(r"bordeuse", r"bordeuse", "Bordeuse Tôle", "generic", "Formage métal"),
        M(r"rouleuse", r"rouleuse", "Rouleuse de Tôle", "mill", "Formage métal"),
        M(r"graveuse", r"graveuse", "Graveuse", "drill", "Gravure"),
        M(r"scie", r"scie", "Scie à Ruban Électrique", "saw", "Découpe"),
        M(r"meuleuse", r"meuleuse", "Meuleuse", "mill", "Ébavurage"),
        M(r"plyeuse|plieuse", r"plyeuse|plieuse", "Plyeuse Tôle", "press", "Pliage"),
        M(r"coupe", r"coupe", "Coupe Cercle", "drill", "Découpe"),
    ],
    "dlog": [
        M(r"presse\s+etoupe", r"presse\s+etoupe", "Presse Étoupe", "press", "Pressage"),
        M(r"panneaux\s+de\s+levage", r"panneaux\s+de\s+levage\s+electrique",
          "Panneaux de Levage Électrique", "generic", "Manutention"),
        M(r"panneaux\s+de\s+levage", r"panneaux\s+de\s+levage",
          "Panneaux de Levage", "generic", "Manutention"),
        M(r"outil\s+de\s+pon", r"outil\s+de\s+pon",
          "Outil de Ponçage et Meulage Électrique", "drill", "Ponçage / meulage"),
        M(r"compresseur", r"compresseur", "Compresseur d'Air", "compressor", "Air comprimé"),
        M(r"presse\s+electrique", r"presse\s+electrique", "Presse Électrique", "press", "Pressage"),
    ],
    "dca": [
        M(r"tronc?g?onneuse|trongonneuse", r"tronc?g?onneuse|trongonneuse",
          "Tronçonneuse", "saw", "Découpe"),
        M(r"perceuse", r"perceuse", "Perceuse Sur-Bâtis", "drill", "Perçage"),
        M(r"limeuse", r"limeuse", "Limeuse à Roche", "generic", "Limage"),
        M(r"guilotine|guillotine", r"guilotine|guillotine",
          "Guillotine Électrique", "press", "Découpe"),
        M(r"rouleuse", r"rouleuse", "Rouleuse", "mill", "Formage métal"),
        M(r"plyeuse|plieuse", r"plyeuse|plieuse", "Plyeuse", "press", "Pliage"),
    ],
    "centrale": [
        M(r"tours?\s+pour\s+bobinage|^tours$", r"tours\s+pour\s+bobinage",
          "Tours pour Bobinage (Bobineuses)", "lathe", "Bobinage"),
        M(r"tour\s*en\s*l'air|tourenl", r"tour\s*en\s*l'air|tourenl",
          "Tour en L'Air", "lathe", "Tournage"),
        M(r"tour\s*parallele|^tour$", r"tour\s*parallele|^tour$",
          "Tour Parallèle", "lathe", "Tournage"),
        M(r"fraiseuse", r"fraiseuse\s+(a|i)\s+montant",
          "Fraiseuse à Montant Mobile", "mill", "Fraisage"),
        M(r"fraiseuse", r"fraiseuse\s+universelle",
          "Fraiseuse Universelle", "mill", "Fraisage"),
        M(r"fraiseuse", r"fraiseuse", "Fraiseuse", "mill", "Fraisage"),
        M(r"rectifi", r"rectifieuse\s+cylindrique",
          "Rectifieuse Cylindrique", "mill", "Rectification"),
        M(r"rectifi", r"rectifi?figuse\s+plane|rectifieuse\s+plane|rectifiuse\s+plane",
          "Rectifieuse Plane", "mill", "Rectification"),
        M(r"rectifi", r"rectifi", "Rectifieuse", "mill", "Rectification"),
        M(r"aleseuse", r"aleseuse", "Aléseuse Horizontale", "mill", "Alésage"),
        M(r"mortaiseuse", r"mortaiseuse", "Mortaiseuse", "mill", "Mortaisage"),
        M(r"etau", r"etau", "Etau-Limeur", "mill", "Limage"),
        M(r"equilibreuse", r"equilibreuse", "Équilibreuse", "generic", "Équilibrage"),
        M(r"perceuse", r"perceuse\s+radiale", "Perceuse Radiale", "drill", "Perçage"),
        M(r"perceuse", r"perceuse\s+electri", "Perceuse Électrique", "drill", "Perçage"),
        M(r"perceuse", r"perceuse", "Perceuse", "drill", "Perçage"),
        M(r"scie", r"scie\s+me?ca?nique", "Scie Mécanique", "saw", "Découpe"),
        M(r"scie", r"scie\s+a\s+ruban", "Scie à Ruban", "saw", "Découpe"),
        M(r"scie", r"scie", "Scie", "saw", "Découpe"),
        M(r"cisaille", r"cisaille", "Cisaille Papier Isolant", "saw", "Découpe"),
        M(r"coupeuse", r"coupeuse", "Coupeuse Bois", "saw", "Découpe bois"),
        M(r"ponceuse", r"ponceuse", "Ponceuse pour Bois", "generic", "Ponçage"),
        M(r"^meule$|meule\s+pour", r"meule\s+pour",
          "Meule pour Bobine Moteur", "generic", "Meulage"),
        M(r"meuleuse", r"meuleuse", "Meuleuse", "mill", "Meulage"),
        M(r"sableuse", r"sableuse", "Sableuse Pièces Métalliques", "generic", "Sablage"),
        M(r"brosses", r"brosses", "Brosses Métalliques Électriques", "generic", "Décaper"),
        M(r"cabine", r"cabine", "Cabine d'Évacuation gaz", "vent", "Extraction gaz"),
        M(r"four", r"four\s+electrique", "Four Électrique", "oven", "Traitement thermique"),
        M(r"presse\s+hydraulique", r"presse\s+hydraulique",
          "Presse Hydraulique", "press", "Pressage"),
        M(r"presse\s+electrique", r"presse\s+electrique",
          "Presse Électrique", "press", "Pressage"),
        M(r"la\s+presse", r"la\s+presse", "La Presse", "press", "Pressage"),
        M(r"la\s+rodeuse", r"la\s+rodeuse", "La Rodeuse", "generic", "Formage"),
        M(r"rodeuse", r"rodeuse\s+electrique", "Rodeuse Électrique",
          "generic", "Formage"),
        M(r"rodeuse", r"rodeuse", "Rodeuse", "generic", "Formage"),
        M(r"banc", r"banc", "Banc d'essai", "generic", "Essais"),
        M(r"compresseur", r"compresseur", "Compresseur", "compressor", "Air comprimé"),
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Zones: explicit hall rectangles (px) + room zones anchored on their label
# ─────────────────────────────────────────────────────────────────────────────
ZONES = {
    "dis": dict(
        hall=[
            ("Zone Production", "S = 4 133,39 m²", (1040, 780, 3560, 2180)),
            ("Zone de Stockage Polyuréthane", "1 106 m³", (3570, 850, 3840, 1750)),
        ],
        room=[
            ("Réfectoire", "S = 43,39 m²", (1628, 652), 6.6),
            ("Hall", "S = 40,95 m²", (1450, 543), 6.4),
            ("Ingénieurs", "S = 31,14 m²", (732, 423), 5.6),
            ("Magasin", "S = 22,36 m²", (716, 1012), 4.7),
            ("Moussala", "S = 21,18 m²", (716, 852), 4.6),
            ("Batis", "S = 394 m²", (976, 783), 19.9),
        ],
    ),
    "dlog": dict(
        hall=[
            ("Zone Production", "S = 2 252,95 m²", (300, 300, 3620, 1240)),
            ("Zone Production", "S = 2 252,95 m²", (1100, 1250, 2450, 3100)),
        ],
        room=[
            ("Elec. Poste", None, (523, 1260), 6.0),
            ("Directeur DSL", "S = 23,10 m²", (324, 1470), 4.8),
            ("Secrétariat DLOG", "S = 21,94 m²", (341, 1704), 4.7),
            ("Sanitaires", "S = 23,40 m²", (328, 2151), 4.8),
            ("Hall", "S = 17,32 m²", (568, 2153), 4.2),
            ("Magasin", "S = 23,40 m²", (902, 2152), 4.8),
            ("Magasin", "S = 55,72 m²", (902, 2480), 7.5),
            ("Sanitaires", "S = 109 m²", (2536, 2733), 10.4),
            ("Vestiaires", "S = 90,23 m²", (2732, 2080), 9.5),
            ("Peinture & Tôlerie", "S = 188,72 m²", (3240, 1780), 13.7),
        ],
    ),
    "dca": dict(
        hall=[("Atelier Chaudronnerie", "S = 2 937,31 m²", (260, 760, 2820, 2940))],
        room=[
            ("Sanitaires", "S = 28,38 m²", (562, 3124), 5.3),
            ("Vestiaires", "S = 46,88 m²", (915, 3122), 6.85),
            ("Magasin", "S = 142,25 m²", (2577, 466), 11.9),
        ],
    ),
    "centrale": dict(
        hall=[
            ("Atelier Fabrication Mécanique", "Sections : Tournage, Équilibrage, Fraisage",
             (1000, 1900, 2300, 4350)),
            ("Atelier Turbo Machine", None, (2462, 1382, 3098, 2018)),
            ("Atelier Bobinage", None, (2450, 2950, 3250, 3750)),
            ("Atelier DEI", None, (2450, 3760, 3250, 4450)),
        ],
        room=[
            ("Instrumentation", None, (528, 1554), 9.0),
            ("Atelier Traitement Thermique", None, (447, 2728), 10.0),
            ("Magasin", None, (293, 3760), 8.0),
            ("Atelier Vannes & Soupapes", None, (412, 4070), 9.0),
            ("Compresseurs", None, (330, 4330), 8.0),
            ("Douche", None, (2376, 2549), 6.0),
        ],
    ),
}

# labels that are never machines (stamps, doors, notes, junk, titles, zone words)
DROP = re.compile(
    r"("
    r"^acc[ée]s$|^projects$|^man$|^epm\.?$|^on$|^196'$|^ouchd$|^mor$|^ele$|^sc$|^ri[eé]$|"
    r"^nb\s*:.*|^importants des compresseur.*|^electrogenes et postes.*|"
    r"^rentres a l.*|^atelier de maintenance$|^materiels et equipment$|"
    r"^f2819p$|^28\.1:9p$|^metalliqu.*|^0\.35.*|^eectrique.*|"
    r"^compresseurs$|"                       # centrale zone title, not a machine
    r"[-']t9gso"
    r")", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def load_labels(name):
    rows = []
    for line in open(os.path.join(HERE, f"labels_{name}.txt")):
        parts = line.strip().split(None, 3)
        y, x, score, text = int(parts[0]), int(parts[1]), float(parts[2]), parts[3]
        rows.append(dict(x=x, y=y, t=" ".join(text.split()), s=score))
    return rows


def nospace(t):
    return norm(t).replace(" ", "")


def dedupe(rows):
    """Collapse repeated readings of the same label (tiles overlap and the OCR
    reads the same text twice with slight spelling/spacing variations)."""
    out = []
    for r in sorted(rows, key=lambda r: -r["s"]):
        keep = True
        for o in out:
            if abs(o["x"] - r["x"]) >= 130 or abs(o["y"] - r["y"]) >= 70:
                continue
            a, b = nospace(o["t"]), nospace(r["t"])
            if a == b or a in b or b in a:
                keep = False
                break
            if abs(o["x"] - r["x"]) <= 60 and abs(o["y"] - r["y"]) <= 40:
                # same spot: near-identical reading (rectifiguse/rectifiuse…)
                if difflib.SequenceMatcher(None, a, b).ratio() >= 0.6:
                    keep = False
                    break
        if keep:
            out.append(r)
    out.sort(key=lambda r: (r["y"], r["x"]))
    return out


def is_noise(t):
    n = norm(t)
    if DROP.search(n):
        return True
    if re.match(r"^s\s*=", n):
        return True                      # surface annotations belong to zones
    if not re.search(r"[a-z']", n):
        return True                      # bare dimensions / numbers
    return False


def build_machines(name, labels, cfg, debug):
    spec, prefix = MACHINES[name], cfg["prefix"]
    s, x0, y0 = cfg["scale"], cfg["x0"], cfg["y0"]
    labels = [l for l in labels if not is_noise(l["t"])]

    # 1. block clustering: union labels in the same column (dx<=90, dy<=50) so
    #    multi-line names ("Presse" / "Electrique") become one text block
    parent = list(range(len(labels)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def uni(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            if (abs(labels[i]["x"] - labels[j]["x"]) <= 90 and
                    abs(labels[i]["y"] - labels[j]["y"]) <= 50):
                uni(i, j)
    blocks = {}
    for i, lab in enumerate(labels):
        blocks.setdefault(find(i), []).append(lab)

    machines = []
    for members in blocks.values():
        members.sort(key=lambda l: (l["y"], l["x"]))
        joined = norm(" ".join(m["t"] for m in members))
        if not re.search(r"[a-z']", joined):
            continue
        # pick the spec entry: full pattern first (longest match), else key
        best_i, best_len = None, -1
        for stage in ("anchor", "key"):
            for i, m in enumerate(spec):
                mo = m[stage].search(joined)
                if mo and len(mo.group(0)) > best_len:
                    best_i, best_len = i, len(mo.group(0))
            if best_i is not None:
                break
        if best_i is None:
            continue
        m = spec[best_i]
        cx = sum(mb["x"] for mb in members) / len(members)
        cy = sum(mb["y"] for mb in members) / len(members)
        w, d = FOOT[m["mtype"]]
        machines.append(dict(
            name=m["name"], mtype=m["mtype"], typ=m["typ"],
            x=round((cx - x0) * s - w / 2, 2), z=round((cy - y0) * s - d / 2, 2),
            w=w, d=d, src=joined[:60],
        ))

    machines.sort(key=lambda e: (e["z"], e["x"]))
    for i, e in enumerate(machines, 1):
        e["id"] = f"{prefix}-{i:02d}"
    resolve_overlaps(machines, cfg)

    # debug: word-labels that never became part of a machine block
    consumed = set()
    for members in blocks.values():
        joined = norm(" ".join(m["t"] for m in members))
        for i, m in enumerate(spec):
            if m["anchor"].search(joined) or m["key"].search(joined):
                consumed.update(id(x) for x in members)
                break
    debug.append(f"-- {prefix} unused word-labels:")
    for l in labels:
        if id(l) not in consumed and re.search(r"[a-z']", norm(l["t"])):
            debug.append(f"     ({l['y']},{l['x']}) {l['t']}")
    return machines


def overlaps(a, b, margin=0.4):
    return (a["x"] < b["x"] + b["w"] + margin and b["x"] < a["x"] + a["w"] + margin and
            a["z"] < b["z"] + b["d"] + margin and b["z"] < a["z"] + a["d"] + margin)


def resolve_overlaps(machines, cfg):
    w_m = (cfg["x1"] - cfg["x0"]) * cfg["scale"]
    d_m = (cfg["y1"] - cfg["y0"]) * cfg["scale"]
    for _ in range(150):
        moved = False
        for i in range(len(machines)):
            for j in range(i + 1, len(machines)):
                a, b = machines[i], machines[j]
                if not overlaps(a, b):
                    continue
                ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
                oz = min(a["z"] + a["d"], b["z"] + b["d"]) - max(a["z"], b["z"])
                if ox < oz:
                    push = ox / 2 + 0.25
                    dirx = 1 if (a["x"] + a["w"] / 2) <= (b["x"] + b["w"] / 2) else -1
                    a["x"] -= dirx * push
                    b["x"] += dirx * push
                else:
                    push = oz / 2 + 0.25
                    dirz = 1 if (a["z"] + a["d"] / 2) <= (b["z"] + b["d"] / 2) else -1
                    a["z"] -= dirz * push
                    b["z"] += dirz * push
                moved = True
        for e in machines:
            e["x"] = max(0.3, min(e["x"], w_m - e["w"] - 0.3))
            e["z"] = max(0.3, min(e["z"], d_m - e["d"] - 0.3))
        if not moved:
            break


def build_zones(name, cfg, debug):
    s, x0, y0 = cfg["scale"], cfg["x0"], cfg["y0"]
    w_m = (cfg["x1"] - x0) * s
    d_m = (cfg["y1"] - y0) * s
    zones, placed = [], []

    def free(rect, gap=0.35):
        return all(not (rect["x"] < p["x"] + p["w"] + gap and p["x"] < rect["x"] + rect["w"] + gap and
                        rect["z"] < p["z"] + p["d"] + gap and p["z"] < rect["z"] + rect["d"] + gap)
                   for p in placed)

    ROOM_COLORS = [0x0b1825, 0x0a1622, 0x0c1d2e]
    room_i = 0
    for zn, area, (px1, py1, px2, py2) in ZONES[name]["hall"]:
        px1, py1 = max(px1, x0), max(py1, y0)
        px2, py2 = min(px2, cfg["x1"]), min(py2, cfg["y1"])   # never overshoot the hall
        rect = dict(x=(px1 - x0) * s, z=(py1 - y0) * s,
                    w=(px2 - px1) * s, d=(py2 - py1) * s)
        placed.append(rect)
        zones.append(dict(name=zn, area=area,
                          x=round(rect["x"], 2), z=round(rect["z"], 2),
                          w=round(rect["w"], 2), d=round(rect["d"], 2),
                          color=0x0c1f30 if rect["w"] * rect["d"] >= 400 else 0x0b1a28))

    # rooms: anchored on the plan label; shrink + grid-search nearest free spot
    for zn, area, (cx, cy), side in ZONES[name]["room"]:
        ax, az = (cx - x0) * s, (cy - y0) * s
        ax = max(0.0, min(ax, w_m))
        az = max(0.0, min(az, d_m))
        found, fallback, fallback_dist = None, None, None
        for k in range(13):                       # scale 1.00 -> 0.40
            sc = 1.0 - 0.05 * k
            half = side * sc / 2
            if half * 2 < 2.0:
                break
            span_x = w_m - 2 * half - 0.4
            span_z = d_m - 2 * half - 0.4
            if span_x <= 0 or span_z <= 0:
                continue
            best, best_dist = None, None
            for ix in range(60):
                rx = 0.2 + span_x * ix / 59
                for iz in range(60):
                    rz = 0.2 + span_z * iz / 59
                    rect = dict(x=rx, z=rz, w=half * 2, d=half * 2)
                    if not free(rect):
                        continue
                    dist = (rx + half - ax) ** 2 + (rz + half - az) ** 2
                    if best_dist is None or dist < best_dist:
                        best, best_dist = rect, dist
            if best is None:
                continue
            # keep the plan size as long as the room stays near its label
            if best_dist <= (max(side * sc, 5.0) * 1.3) ** 2:
                found = best
                break
            if fallback is None or best_dist < fallback_dist:
                fallback, fallback_dist = best, best_dist
        if not found:
            found = fallback
        if not found:
            debug.append(f"!! zone dropped: {name} {zn}")
            continue
        placed.append(found)
        zones.append(dict(name=zn, area=area,
                          x=round(found["x"], 2), z=round(found["z"], 2),
                          w=round(found["w"], 2), d=round(found["d"], 2),
                          color=ROOM_COLORS[room_i % len(ROOM_COLORS)]))
        room_i += 1
    return zones


# ── deterministic SIMULATED condition data ───────────────────────────────────
HIST = {
    "ok": ["Inspection préventive OK", "RAS — relevé conforme", "Graissage effectué",
           "Alignement contrôlé", "Lame vérifiée OK"],
    "warn": ["Vibration anormale détectée", "Disque à 60% d'usure", "Résistance à surveiller",
             "Jeu axial à surveiller", "Température en hausse"],
    "danger": ["Bielle usée", "Fuite hydraulique détectée", "Roulement à remplacer",
               "Surcharge répétée"],
    "critical": ["Surchauffe répétée", "Arrêt d'urgence déclenché", "Panne moteur — blocage"],
}
STATUSES = [("ok", 0.66), ("warn", 0.17), ("danger", 0.10), ("critical", 0.07)]


def simulate(eq):
    rng = random.Random(sum(ord(c) * (i + 3) for i, c in enumerate(eq["id"])) ^ 0x5EED)
    r = rng.random()
    acc, status = 0.0, "ok"
    for st, p in STATUSES:
        acc += p
        if r <= acc:
            status = st
            break
    rc = rng.random()
    if status in ("danger", "critical"):
        crit = "A" if rc < 0.55 else ("B" if rc < 0.9 else "C")
    else:
        crit = "A" if rc < 0.2 else ("B" if rc < 0.58 else "C")
    age = rng.randint(3, 28)
    last = date(2024, 1, 1) + timedelta(days=rng.randint(0, 170))
    nxt = last + timedelta(days=183)
    hist = []
    for k in range(1 if status == "ok" else rng.randint(1, 2)):
        d = last - timedelta(days=180 * (k + 1))
        hist.append(f"{d.isoformat()} — {rng.choice(HIST[status])}")
    eq.update(status=status, crit=crit, age=age,
              last=last.isoformat(), next=nxt.isoformat(), history=list(reversed(hist)))


def js_str(s):
    """single-quoted JS string literal (escape quotes/backslashes)"""
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def emit():
    out, summary, debug = {}, [], []
    for name in ORDER:
        cfg = PLANS[name]
        labels = dedupe(load_labels(name))
        machines = build_machines(name, labels, cfg, debug)
        zones = build_zones(name, cfg, debug)
        for eq in machines:
            eq["x"], eq["z"] = round(eq["x"], 2), round(eq["z"], 2)
            simulate(eq)
        out[name] = dict(cfg=cfg, machines=machines, zones=zones)

        w_m = (cfg["x1"] - cfg["x0"]) * cfg["scale"]
        d_m = (cfg["y1"] - cfg["y0"]) * cfg["scale"]
        summary.append(f"=== {cfg['label']}  {len(machines)} machines, {len(zones)} zones  "
                       f"[{w_m:.1f} x {d_m:.1f} m, scale {cfg['scale']} m/px]")
        for z in zones:
            summary.append(f"    zone  {z['name']:<32} x={z['x']:6.1f} z={z['z']:6.1f} "
                           f"w={z['w']:5.1f} d={z['d']:5.1f}  {z['area'] or ''}")
        for e in machines:
            summary.append(f"    equip {e['id']:<7} {e['name']:<42} {e['mtype']:<10} "
                           f"x={e['x']:6.1f} z={e['z']:6.1f} [{e['src']}]")

    js = ["// ─────────────────────────────────────────────────────────────────",
          "// ATELIERS — implantation relevée sur les plans SOMIZ scannés",
          "//   « PLAN D'IMPLANTATION DES MACHINES ET ÉQUIPEMENTS » (SOMIZ, Arzew)",
          "//   DIS / DLOG / DCA : Plan P-01, ind. 01, 12/05/2024",
          "//   Centrale         : Plan P-01, ind. 01, 01/04/2024",
          "// Positions et surfaces : APPROXIMATIVES (relevées par OCR sur le scan ;",
          "//   DIS calé sur la cote d'ensemble 91,41 m, autres ateliers estimés",
          "//   à partir des surfaces S= imprimées — aucune cote lisible au scan).",
          "// États / âges / historiques : SIMULÉS pour la démonstration,",
          "//   aucune donnée de maintenance réelle n'est représentée ici.",
          "// ─────────────────────────────────────────────────────────────────",
          "const ATELIERS = ["]
    for name in ORDER:
        d = out[name]
        cfg = d["cfg"]
        w_m = (cfg["x1"] - cfg["x0"]) * cfg["scale"]
        d_m = (cfg["y1"] - cfg["y0"]) * cfg["scale"]
        js.append(f"  {{ name:{js_str(cfg['label'])}, surface:{js_str(cfg['surface'])}, "
                  f"w:{w_m:.2f}, d:{d_m:.2f},")
        js.append("    zones:[")
        for z in d["zones"]:
            area = f", area:{js_str(z['area'])}" if z["area"] else ""
            js.append(f"      {{name:{js_str(z['name'])},x:{z['x']},z:{z['z']},w:{z['w']},d:{z['d']},"
                      f"color:0x{z['color']:06x}{area}}},")
        js.append("    ],")
        js.append("    equipment:[")
        for e in d["machines"]:
            hist = ",".join(js_str(h) for h in e["history"])
            js.append(
                f"      mkEquip({js_str(e['id'])},{js_str(e['name'])},{js_str(e['typ'])},"
                f"{js_str(e['mtype'])},{e['x']},{e['z']},{e['w']},{e['d']},STATUS.{e['status'].upper()}"
                f",{js_str(e['crit'])},{e['age']},{js_str(e['last'])},{js_str(e['next'])},[{hist}]),")
        js.append("    ]")
        js.append("  },")
    js.append("];")
    js.append("")

    with open(os.path.join(HERE, "ateliers_snippet.js"), "w") as fh:
        fh.write("\n".join(js))
    with open(os.path.join(HERE, "layout_summary.txt"), "w") as fh:
        fh.write("\n".join(summary + [""] + debug) + "\n")
    with open(os.path.join(HERE, "layout_data.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\n".join(summary))
    print("\n".join(debug))
    print("\nwrote ateliers_snippet.js, layout_summary.txt, layout_data.json")


if __name__ == "__main__":
    emit()

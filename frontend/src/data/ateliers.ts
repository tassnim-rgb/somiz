// Plan-derived plant data for the SOMIZ React app — GENERATED FILE.
// Source: OCR of « PLAN D'IMPLANTATION DES MACHINES ET ÉQUIPEMENTS »
// P-01 ind. 01 (DIS · DLOG · DCA 12/05/2024, Centrale 01/04/2024).
// Positions/surfaces: APPROXIMATE (OCR readings, see tools/plan_layout/README.md).
// Status/age/dates/sensor states: SIMULATED (seeded, deterministic) — not SOMIZ data.
// Regenerate with: node tools/plan_layout/make_ts.js (byte-identical; reads
// tools/plan_layout/ateliers_data.json — the frozen dump of the ATELIERS block
// in index.html; layout numbers originate from tools/plan_layout/gen_layout.py).

export type Status = 'ok' | 'warn' | 'danger' | 'critical';

export interface Zone {
  name: string; x: number; z: number; w: number; d: number;
  color: number; area?: string;
}

export interface Sensor {
  label: string; unit: string; base: number; kind: 'vib' | 'temp' | 'rpm' | 'load';
  _mean: number; _noise: number; _phase: number; _omega: number;
  _lastEvent: number; value: number;
}

export interface Equip {
  id: string; name: string; type: string; mtype: string;
  x: number; z: number; w: number; d: number;
  status: Status; criticality: 'A' | 'B' | 'C'; age: number;
  lastMaint: string; nextMaint: string; history: string[];
  sensors: Sensor[]; _wear: number;
}

export interface Atelier {
  name: string; surface: string; w: number; d: number;
  zones: Zone[]; equipment: Equip[];
}

export const STATUS_COLORS: Record<Status, number> = {"ok":3066993,"warn":16098851,"danger":15226175,"critical":16723310};
export const SENSOR_SCALE: Record<Status, number> = {"ok":1,"warn":1.18,"danger":1.5,"critical":1.95};
export const WEAR_INIT: Record<Status, number> = {"ok":0.15,"warn":0.52,"danger":0.78,"critical":0.94};

export const ATELIERS: Atelier[] = [
 {
  "name": "Atelier DIS",
  "surface": "4 133 m²",
  "w": 91.41,
  "d": 54.35,
  "zones": [
   {
    "name": "Zone Production",
    "x": 15.1,
    "z": 15.92,
    "w": 69.17,
    "d": 38.43,
    "color": 794416,
    "area": "S = 4 133,39 m²"
   },
   {
    "name": "Zone de Stockage Polyuréthane",
    "x": 84.55,
    "z": 17.84,
    "w": 6.86,
    "d": 24.7,
    "color": 727592,
    "area": "1 106 m³"
   },
   {
    "name": "Réfectoire",
    "x": 27.38,
    "z": 8.23,
    "w": 6.6,
    "d": 6.6,
    "color": 727077,
    "area": "S = 43,39 m²"
   },
   {
    "name": "Hall",
    "x": 20.28,
    "z": 5.84,
    "w": 6.4,
    "d": 6.4,
    "color": 661026,
    "area": "S = 40,95 m²"
   },
   {
    "name": "Ingénieurs",
    "x": 4.54,
    "z": 3.48,
    "w": 5.6,
    "d": 5.6,
    "color": 793902,
    "area": "S = 31,14 m²"
   },
   {
    "name": "Magasin",
    "x": 3.13,
    "z": 20.23,
    "w": 4.7,
    "d": 4.7,
    "color": 727077,
    "area": "S = 22,36 m²"
   },
   {
    "name": "Moussala",
    "x": 4.59,
    "z": 15.26,
    "w": 4.6,
    "d": 4.6,
    "color": 661026,
    "area": "S = 21,18 m²"
   },
   {
    "name": "Batis",
    "x": 0.2,
    "z": 25.3,
    "w": 13.93,
    "d": 13.93,
    "color": 793902,
    "area": "S = 394 m²"
   }
  ],
  "equipment": [
   {
    "id": "DIS-01",
    "name": "Guillotine Électrique",
    "type": "Découpe",
    "mtype": "press",
    "x": 35.14,
    "z": 16.23,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "A",
    "age": 19,
    "lastMaint": "2024-06-17",
    "nextMaint": "2024-12-17",
    "history": [
     "2023-12-20 — RAS — relevé conforme"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 6.216713796873818,
      "_omega": 2.0991722502884302,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 3.30987932367892,
      "_omega": 0.20973650030544397,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 2.6265022903507753,
      "_omega": 1.7128998895586038,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.14049239476026643
   },
   {
    "id": "DIS-02",
    "name": "Guillotine Électrique",
    "type": "Découpe",
    "mtype": "press",
    "x": 19.14,
    "z": 15.13,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "B",
    "age": 27,
    "lastMaint": "2024-03-11",
    "nextMaint": "2024-09-10",
    "history": [
     "2023-09-13 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 2.244883380389774,
      "_omega": 1.7890606472423114,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 5.2852628110914175,
      "_omega": 0.30012580088966834,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 3.7154661388472046,
      "_omega": 1.3066044391439755,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.16459973650991824
   },
   {
    "id": "DIS-03",
    "name": "Extracteur d'Air",
    "type": "Ventilation",
    "mtype": "vent",
    "x": 61.99,
    "z": 19.36,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 23,
    "lastMaint": "2024-01-15",
    "nextMaint": "2024-07-16",
    "history": [
     "2023-07-19 — Inspection préventive OK"
    ],
    "sensors": [
     {
      "label": "Débit",
      "unit": "m³/h",
      "base": 2400,
      "kind": "load",
      "_mean": 2400,
      "_noise": 0,
      "_phase": 2.308477046493793,
      "_omega": 1.524181152933698,
      "_lastEvent": 0,
      "value": 2400
     },
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.6,
      "kind": "vib",
      "_mean": 0.6,
      "_noise": 0,
      "_phase": 1.7774594695244745,
      "_omega": 5.983665203591034,
      "_lastEvent": 0,
      "value": 0.6
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 29,
      "kind": "temp",
      "_mean": 29,
      "_noise": 0,
      "_phase": 2.908287136269942,
      "_omega": 0.15424262285497103,
      "_lastEvent": 0,
      "value": 29
     }
    ],
    "_wear": 0.1626408491186581
   },
   {
    "id": "DIS-04",
    "name": "Guillotine Électrique",
    "type": "Découpe",
    "mtype": "press",
    "x": 19.16,
    "z": 19.56,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "C",
    "age": 7,
    "lastMaint": "2024-02-13",
    "nextMaint": "2024-08-14",
    "history": [
     "2023-08-17 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 5.089247259950737,
      "_omega": 1.411129356792462,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 0.12370540003841561,
      "_omega": 0.25413101316452347,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 1.1159547405082972,
      "_omega": 1.2216283153442307,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.14644888046004312
   },
   {
    "id": "DIS-05",
    "name": "Machine Wintech Découpage Polyuréthane",
    "type": "Découpe mousse",
    "mtype": "mill",
    "x": 57.28,
    "z": 22.57,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "C",
    "age": 13,
    "lastMaint": "2024-01-24",
    "nextMaint": "2024-07-25",
    "history": [
     "2023-07-28 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 6.222165241985369,
      "_omega": 5.62734089064122,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 1.200529763455067,
      "_omega": 0.2638488329430151,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 0.13845469200740224,
      "_omega": 1.7265941123125927,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.14899185725976583
   },
   {
    "id": "DIS-06",
    "name": "Bordeuse Tôle",
    "type": "Formage métal",
    "mtype": "generic",
    "x": 35.66,
    "z": 23.8,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 28,
    "lastMaint": "2024-06-06",
    "nextMaint": "2024-12-06",
    "history": [
     "2023-12-09 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 1.522600174725675,
      "_omega": 4.241487514404376,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 2.681182783833325,
      "_omega": 0.15343731439183741,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 0.7988679119934954,
      "_omega": 1.4531730486828844,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.16182128083755815
   },
   {
    "id": "DIS-07",
    "name": "Rouleuse de Tôle",
    "type": "Formage métal",
    "mtype": "mill",
    "x": 21.32,
    "z": 23.99,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "C",
    "age": 12,
    "lastMaint": "2024-04-17",
    "nextMaint": "2024-10-17",
    "history": [
     "2023-10-20 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 2.471807779614542,
      "_omega": 6.45849292956456,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 6.011752575757845,
      "_omega": 0.3256969869960975,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 2.829564036876721,
      "_omega": 1.258390093603159,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.13672856634034472
   },
   {
    "id": "DIS-08",
    "name": "Scie à Ruban Électrique",
    "type": "Découpe",
    "mtype": "saw",
    "x": 52.46,
    "z": 24.93,
    "w": 3.5,
    "d": 4,
    "status": "ok",
    "criticality": "C",
    "age": 20,
    "lastMaint": "2024-05-04",
    "nextMaint": "2024-11-03",
    "history": [
     "2023-11-06 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 22,
      "_noise": 0,
      "_phase": 6.2673111781153,
      "_omega": 1.4220917584830182,
      "_lastEvent": 0,
      "value": 22
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 35,
      "_noise": 0,
      "_phase": 3.216109105728727,
      "_omega": 0.150830350684708,
      "_lastEvent": 0,
      "value": 35
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 410,
      "_noise": 0,
      "_phase": 3.330762907573402,
      "_omega": 2.06861487963087,
      "_lastEvent": 0,
      "value": 410
     }
    ],
    "_wear": 0.14605559435824886
   },
   {
    "id": "DIS-09",
    "name": "Graveuse",
    "type": "Gravure",
    "mtype": "drill",
    "x": 37.26,
    "z": 27.24,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 6,
    "lastMaint": "2024-03-31",
    "nextMaint": "2024-09-30",
    "history": [
     "2023-10-03 — RAS — relevé conforme"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 1.2640350281668105,
      "_omega": 4.876875917962241,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 1.9043480331547613,
      "_omega": 0.3469413156781723,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 1.5677626205195974,
      "_omega": 2.0962277828804172,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.13504146274278744
   },
   {
    "id": "DIS-10",
    "name": "Guillotine Électrique",
    "type": "Découpe",
    "mtype": "press",
    "x": 20.44,
    "z": 27.99,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "B",
    "age": 3,
    "lastMaint": "2024-06-07",
    "nextMaint": "2024-12-07",
    "history": [
     "2023-12-10 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 5.566194643162244,
      "_omega": 0.8200454729499884,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 3.2068232080480543,
      "_omega": 0.3502436905235433,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 5.309433023603304,
      "_omega": 1.6659369659826375,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.13524912810153714
   },
   {
    "id": "DIS-11",
    "name": "Scie à Ruban Électrique",
    "type": "Découpe",
    "mtype": "saw",
    "x": 67.77,
    "z": 28.74,
    "w": 3.5,
    "d": 4,
    "status": "ok",
    "criticality": "A",
    "age": 9,
    "lastMaint": "2024-01-03",
    "nextMaint": "2024-07-04",
    "history": [
     "2023-07-07 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 22,
      "_noise": 0,
      "_phase": 3.702391493233337,
      "_omega": 2.044106156071585,
      "_lastEvent": 0,
      "value": 22
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 35,
      "_noise": 0,
      "_phase": 4.712131911600382,
      "_omega": 0.3072910842460063,
      "_lastEvent": 0,
      "value": 35
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 410,
      "_noise": 0,
      "_phase": 3.4835517061906787,
      "_omega": 0.8564182056850962,
      "_lastEvent": 0,
      "value": 410
     }
    ],
    "_wear": 0.14111802113532615
   },
   {
    "id": "DIS-12",
    "name": "Graveuse",
    "type": "Gravure",
    "mtype": "drill",
    "x": 41.73,
    "z": 27.24,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 9,
    "lastMaint": "2024-01-21",
    "nextMaint": "2024-07-22",
    "history": [
     "2023-07-25 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 1.6956490920578633,
      "_omega": 4.7328906651005465,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 6.246949380710055,
      "_omega": 0.266044667399145,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 1.2395319246335583,
      "_omega": 2.030529439948567,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.16351679967019128
   },
   {
    "id": "DIS-13",
    "name": "Bordeuse Tôle",
    "type": "Formage métal",
    "mtype": "generic",
    "x": 34.87,
    "z": 30.71,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 23,
    "lastMaint": "2024-03-14",
    "nextMaint": "2024-09-13",
    "history": [
     "2023-09-16 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 6.100093253317762,
      "_omega": 6.746937699735769,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 3.1257303385187063,
      "_omega": 0.1811296153192414,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 4.360946953672113,
      "_omega": 1.5824887254733309,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.16282833633664964
   },
   {
    "id": "DIS-14",
    "name": "Rouleuse de Tôle",
    "type": "Formage métal",
    "mtype": "mill",
    "x": 21.44,
    "z": 32.42,
    "w": 4,
    "d": 3.5,
    "status": "danger",
    "criticality": "A",
    "age": 25,
    "lastMaint": "2024-04-26",
    "nextMaint": "2024-10-26",
    "history": [
     "2023-10-29 — Roulement à remplacer"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 2.0999999999999996,
      "_noise": 0,
      "_phase": 1.8794277061600702,
      "_omega": 6.220726698207606,
      "_lastEvent": 0,
      "value": 2.1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 61.5,
      "_noise": 0,
      "_phase": 5.80346609650745,
      "_omega": 0.21181145053400022,
      "_lastEvent": 0,
      "value": 61.5
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 93,
      "_noise": 0,
      "_phase": 3.591855154931444,
      "_omega": 2.1507656219862303,
      "_lastEvent": 0,
      "value": 93
     }
    ],
    "_wear": 0.8269707035317329
   },
   {
    "id": "DIS-15",
    "name": "Rouleuse de Tôle",
    "type": "Formage métal",
    "mtype": "mill",
    "x": 39.37,
    "z": 30.66,
    "w": 4,
    "d": 3.5,
    "status": "danger",
    "criticality": "B",
    "age": 15,
    "lastMaint": "2024-01-07",
    "nextMaint": "2024-07-08",
    "history": [
     "2023-01-12 — Surcharge répétée",
     "2023-07-11 — Fuite hydraulique détectée"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 2.0999999999999996,
      "_noise": 0,
      "_phase": 3.3404249535160035,
      "_omega": 4.895980470544456,
      "_lastEvent": 0,
      "value": 2.1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 61.5,
      "_noise": 0,
      "_phase": 5.148947424354573,
      "_omega": 0.3629404082168638,
      "_lastEvent": 0,
      "value": 61.5
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 93,
      "_noise": 0,
      "_phase": 5.100393815571747,
      "_omega": 1.5303003536518593,
      "_lastEvent": 0,
      "value": 93
     }
    ],
    "_wear": 0.8130056116368616
   },
   {
    "id": "DIS-16",
    "name": "Cintreuse Rouleuse de Tôle",
    "type": "Formage métal",
    "mtype": "mill",
    "x": 14.25,
    "z": 32.55,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "B",
    "age": 26,
    "lastMaint": "2024-02-06",
    "nextMaint": "2024-08-07",
    "history": [
     "2023-08-10 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 3.8289970728244804,
      "_omega": 4.359177821931082,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 5.271191748897487,
      "_omega": 0.23457523102828415,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 1.7019724839977541,
      "_omega": 2.0176965622104976,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.14460377021701695
   },
   {
    "id": "DIS-17",
    "name": "Scie à Ruban Électrique",
    "type": "Découpe",
    "mtype": "saw",
    "x": 46.95,
    "z": 33.68,
    "w": 3.5,
    "d": 4,
    "status": "ok",
    "criticality": "C",
    "age": 6,
    "lastMaint": "2024-04-12",
    "nextMaint": "2024-10-12",
    "history": [
     "2023-10-15 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 22,
      "_noise": 0,
      "_phase": 3.2067059845036914,
      "_omega": 0.8078708111317999,
      "_lastEvent": 0,
      "value": 22
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 35,
      "_noise": 0,
      "_phase": 1.4074039501134021,
      "_omega": 0.29107917718531057,
      "_lastEvent": 0,
      "value": 35
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 410,
      "_noise": 0,
      "_phase": 2.855759051407201,
      "_omega": 1.6811130021158802,
      "_lastEvent": 0,
      "value": 410
     }
    ],
    "_wear": 0.1486149274010665
   },
   {
    "id": "DIS-18",
    "name": "Guillotine Manuel",
    "type": "Découpe",
    "mtype": "press",
    "x": 28.41,
    "z": 34.76,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "B",
    "age": 25,
    "lastMaint": "2024-05-25",
    "nextMaint": "2024-11-24",
    "history": [
     "2023-11-27 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 4.545094760149609,
      "_omega": 1.558856867841027,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 1.9489192103399184,
      "_omega": 0.2629164907637691,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 4.952593262232989,
      "_omega": 1.0654828023357341,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.16123558456031986
   },
   {
    "id": "DIS-19",
    "name": "Guillotine Électrique",
    "type": "Découpe",
    "mtype": "press",
    "x": 20.39,
    "z": 36.35,
    "w": 4,
    "d": 4,
    "status": "danger",
    "criticality": "B",
    "age": 14,
    "lastMaint": "2024-03-17",
    "nextMaint": "2024-09-16",
    "history": [
     "2023-09-19 — Fuite hydraulique détectée"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 217.5,
      "_noise": 0,
      "_phase": 4.56140597657532,
      "_omega": 2.04305140135678,
      "_lastEvent": 0,
      "value": 217.5
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 66,
      "_noise": 0,
      "_phase": 6.122988993508367,
      "_omega": 0.280003017884231,
      "_lastEvent": 0,
      "value": 66
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 57,
      "_noise": 0,
      "_phase": 2.5861643380684867,
      "_omega": 0.973769489740761,
      "_lastEvent": 0,
      "value": 57
     }
    ],
    "_wear": 0.7921402439862489
   },
   {
    "id": "DIS-20",
    "name": "Rouleuse de Tôle",
    "type": "Formage métal",
    "mtype": "mill",
    "x": 38.8,
    "z": 34.66,
    "w": 4,
    "d": 3.5,
    "status": "critical",
    "criticality": "A",
    "age": 6,
    "lastMaint": "2024-05-21",
    "nextMaint": "2024-11-20",
    "history": [
     "2023-11-23 — Arrêt d'urgence déclenché"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 2.73,
      "_noise": 0,
      "_phase": 2.6721165442101307,
      "_omega": 5.9805632865971186,
      "_lastEvent": 0,
      "value": 2.7
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 79.95,
      "_noise": 0,
      "_phase": 0.683863157213761,
      "_omega": 0.19462273519890042,
      "_lastEvent": 0,
      "value": 80
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 120.89999999999999,
      "_noise": 0,
      "_phase": 5.621644726703159,
      "_omega": 1.5474987924644525,
      "_lastEvent": 0,
      "value": 120.9
     }
    ],
    "_wear": 0.9817073551109083
   },
   {
    "id": "DIS-21",
    "name": "Meuleuse",
    "type": "Ébavurage",
    "mtype": "mill",
    "x": 62.12,
    "z": 35.69,
    "w": 4,
    "d": 3.5,
    "status": "warn",
    "criticality": "A",
    "age": 16,
    "lastMaint": "2024-06-15",
    "nextMaint": "2024-12-15",
    "history": [
     "2023-06-21 — Résistance à surveiller",
     "2023-12-18 — Disque à 60% d'usure"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.652,
      "_noise": 0,
      "_phase": 2.9652622241558673,
      "_omega": 4.413970281179505,
      "_lastEvent": 0,
      "value": 1.7
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 48.379999999999995,
      "_noise": 0,
      "_phase": 5.199301254647431,
      "_omega": 0.16686789385588308,
      "_lastEvent": 0,
      "value": 48.4
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 73.16,
      "_noise": 0,
      "_phase": 4.729314457279793,
      "_omega": 1.007044784457191,
      "_lastEvent": 0,
      "value": 73.2
     }
    ],
    "_wear": 0.47764611847955435
   },
   {
    "id": "DIS-22",
    "name": "Graveuse",
    "type": "Gravure",
    "mtype": "drill",
    "x": 35.3,
    "z": 35.75,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 23,
    "lastMaint": "2024-05-28",
    "nextMaint": "2024-11-27",
    "history": [
     "2023-11-30 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 1.8322692481557856,
      "_omega": 4.101626447583207,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 0.4002896732761252,
      "_omega": 0.17857197210685308,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 5.855103467077126,
      "_omega": 0.9789598413027252,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.15102296331738088
   },
   {
    "id": "DIS-23",
    "name": "Scie à Ruban Électrique",
    "type": "Découpe",
    "mtype": "saw",
    "x": 52.49,
    "z": 35.85,
    "w": 3.5,
    "d": 4,
    "status": "warn",
    "criticality": "B",
    "age": 28,
    "lastMaint": "2024-02-11",
    "nextMaint": "2024-08-12",
    "history": [
     "2023-08-15 — Jeu axial à surveiller"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 25.959999999999997,
      "_noise": 0,
      "_phase": 2.7130830417216276,
      "_omega": 1.6576281871825822,
      "_lastEvent": 0,
      "value": 26
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 41.3,
      "_noise": 0,
      "_phase": 1.9090621214367178,
      "_omega": 0.379244686156348,
      "_lastEvent": 0,
      "value": 41.3
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 483.79999999999995,
      "_noise": 0,
      "_phase": 0.7005279306768615,
      "_omega": 1.2004855924666082,
      "_lastEvent": 0,
      "value": 483.8
     }
    ],
    "_wear": 0.5468634993522952
   },
   {
    "id": "DIS-24",
    "name": "Coupe Cercle",
    "type": "Découpe",
    "mtype": "drill",
    "x": 14.56,
    "z": 36.83,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 25,
    "lastMaint": "2024-03-04",
    "nextMaint": "2024-09-03",
    "history": [
     "2023-09-06 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 3.439086077131596,
      "_omega": 4.709790772436757,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 2.598921133943034,
      "_omega": 0.3293258994801946,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 3.2108999440826955,
      "_omega": 2.107255029056919,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.158801606839032
   },
   {
    "id": "DIS-25",
    "name": "Rouleuse de Tôle",
    "type": "Formage métal",
    "mtype": "mill",
    "x": 21.22,
    "z": 40.77,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "B",
    "age": 26,
    "lastMaint": "2024-03-15",
    "nextMaint": "2024-09-14",
    "history": [
     "2023-09-17 — RAS — relevé conforme"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 2.487031707557717,
      "_omega": 4.613516705199952,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 2.8583728088334466,
      "_omega": 0.20955172141562073,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 2.9136468858263145,
      "_omega": 1.9287730840174424,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.14142580230743323
   },
   {
    "id": "DIS-26",
    "name": "Plyeuse Tôle",
    "type": "Pliage",
    "mtype": "press",
    "x": 39.15,
    "z": 38.57,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "C",
    "age": 18,
    "lastMaint": "2024-06-05",
    "nextMaint": "2024-12-05",
    "history": [
     "2023-12-08 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 4.798808148444391,
      "_omega": 1.493299837513388,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 2.405952147228232,
      "_omega": 0.3413298926280394,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 1.1712247085535041,
      "_omega": 2.161582745673318,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.14906822091859281
   },
   {
    "id": "DIS-27",
    "name": "Bordeuse Tôle",
    "type": "Formage métal",
    "mtype": "generic",
    "x": 39.42,
    "z": 43,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 24,
    "lastMaint": "2024-05-29",
    "nextMaint": "2024-11-28",
    "history": [
     "2023-12-01 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 1.2477313561029386,
      "_omega": 5.940216047619591,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 3.4971368945432038,
      "_omega": 0.2681642500815138,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 3.4809922538948275,
      "_omega": 1.3341994067986476,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.1377410816461584
   },
   {
    "id": "DIS-28",
    "name": "Coupe Cercle",
    "type": "Découpe",
    "mtype": "drill",
    "x": 28.96,
    "z": 42.21,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 13,
    "lastMaint": "2024-03-04",
    "nextMaint": "2024-09-03",
    "history": [
     "2023-09-06 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 2.498594102166851,
      "_omega": 5.840961827873658,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 0.3917080422333187,
      "_omega": 0.3503651076206793,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 4.520147615267558,
      "_omega": 2.17283608637601,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.15999721379617796
   },
   {
    "id": "DIS-29",
    "name": "Scie à Ruban Électrique",
    "type": "Découpe",
    "mtype": "saw",
    "x": 67.63,
    "z": 47.25,
    "w": 3.5,
    "d": 4,
    "status": "warn",
    "criticality": "A",
    "age": 17,
    "lastMaint": "2024-04-17",
    "nextMaint": "2024-10-17",
    "history": [
     "2023-04-23 — Résistance à surveiller",
     "2023-10-20 — Vibration anormale détectée"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 25.959999999999997,
      "_noise": 0,
      "_phase": 6.258262475161118,
      "_omega": 0.9698382006195871,
      "_lastEvent": 0,
      "value": 26
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 41.3,
      "_noise": 0,
      "_phase": 3.27608740976704,
      "_omega": 0.18037448290648592,
      "_lastEvent": 0,
      "value": 41.3
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 483.79999999999995,
      "_noise": 0,
      "_phase": 0.6101996639907328,
      "_omega": 2.018495987286554,
      "_lastEvent": 0,
      "value": 483.8
     }
    ],
    "_wear": 0.5075014109501869
   }
  ]
 },
 {
  "name": "Atelier DLOG",
  "surface": "2 253 m²",
  "w": 63.08,
  "d": 53.2,
  "zones": [
   {
    "name": "Zone Production",
    "x": 0,
    "z": 0,
    "w": 63.08,
    "d": 17.86,
    "color": 794416,
    "area": "S = 2 252,95 m²"
   },
   {
    "name": "Zone Production",
    "x": 15.2,
    "z": 18.05,
    "w": 25.65,
    "d": 35.15,
    "color": 794416,
    "area": "S = 2 252,95 m²"
   },
   {
    "name": "Elec. Poste",
    "x": 1.16,
    "z": 18.44,
    "w": 6,
    "d": 6,
    "color": 727077
   },
   {
    "name": "Directeur DSL",
    "x": 0.2,
    "z": 25.42,
    "w": 4.8,
    "d": 4.8,
    "color": 661026,
    "area": "S = 23,10 m²"
   },
   {
    "name": "Secrétariat DLOG",
    "x": 0.2,
    "z": 30.66,
    "w": 4.23,
    "d": 4.23,
    "color": 793902,
    "area": "S = 21,94 m²"
   },
   {
    "name": "Sanitaires",
    "x": 0.2,
    "z": 36,
    "w": 4.8,
    "d": 4.8,
    "color": 727077,
    "area": "S = 23,40 m²"
   },
   {
    "name": "Hall",
    "x": 6.15,
    "z": 33.15,
    "w": 4.2,
    "d": 4.2,
    "color": 661026,
    "area": "S = 17,32 m²"
   },
   {
    "name": "Magasin",
    "x": 9.03,
    "z": 27.86,
    "w": 4.8,
    "d": 4.8,
    "color": 793902,
    "area": "S = 23,40 m²"
   },
   {
    "name": "Magasin",
    "x": 6.75,
    "z": 37.82,
    "w": 7.5,
    "d": 7.5,
    "color": 727077,
    "area": "S = 55,72 m²"
   },
   {
    "name": "Sanitaires",
    "x": 41.85,
    "z": 41.16,
    "w": 10.4,
    "d": 10.4,
    "color": 661026,
    "area": "S = 109 m²"
   },
   {
    "name": "Vestiaires",
    "x": 41.66,
    "z": 28.82,
    "w": 9.5,
    "d": 9.5,
    "color": 793902,
    "area": "S = 90,23 m²"
   },
   {
    "name": "Peinture & Tôlerie",
    "x": 51.92,
    "z": 22.89,
    "w": 10.96,
    "d": 10.96,
    "color": 727077,
    "area": "S = 188,72 m²"
   }
  ],
  "equipment": [
   {
    "id": "DLG-01",
    "name": "Presse Étoupe",
    "type": "Pressage",
    "mtype": "press",
    "x": 9.78,
    "z": 2.9,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "B",
    "age": 22,
    "lastMaint": "2024-02-11",
    "nextMaint": "2024-08-12",
    "history": [
     "2023-08-15 — Inspection préventive OK"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 4.915876226529018,
      "_omega": 2.132687937773115,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 5.457392738561696,
      "_omega": 0.20606395244987463,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 5.465635883669264,
      "_omega": 1.8286898257505875,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.1631458803619614
   },
   {
    "id": "DLG-02",
    "name": "Panneaux de Levage",
    "type": "Manutention",
    "mtype": "generic",
    "x": 10.81,
    "z": 7.39,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "A",
    "age": 26,
    "lastMaint": "2024-03-13",
    "nextMaint": "2024-09-12",
    "history": [
     "2023-09-15 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 1.5378992157791282,
      "_omega": 3.5404786692385906,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 6.281081244290445,
      "_omega": 0.22193778697882127,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 3.529868975720314,
      "_omega": 1.647923339741244,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.15793559375336028
   },
   {
    "id": "DLG-03",
    "name": "Outil de Ponçage et Meulage Électrique",
    "type": "Ponçage / meulage",
    "mtype": "drill",
    "x": 33.52,
    "z": 32.62,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 6,
    "lastMaint": "2024-06-05",
    "nextMaint": "2024-12-05",
    "history": [
     "2023-12-08 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 1.5580836147720785,
      "_omega": 4.021726961592789,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 1.7109033257623003,
      "_omega": 0.3471974015726675,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 5.86680418965728,
      "_omega": 1.5058834217224093,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.13550961404472583
   },
   {
    "id": "DLG-04",
    "name": "Compresseur d'Air",
    "type": "Air comprimé",
    "mtype": "compressor",
    "x": 48.17,
    "z": 37.7,
    "w": 3,
    "d": 3,
    "status": "danger",
    "criticality": "A",
    "age": 17,
    "lastMaint": "2024-05-14",
    "nextMaint": "2024-11-13",
    "history": [
     "2023-11-16 — Fuite hydraulique détectée"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 8.2,
      "kind": "load",
      "_mean": 12.299999999999999,
      "_noise": 0,
      "_phase": 1.0720808092043979,
      "_omega": 1.2263384265898838,
      "_lastEvent": 0,
      "value": 12.3
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 56,
      "kind": "temp",
      "_mean": 84,
      "_noise": 0,
      "_phase": 3.746066468640819,
      "_omega": 0.25224904840604195,
      "_lastEvent": 0,
      "value": 84
     },
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 2.1,
      "kind": "vib",
      "_mean": 3.1500000000000004,
      "_noise": 0,
      "_phase": 2.0529386520558663,
      "_omega": 6.145081017850551,
      "_lastEvent": 0,
      "value": 3.2
     }
    ],
    "_wear": 0.7555595360929211
   },
   {
    "id": "DLG-05",
    "name": "Presse Électrique",
    "type": "Pressage",
    "mtype": "press",
    "x": 34.1,
    "z": 46.7,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "C",
    "age": 20,
    "lastMaint": "2024-03-19",
    "nextMaint": "2024-09-18",
    "history": [
     "2023-09-21 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 2.2877554011105907,
      "_omega": 1.893969758218944,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 4.0975519554533095,
      "_omega": 0.2760605435743283,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 4.2770586683671175,
      "_omega": 1.1734451992238422,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.160326988204598
   },
   {
    "id": "DLG-06",
    "name": "Panneaux de Levage Électrique",
    "type": "Manutention",
    "mtype": "generic",
    "x": 17.71,
    "z": 49.9,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 20,
    "lastMaint": "2024-01-26",
    "nextMaint": "2024-07-27",
    "history": [
     "2023-07-30 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 5.4672695099012705,
      "_omega": 5.659885728539077,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 4.248704226985498,
      "_omega": 0.2919445749461063,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 4.2174267040560105,
      "_omega": 1.0866722919345477,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.14196237317528862
   }
  ]
 },
 {
  "name": "Atelier Centrale",
  "surface": "Multi-zones",
  "w": 66,
  "d": 79.64,
  "zones": [
   {
    "name": "Atelier Fabrication Mécanique",
    "x": 16.5,
    "z": 18.04,
    "w": 28.6,
    "d": 53.9,
    "color": 794416,
    "area": "Sections : Tournage, Équilibrage, Fraisage"
   },
   {
    "name": "Atelier Turbo Machine",
    "x": 48.66,
    "z": 6.64,
    "w": 13.99,
    "d": 13.99,
    "color": 727592
   },
   {
    "name": "Atelier Bobinage",
    "x": 48.4,
    "z": 41.14,
    "w": 17.6,
    "d": 17.6,
    "color": 727592
   },
   {
    "name": "Atelier DEI",
    "x": 48.4,
    "z": 58.96,
    "w": 17.6,
    "d": 15.18,
    "color": 727592
   },
   {
    "name": "Instrumentation",
    "x": 1.16,
    "z": 6.15,
    "w": 9,
    "d": 9,
    "color": 727077
   },
   {
    "name": "Atelier Traitement Thermique",
    "x": 0.2,
    "z": 30.71,
    "w": 10,
    "d": 10,
    "color": 661026
   },
   {
    "name": "Magasin",
    "x": 0.2,
    "z": 54.54,
    "w": 8,
    "d": 8,
    "color": 793902
   },
   {
    "name": "Atelier Vannes & Soupapes",
    "x": 0.2,
    "z": 63.3,
    "w": 9,
    "d": 9,
    "color": 727077
   },
   {
    "name": "Compresseurs",
    "x": 0.2,
    "z": 73.04,
    "w": 6.4,
    "d": 6.4,
    "color": 661026
   },
   {
    "name": "Douche",
    "x": 45.66,
    "z": 28.75,
    "w": 6,
    "d": 6,
    "color": 793902
   }
  ],
  "equipment": [
   {
    "id": "CEN-01",
    "name": "Compresseur",
    "type": "Air comprimé",
    "mtype": "compressor",
    "x": 19.8,
    "z": 0.35,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "A",
    "age": 3,
    "lastMaint": "2024-06-01",
    "nextMaint": "2024-12-01",
    "history": [
     "2023-12-04 — Inspection préventive OK"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 8.2,
      "kind": "load",
      "_mean": 8.2,
      "_noise": 0,
      "_phase": 5.807359064420543,
      "_omega": 2.1199497951790294,
      "_lastEvent": 0,
      "value": 8.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 56,
      "kind": "temp",
      "_mean": 56,
      "_noise": 0,
      "_phase": 4.670453659882769,
      "_omega": 0.3678928721738443,
      "_lastEvent": 0,
      "value": 56
     },
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 2.1,
      "kind": "vib",
      "_mean": 2.1,
      "_noise": 0,
      "_phase": 2.5487225805002276,
      "_omega": 3.058878293287254,
      "_lastEvent": 0,
      "value": 2.1
     }
    ],
    "_wear": 0.15243400790984638
   },
   {
    "id": "CEN-02",
    "name": "Mortaiseuse",
    "type": "Mortaisage",
    "mtype": "mill",
    "x": 39.14,
    "z": 1.75,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "C",
    "age": 8,
    "lastMaint": "2024-05-18",
    "nextMaint": "2024-11-17",
    "history": [
     "2023-11-20 — RAS — relevé conforme"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 4.089944213317569,
      "_omega": 3.8847952089773954,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 0.9853727162069518,
      "_omega": 0.165646874962853,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 1.0089208762028972,
      "_omega": 1.2206165191061125,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.150260892768298
   },
   {
    "id": "CEN-03",
    "name": "Scie Mécanique",
    "type": "Découpe",
    "mtype": "saw",
    "x": 28.8,
    "z": 4.95,
    "w": 3.5,
    "d": 4,
    "status": "ok",
    "criticality": "B",
    "age": 25,
    "lastMaint": "2024-05-09",
    "nextMaint": "2024-11-08",
    "history": [
     "2023-11-11 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 22,
      "_noise": 0,
      "_phase": 4.845327025521907,
      "_omega": 1.722920144810168,
      "_lastEvent": 0,
      "value": 22
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 35,
      "_noise": 0,
      "_phase": 3.30850063863388,
      "_omega": 0.25597533762258073,
      "_lastEvent": 0,
      "value": 35
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 410,
      "_noise": 0,
      "_phase": 1.071716094925332,
      "_omega": 1.1494782043154272,
      "_lastEvent": 0,
      "value": 410
     }
    ],
    "_wear": 0.1422661799141198
   },
   {
    "id": "CEN-04",
    "name": "Banc d'essai",
    "type": "Essais",
    "mtype": "generic",
    "x": 0.3,
    "z": 5.13,
    "w": 4,
    "d": 3,
    "status": "warn",
    "criticality": "C",
    "age": 6,
    "lastMaint": "2024-03-29",
    "nextMaint": "2024-09-28",
    "history": [
     "2023-04-04 — Disque à 60% d'usure",
     "2023-10-01 — Température en hausse"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1.18,
      "_noise": 0,
      "_phase": 4.759226140279142,
      "_omega": 6.624874159841003,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 42.48,
      "_noise": 0,
      "_phase": 6.07314065695123,
      "_omega": 0.20139822188966225,
      "_lastEvent": 0,
      "value": 42.5
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 53.099999999999994,
      "_noise": 0,
      "_phase": 4.517567041624165,
      "_omega": 1.4218553524245616,
      "_lastEvent": 0,
      "value": 53.1
     }
    ],
    "_wear": 0.5366237477703315
   },
   {
    "id": "CEN-05",
    "name": "Etau-Limeur",
    "type": "Limage",
    "mtype": "mill",
    "x": 39.1,
    "z": 5.75,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "B",
    "age": 6,
    "lastMaint": "2024-05-03",
    "nextMaint": "2024-11-02",
    "history": [
     "2023-11-05 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 5.6776712901448425,
      "_omega": 5.774374958482287,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 0.25987444206668026,
      "_omega": 0.28461182112871247,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 2.1658137355579985,
      "_omega": 1.1748661538377045,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.16069977801272997
   },
   {
    "id": "CEN-06",
    "name": "Scie à Ruban",
    "type": "Découpe",
    "mtype": "saw",
    "x": 19.28,
    "z": 9.79,
    "w": 3.5,
    "d": 4,
    "status": "ok",
    "criticality": "B",
    "age": 12,
    "lastMaint": "2024-06-05",
    "nextMaint": "2024-12-05",
    "history": [
     "2023-12-08 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 22,
      "_noise": 0,
      "_phase": 3.3131221895156666,
      "_omega": 1.7052351662361516,
      "_lastEvent": 0,
      "value": 22
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 35,
      "_noise": 0,
      "_phase": 4.0860772976692985,
      "_omega": 0.28987736552374166,
      "_lastEvent": 0,
      "value": 35
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 410,
      "_noise": 0,
      "_phase": 3.748010683739583,
      "_omega": 1.6144865177385332,
      "_lastEvent": 0,
      "value": 410
     }
    ],
    "_wear": 0.1454829394796022
   },
   {
    "id": "CEN-07",
    "name": "Scie Mécanique",
    "type": "Découpe",
    "mtype": "saw",
    "x": 26.06,
    "z": 9.79,
    "w": 3.5,
    "d": 4,
    "status": "warn",
    "criticality": "C",
    "age": 5,
    "lastMaint": "2024-04-29",
    "nextMaint": "2024-10-29",
    "history": [
     "2023-11-01 — Température en hausse"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 25.959999999999997,
      "_noise": 0,
      "_phase": 6.254180636916374,
      "_omega": 1.3363683797278334,
      "_lastEvent": 0,
      "value": 26
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 41.3,
      "_noise": 0,
      "_phase": 5.0440062035842415,
      "_omega": 0.26965223647008374,
      "_lastEvent": 0,
      "value": 41.3
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 483.79999999999995,
      "_noise": 0,
      "_phase": 3.4121696630266514,
      "_omega": 1.1328522113659583,
      "_lastEvent": 0,
      "value": 483.8
     }
    ],
    "_wear": 0.4739966348644921
   },
   {
    "id": "CEN-08",
    "name": "Perceuse Radiale",
    "type": "Perçage",
    "mtype": "drill",
    "x": 37.84,
    "z": 15.52,
    "w": 3,
    "d": 3,
    "status": "danger",
    "criticality": "A",
    "age": 5,
    "lastMaint": "2024-02-20",
    "nextMaint": "2024-08-21",
    "history": [
     "2023-08-24 — Bielle usée"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 1.35,
      "_noise": 0,
      "_phase": 2.4938987335076717,
      "_omega": 6.153095548178703,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 49.5,
      "_noise": 0,
      "_phase": 3.053249301857552,
      "_omega": 0.2173894864354448,
      "_lastEvent": 0,
      "value": 49.5
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1800,
      "_noise": 0,
      "_phase": 0.10650173873859363,
      "_omega": 2.0551501633412856,
      "_lastEvent": 0,
      "value": 1800
     }
    ],
    "_wear": 0.7992192555677557
   },
   {
    "id": "CEN-09",
    "name": "Banc d'essai",
    "type": "Essais",
    "mtype": "generic",
    "x": 0.3,
    "z": 15.7,
    "w": 4,
    "d": 3,
    "status": "warn",
    "criticality": "C",
    "age": 12,
    "lastMaint": "2024-02-13",
    "nextMaint": "2024-08-14",
    "history": [
     "2023-08-17 — Résistance à surveiller"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1.18,
      "_noise": 0,
      "_phase": 4.0466569509251356,
      "_omega": 4.948239937001185,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 42.48,
      "_noise": 0,
      "_phase": 5.403329743028905,
      "_omega": 0.2889092857386285,
      "_lastEvent": 0,
      "value": 42.5
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 53.099999999999994,
      "_noise": 0,
      "_phase": 4.426003380648539,
      "_omega": 1.4866819850955808,
      "_lastEvent": 0,
      "value": 53.1
     }
    ],
    "_wear": 0.5224486618522872
   },
   {
    "id": "CEN-10",
    "name": "La Presse",
    "type": "Pressage",
    "mtype": "press",
    "x": 58.28,
    "z": 16.44,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "C",
    "age": 17,
    "lastMaint": "2024-06-16",
    "nextMaint": "2024-12-16",
    "history": [
     "2023-12-19 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 2.2735959563012718,
      "_omega": 1.7135313376575325,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 6.105260773092154,
      "_omega": 0.3853470231416751,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 0.9267192740909728,
      "_omega": 1.3438975807255318,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.16415434865037604
   },
   {
    "id": "CEN-11",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 17.26,
    "z": 19.07,
    "w": 5,
    "d": 3,
    "status": "critical",
    "criticality": "C",
    "age": 4,
    "lastMaint": "2024-02-06",
    "nextMaint": "2024-08-07",
    "history": [
     "2023-08-10 — Surchauffe répétée"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 2.34,
      "_noise": 0,
      "_phase": 4.808309476933175,
      "_omega": 4.931658388119528,
      "_lastEvent": 0,
      "value": 2.3
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 74.1,
      "_noise": 0,
      "_phase": 4.267691908233007,
      "_omega": 0.18119983637014234,
      "_lastEvent": 0,
      "value": 74.1
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 1657.5,
      "_noise": 0,
      "_phase": 4.372324615089099,
      "_omega": 1.502081350365632,
      "_lastEvent": 0,
      "value": 1657.5
     }
    ],
    "_wear": 0.9327506079905399
   },
   {
    "id": "CEN-12",
    "name": "Tour en L'Air",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 30.98,
    "z": 19.09,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "A",
    "age": 20,
    "lastMaint": "2024-05-25",
    "nextMaint": "2024-11-24",
    "history": [
     "2023-11-27 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 4.858857332422743,
      "_omega": 4.146851052886767,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 4.749300618576835,
      "_omega": 0.22525285402167128,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 1.5575235753013483,
      "_omega": 2.1821445442204253,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.15804290066576324
   },
   {
    "id": "CEN-13",
    "name": "La Rodeuse",
    "type": "Formage",
    "mtype": "generic",
    "x": 52.38,
    "z": 19.29,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 23,
    "lastMaint": "2024-05-01",
    "nextMaint": "2024-10-31",
    "history": [
     "2023-11-03 — Inspection préventive OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 1.8324407546243613,
      "_omega": 3.57404120771118,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 3.6639160943453035,
      "_omega": 0.2779034077944418,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 2.174162584590271,
      "_omega": 1.0028919931700826,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.15529385023693992
   },
   {
    "id": "CEN-14",
    "name": "Perceuse Radiale",
    "type": "Perçage",
    "mtype": "drill",
    "x": 37.85,
    "z": 20.81,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 28,
    "lastMaint": "2024-06-02",
    "nextMaint": "2024-12-02",
    "history": [
     "2023-12-05 — RAS — relevé conforme"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 0.6534680056061639,
      "_omega": 4.729189800274438,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 3.1680912410734625,
      "_omega": 0.21178259302257063,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 4.685135356983999,
      "_omega": 1.841731160789996,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.14108509970055588
   },
   {
    "id": "CEN-15",
    "name": "Rectifieuse Plane",
    "type": "Rectification",
    "mtype": "mill",
    "x": 26.38,
    "z": 31.26,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "B",
    "age": 17,
    "lastMaint": "2024-02-04",
    "nextMaint": "2024-08-05",
    "history": [
     "2023-08-08 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 1.7369522079071933,
      "_omega": 6.810509933095672,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 1.5122642737893761,
      "_omega": 0.26013167334210346,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 3.748885637337837,
      "_omega": 1.0825099470755366,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.1352186989802121
   },
   {
    "id": "CEN-16",
    "name": "Aléseuse Horizontale",
    "type": "Alésage",
    "mtype": "mill",
    "x": 37.04,
    "z": 32.06,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "A",
    "age": 26,
    "lastMaint": "2024-05-23",
    "nextMaint": "2024-11-22",
    "history": [
     "2023-11-25 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 0.3762434217311147,
      "_omega": 4.291141681689931,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 1.7731215655184724,
      "_omega": 0.19010600451773466,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 1.5657744651852041,
      "_omega": 1.8867851900618953,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.1583018132994866
   },
   {
    "id": "CEN-17",
    "name": "Rectifieuse Cylindrique",
    "type": "Rectification",
    "mtype": "mill",
    "x": 31.68,
    "z": 35.21,
    "w": 4,
    "d": 3.5,
    "status": "critical",
    "criticality": "B",
    "age": 24,
    "lastMaint": "2024-01-17",
    "nextMaint": "2024-07-18",
    "history": [
     "2023-07-21 — Surchauffe répétée"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 2.73,
      "_noise": 0,
      "_phase": 2.040317529942331,
      "_omega": 5.076956303981605,
      "_lastEvent": 0,
      "value": 2.7
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 79.95,
      "_noise": 0,
      "_phase": 0.29539530861658536,
      "_omega": 0.3675205152417328,
      "_lastEvent": 0,
      "value": 80
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 120.89999999999999,
      "_noise": 0,
      "_phase": 4.790592091520951,
      "_omega": 1.3436520450625604,
      "_lastEvent": 0,
      "value": 120.9
     }
    ],
    "_wear": 0.8675093287031204
   },
   {
    "id": "CEN-18",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 16.73,
    "z": 35.17,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 18,
    "lastMaint": "2024-02-19",
    "nextMaint": "2024-08-20",
    "history": [
     "2023-08-23 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 2.69583572156179,
      "_omega": 3.384840205759981,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 0.8892289768409394,
      "_omega": 0.2964604336517279,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 5.824854139600399,
      "_omega": 1.6632340258143898,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.14502041510835043
   },
   {
    "id": "CEN-19",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 22.29,
    "z": 38.22,
    "w": 5,
    "d": 3,
    "status": "critical",
    "criticality": "A",
    "age": 10,
    "lastMaint": "2024-05-27",
    "nextMaint": "2024-11-26",
    "history": [
     "2023-11-29 — Panne moteur — blocage"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 2.34,
      "_noise": 0,
      "_phase": 1.6571775310930974,
      "_omega": 6.535101868634332,
      "_lastEvent": 0,
      "value": 2.3
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 74.1,
      "_noise": 0,
      "_phase": 4.849806388244469,
      "_omega": 0.3373384593582158,
      "_lastEvent": 0,
      "value": 74.1
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 1657.5,
      "_noise": 0,
      "_phase": 4.902517017235649,
      "_omega": 0.9849200118435318,
      "_lastEvent": 0,
      "value": 1657.5
     }
    ],
    "_wear": 0.8711962647474597
   },
   {
    "id": "CEN-20",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 16.64,
    "z": 38.67,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 10,
    "lastMaint": "2024-05-26",
    "nextMaint": "2024-11-25",
    "history": [
     "2023-11-28 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 4.740372715310353,
      "_omega": 4.4729331678852,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 0.1015330547235779,
      "_omega": 0.17372423584735722,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 4.072916525575028,
      "_omega": 0.9451434510199733,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.15003670395111574
   },
   {
    "id": "CEN-21",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 26.41,
    "z": 41.72,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 10,
    "lastMaint": "2024-04-17",
    "nextMaint": "2024-10-17",
    "history": [
     "2023-10-20 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 4.8998430609574095,
      "_omega": 6.180717252921711,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 0.21755564125279098,
      "_omega": 0.3942540891134697,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 0.3850920874462038,
      "_omega": 1.5611977448976082,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.1395549045834075
   },
   {
    "id": "CEN-22",
    "name": "Rectifieuse Cylindrique",
    "type": "Rectification",
    "mtype": "mill",
    "x": 31.91,
    "z": 41.81,
    "w": 4,
    "d": 3.5,
    "status": "warn",
    "criticality": "A",
    "age": 11,
    "lastMaint": "2024-02-21",
    "nextMaint": "2024-08-22",
    "history": [
     "2023-08-25 — Jeu axial à surveiller"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.652,
      "_noise": 0,
      "_phase": 1.9834416447606171,
      "_omega": 6.653577148640197,
      "_lastEvent": 0,
      "value": 1.7
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 48.379999999999995,
      "_noise": 0,
      "_phase": 2.803195438467574,
      "_omega": 0.20316956871686448,
      "_lastEvent": 0,
      "value": 48.4
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 73.16,
      "_noise": 0,
      "_phase": 4.825772109223806,
      "_omega": 1.0220856660127036,
      "_lastEvent": 0,
      "value": 73.2
     }
    ],
    "_wear": 0.5249722279430755
   },
   {
    "id": "CEN-23",
    "name": "Tours pour Bobinage (Bobineuses)",
    "type": "Bobinage",
    "mtype": "lathe",
    "x": 52.11,
    "z": 42.19,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 6,
    "lastMaint": "2024-04-16",
    "nextMaint": "2024-10-16",
    "history": [
     "2023-10-19 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 5.53604249011906,
      "_omega": 6.598159097093564,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 0.6255346851923714,
      "_omega": 0.2927042015229148,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 2.264883564923595,
      "_omega": 1.8795876336690467,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.14141856081671184
   },
   {
    "id": "CEN-24",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 16.16,
    "z": 42.85,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 26,
    "lastMaint": "2024-03-03",
    "nextMaint": "2024-09-02",
    "history": [
     "2023-09-05 — RAS — relevé conforme"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 0.30197924782767316,
      "_omega": 5.580959617437737,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 1.8329286936804916,
      "_omega": 0.3149896883696649,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 3.4408398215682823,
      "_omega": 1.6338301220072733,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.1540826679946193
   },
   {
    "id": "CEN-25",
    "name": "Cisaille Papier Isolant",
    "type": "Découpe",
    "mtype": "saw",
    "x": 57.56,
    "z": 45.44,
    "w": 3.5,
    "d": 4,
    "status": "ok",
    "criticality": "A",
    "age": 27,
    "lastMaint": "2024-06-05",
    "nextMaint": "2024-12-05",
    "history": [
     "2023-12-08 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 22,
      "_noise": 0,
      "_phase": 4.366069256648212,
      "_omega": 0.9081558472161739,
      "_lastEvent": 0,
      "value": 22
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 35,
      "_noise": 0,
      "_phase": 4.615879356578631,
      "_omega": 0.2509361381348597,
      "_lastEvent": 0,
      "value": 35
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 410,
      "_noise": 0,
      "_phase": 0.6649123250868586,
      "_omega": 1.0140879034887968,
      "_lastEvent": 0,
      "value": 410
     }
    ],
    "_wear": 0.15962444518793725
   },
   {
    "id": "CEN-26",
    "name": "Meule pour Bobine Moteur",
    "type": "Meulage",
    "mtype": "generic",
    "x": 53.17,
    "z": 50.48,
    "w": 4,
    "d": 3,
    "status": "warn",
    "criticality": "A",
    "age": 23,
    "lastMaint": "2024-01-08",
    "nextMaint": "2024-07-09",
    "history": [
     "2023-07-12 — Résistance à surveiller"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1.18,
      "_noise": 0,
      "_phase": 0.06790259419186108,
      "_omega": 4.052046097233113,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 42.48,
      "_noise": 0,
      "_phase": 3.091389414137395,
      "_omega": 0.2467046429461516,
      "_lastEvent": 0,
      "value": 42.5
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 53.099999999999994,
      "_noise": 0,
      "_phase": 1.5948526863725432,
      "_omega": 1.5719393439602767,
      "_lastEvent": 0,
      "value": 53.1
     }
    ],
    "_wear": 0.5033536137235546
   },
   {
    "id": "CEN-27",
    "name": "Fraiseuse Universelle",
    "type": "Fraisage",
    "mtype": "mill",
    "x": 31.84,
    "z": 50.43,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "C",
    "age": 4,
    "lastMaint": "2024-02-06",
    "nextMaint": "2024-08-07",
    "history": [
     "2023-08-10 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 5.829160113351733,
      "_omega": 6.771639011601868,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 4.010215078203998,
      "_omega": 0.16855165522720314,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 2.1691221730294843,
      "_omega": 1.3232311148560725,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.14484070061061954
   },
   {
    "id": "CEN-28",
    "name": "Coupeuse Bois",
    "type": "Découpe bois",
    "mtype": "saw",
    "x": 58.47,
    "z": 51.04,
    "w": 3.5,
    "d": 4,
    "status": "ok",
    "criticality": "B",
    "age": 6,
    "lastMaint": "2024-03-14",
    "nextMaint": "2024-09-13",
    "history": [
     "2023-09-16 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 22,
      "_noise": 0,
      "_phase": 5.510048445868933,
      "_omega": 1.16862992258134,
      "_lastEvent": 0,
      "value": 22
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 35,
      "_noise": 0,
      "_phase": 2.2334962274036427,
      "_omega": 0.31242908665839425,
      "_lastEvent": 0,
      "value": 35
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 410,
      "_noise": 0,
      "_phase": 0.09036704493925088,
      "_omega": 1.8906570361923527,
      "_lastEvent": 0,
      "value": 410
     }
    ],
    "_wear": 0.15058446497058384
   },
   {
    "id": "CEN-29",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 16.73,
    "z": 51.96,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 13,
    "lastMaint": "2024-01-29",
    "nextMaint": "2024-07-30",
    "history": [
     "2023-08-02 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 0.12721050729704014,
      "_omega": 5.3024230348579735,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 0.3902030671640087,
      "_omega": 0.18589736582812047,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 4.915043637883455,
      "_omega": 0.9492268747218107,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.15578024763179443
   },
   {
    "id": "CEN-30",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 24.74,
    "z": 53.6,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 5,
    "lastMaint": "2024-05-22",
    "nextMaint": "2024-11-21",
    "history": [
     "2023-11-24 — Inspection préventive OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 4.916518577700377,
      "_omega": 3.2126804817961077,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 4.743676059841254,
      "_omega": 0.21745196992807198,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 6.1655223127014285,
      "_omega": 1.4024533436096187,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.14760772703030317
   },
   {
    "id": "CEN-31",
    "name": "Fraiseuse Universelle",
    "type": "Fraisage",
    "mtype": "mill",
    "x": 31.85,
    "z": 54.33,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "C",
    "age": 26,
    "lastMaint": "2024-06-04",
    "nextMaint": "2024-12-04",
    "history": [
     "2023-12-07 — Inspection préventive OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 0.8894557882503279,
      "_omega": 5.623388723100041,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 1.6980379188455235,
      "_omega": 0.32306850337722953,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 0.05307960158609093,
      "_omega": 1.0391150516091239,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.14378497977842644
   },
   {
    "id": "CEN-32",
    "name": "Cabine d'Évacuation gaz",
    "type": "Extraction gaz",
    "mtype": "vent",
    "x": 57.89,
    "z": 55.54,
    "w": 3,
    "d": 3,
    "status": "warn",
    "criticality": "C",
    "age": 26,
    "lastMaint": "2024-03-24",
    "nextMaint": "2024-09-23",
    "history": [
     "2023-09-26 — Vibration anormale détectée"
    ],
    "sensors": [
     {
      "label": "Débit",
      "unit": "m³/h",
      "base": 2400,
      "kind": "load",
      "_mean": 2832,
      "_noise": 0,
      "_phase": 2.232373653231284,
      "_omega": 1.3863127319579522,
      "_lastEvent": 0,
      "value": 2832
     },
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.6,
      "kind": "vib",
      "_mean": 0.708,
      "_noise": 0,
      "_phase": 4.730861121184285,
      "_omega": 4.882404721455187,
      "_lastEvent": 0,
      "value": 0.7
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 29,
      "kind": "temp",
      "_mean": 34.22,
      "_noise": 0,
      "_phase": 1.0734574154925731,
      "_omega": 0.39221651765512716,
      "_lastEvent": 0,
      "value": 34.2
     }
    ],
    "_wear": 0.5101039134459492
   },
   {
    "id": "CEN-33",
    "name": "Presse Électrique",
    "type": "Pressage",
    "mtype": "press",
    "x": 53.39,
    "z": 55.29,
    "w": 4,
    "d": 4,
    "status": "danger",
    "criticality": "A",
    "age": 23,
    "lastMaint": "2024-01-02",
    "nextMaint": "2024-07-03",
    "history": [
     "2023-07-06 — Bielle usée"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 217.5,
      "_noise": 0,
      "_phase": 3.7485479760225537,
      "_omega": 2.075624838138259,
      "_lastEvent": 0,
      "value": 217.5
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 66,
      "_noise": 0,
      "_phase": 0.1450896054670351,
      "_omega": 0.28924736928228456,
      "_lastEvent": 0,
      "value": 66
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 57,
      "_noise": 0,
      "_phase": 4.32428452444931,
      "_omega": 1.6386666677128288,
      "_lastEvent": 0,
      "value": 57
     }
    ],
    "_wear": 0.702953862299772
   },
   {
    "id": "CEN-34",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 17.04,
    "z": 55.46,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "A",
    "age": 4,
    "lastMaint": "2024-03-24",
    "nextMaint": "2024-09-23",
    "history": [
     "2023-09-26 — Inspection préventive OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 2.6559671107469716,
      "_omega": 5.9470943533452445,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 5.326380548372917,
      "_omega": 0.25058286825647275,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 5.527750979368274,
      "_omega": 1.6960288760126048,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.1433923960499147
   },
   {
    "id": "CEN-35",
    "name": "Fraiseuse",
    "type": "Fraisage",
    "mtype": "mill",
    "x": 37.12,
    "z": 56.89,
    "w": 4,
    "d": 3.5,
    "status": "critical",
    "criticality": "B",
    "age": 10,
    "lastMaint": "2024-03-31",
    "nextMaint": "2024-09-30",
    "history": [
     "2023-04-06 — Panne moteur — blocage",
     "2023-10-03 — Surchauffe répétée"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 2.73,
      "_noise": 0,
      "_phase": 1.0105778562910388,
      "_omega": 3.559322978326473,
      "_lastEvent": 0,
      "value": 2.7
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 79.95,
      "_noise": 0,
      "_phase": 4.1701691937393015,
      "_omega": 0.3229461321642926,
      "_lastEvent": 0,
      "value": 80
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 120.89999999999999,
      "_noise": 0,
      "_phase": 2.0897883943376945,
      "_omega": 1.34833456308824,
      "_lastEvent": 0,
      "value": 120.9
     }
    ],
    "_wear": 0.9970412914337623
   },
   {
    "id": "CEN-36",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 24.74,
    "z": 57.01,
    "w": 5,
    "d": 3,
    "status": "critical",
    "criticality": "C",
    "age": 23,
    "lastMaint": "2024-02-03",
    "nextMaint": "2024-08-04",
    "history": [
     "2023-02-08 — Surchauffe répétée",
     "2023-08-07 — Panne moteur — blocage"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 2.34,
      "_noise": 0,
      "_phase": 3.0003599318999323,
      "_omega": 6.397657600943413,
      "_lastEvent": 0,
      "value": 2.3
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 74.1,
      "_noise": 0,
      "_phase": 2.448396436878934,
      "_omega": 0.208491811312509,
      "_lastEvent": 0,
      "value": 74.1
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 1657.5,
      "_noise": 0,
      "_phase": 4.561171942598423,
      "_omega": 1.4603333676089334,
      "_lastEvent": 0,
      "value": 1657.5
     }
    ],
    "_wear": 1.029867016730917
   },
   {
    "id": "CEN-37",
    "name": "Fraiseuse Universelle",
    "type": "Fraisage",
    "mtype": "mill",
    "x": 31.86,
    "z": 58.33,
    "w": 4,
    "d": 3.5,
    "status": "warn",
    "criticality": "A",
    "age": 6,
    "lastMaint": "2024-02-16",
    "nextMaint": "2024-08-17",
    "history": [
     "2023-02-21 — Jeu axial à surveiller",
     "2023-08-20 — Jeu axial à surveiller"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.652,
      "_noise": 0,
      "_phase": 0.23907071434342417,
      "_omega": 6.234249705676601,
      "_lastEvent": 0,
      "value": 1.7
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 48.379999999999995,
      "_noise": 0,
      "_phase": 5.544731712899671,
      "_omega": 0.15224745801525447,
      "_lastEvent": 0,
      "value": 48.4
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 73.16,
      "_noise": 0,
      "_phase": 3.628792920891553,
      "_omega": 1.7838800178275824,
      "_lastEvent": 0,
      "value": 73.2
     }
    ],
    "_wear": 0.5456161604755467
   },
   {
    "id": "CEN-38",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 16.73,
    "z": 58.89,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 16,
    "lastMaint": "2024-04-23",
    "nextMaint": "2024-10-23",
    "history": [
     "2023-10-26 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 2.929966583456213,
      "_omega": 6.766521083893098,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 2.0533694816087147,
      "_omega": 0.21340905678091485,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 0.20973824844607386,
      "_omega": 2.0900344722478845,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.13999026342267343
   },
   {
    "id": "CEN-39",
    "name": "Sableuse Pièces Métalliques",
    "type": "Sablage",
    "mtype": "generic",
    "x": 0.36,
    "z": 60.06,
    "w": 4,
    "d": 3,
    "status": "warn",
    "criticality": "A",
    "age": 15,
    "lastMaint": "2024-01-15",
    "nextMaint": "2024-07-16",
    "history": [
     "2023-07-19 — Température en hausse"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1.18,
      "_noise": 0,
      "_phase": 3.1887949594699814,
      "_omega": 3.715891910215151,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 42.48,
      "_noise": 0,
      "_phase": 0.37474044726377415,
      "_omega": 0.18274586833035233,
      "_lastEvent": 0,
      "value": 42.5
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 53.099999999999994,
      "_noise": 0,
      "_phase": 0.9936218437352444,
      "_omega": 2.1139748293908998,
      "_lastEvent": 0,
      "value": 53.1
     }
    ],
    "_wear": 0.5288523807132084
   },
   {
    "id": "CEN-40",
    "name": "Meuleuse",
    "type": "Meulage",
    "mtype": "mill",
    "x": 54.77,
    "z": 60.25,
    "w": 4,
    "d": 3.5,
    "status": "danger",
    "criticality": "A",
    "age": 17,
    "lastMaint": "2024-05-14",
    "nextMaint": "2024-11-13",
    "history": [
     "2023-11-16 — Fuite hydraulique détectée"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 2.0999999999999996,
      "_noise": 0,
      "_phase": 0.1720787777117683,
      "_omega": 6.70875668447507,
      "_lastEvent": 0,
      "value": 2.1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 61.5,
      "_noise": 0,
      "_phase": 4.443186117255848,
      "_omega": 0.21761017784444064,
      "_lastEvent": 0,
      "value": 61.5
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 93,
      "_noise": 0,
      "_phase": 3.037541528326149,
      "_omega": 1.2434134259358471,
      "_lastEvent": 0,
      "value": 93
     }
    ],
    "_wear": 0.7128769240366337
   },
   {
    "id": "CEN-41",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 24.74,
    "z": 60.44,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 20,
    "lastMaint": "2024-03-19",
    "nextMaint": "2024-09-18",
    "history": [
     "2023-09-21 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 4.05589306269331,
      "_omega": 4.420886960742962,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 4.671273544846468,
      "_omega": 0.2544401394095761,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 3.685101416112386,
      "_omega": 1.322386395116908,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.1456477603058352
   },
   {
    "id": "CEN-42",
    "name": "Banc d'essai",
    "type": "Essais",
    "mtype": "generic",
    "x": 6.84,
    "z": 61.17,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 20,
    "lastMaint": "2024-01-26",
    "nextMaint": "2024-07-27",
    "history": [
     "2023-07-30 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 1.6394054747709579,
      "_omega": 4.010472939789196,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 3.2257470074797285,
      "_omega": 0.22833762699080418,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 6.015866796402934,
      "_omega": 1.1723764934225045,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.14914881272738467
   },
   {
    "id": "CEN-43",
    "name": "Fraiseuse Universelle",
    "type": "Fraisage",
    "mtype": "mill",
    "x": 31.85,
    "z": 62.46,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "A",
    "age": 19,
    "lastMaint": "2024-06-17",
    "nextMaint": "2024-12-17",
    "history": [
     "2023-12-20 — RAS — relevé conforme"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 6.0165870766323595,
      "_omega": 4.307288583754181,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 1.863568639744777,
      "_omega": 0.3083630361632287,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 1.52445995272856,
      "_omega": 1.2912506916707014,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.14550507632674048
   },
   {
    "id": "CEN-44",
    "name": "Perceuse Électrique",
    "type": "Perçage",
    "mtype": "drill",
    "x": 59.27,
    "z": 63.38,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 27,
    "lastMaint": "2024-03-11",
    "nextMaint": "2024-09-10",
    "history": [
     "2023-09-13 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 4.60264473979115,
      "_omega": 6.227700316705251,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 2.436133829723925,
      "_omega": 0.23495166841689083,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 5.780482926245865,
      "_omega": 1.1710478773692135,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.15822221671865305
   },
   {
    "id": "CEN-45",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 24.76,
    "z": 63.94,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 23,
    "lastMaint": "2024-01-15",
    "nextMaint": "2024-07-16",
    "history": [
     "2023-07-19 — Inspection préventive OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 6.141826505248222,
      "_omega": 3.971837047768874,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 0.06454911467407222,
      "_omega": 0.20585041707812937,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 5.972481381693945,
      "_omega": 2.109336567236048,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.1355380085576827
   },
   {
    "id": "CEN-46",
    "name": "Presse Hydraulique",
    "type": "Pressage",
    "mtype": "press",
    "x": 7.31,
    "z": 65.33,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "C",
    "age": 7,
    "lastMaint": "2024-02-13",
    "nextMaint": "2024-08-14",
    "history": [
     "2023-08-17 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 5.56651894754004,
      "_omega": 2.1883448780193575,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 2.890731680313916,
      "_omega": 0.26042043485726973,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 2.984104575501594,
      "_omega": 1.0807721527934318,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.146877269217678
   },
   {
    "id": "CEN-47",
    "name": "Équilibreuse",
    "type": "Équilibrage",
    "mtype": "generic",
    "x": 25.26,
    "z": 67.37,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 13,
    "lastMaint": "2024-01-24",
    "nextMaint": "2024-07-25",
    "history": [
     "2023-07-28 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 5.046567299986008,
      "_omega": 4.229842138376595,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 2.767549229647873,
      "_omega": 0.21505934858153486,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 0.9991114268467172,
      "_omega": 1.9000883688307084,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.16082479563208707
   },
   {
    "id": "CEN-48",
    "name": "Tour Parallèle",
    "type": "Tournage",
    "mtype": "lathe",
    "x": 17.21,
    "z": 67.48,
    "w": 5,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 28,
    "lastMaint": "2024-06-06",
    "nextMaint": "2024-12-06",
    "history": [
     "2023-12-09 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.2,
      "kind": "vib",
      "_mean": 1.2,
      "_noise": 0,
      "_phase": 2.0031484142807976,
      "_omega": 5.155544765690481,
      "_lastEvent": 0,
      "value": 1.2
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 38,
      "kind": "temp",
      "_mean": 38,
      "_noise": 0,
      "_phase": 2.797581485435587,
      "_omega": 0.3067387849354925,
      "_lastEvent": 0,
      "value": 38
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 850,
      "kind": "rpm",
      "_mean": 850,
      "_noise": 0,
      "_phase": 3.861149708210628,
      "_omega": 1.7369441059955177,
      "_lastEvent": 0,
      "value": 850
     }
    ],
    "_wear": 0.15440902439338594
   },
   {
    "id": "CEN-49",
    "name": "Fraiseuse Universelle",
    "type": "Fraisage",
    "mtype": "mill",
    "x": 31.86,
    "z": 67.69,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "C",
    "age": 12,
    "lastMaint": "2024-04-17",
    "nextMaint": "2024-10-17",
    "history": [
     "2023-10-20 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 0.4884014420537394,
      "_omega": 3.1667102516122827,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 0.44214677575481787,
      "_omega": 0.16273209108378217,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 3.331387270174915,
      "_omega": 1.1174371202554667,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.13817030543566683
   },
   {
    "id": "CEN-50",
    "name": "Banc d'essai",
    "type": "Essais",
    "mtype": "generic",
    "x": 0.3,
    "z": 67.56,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 26,
    "lastMaint": "2024-05-17",
    "nextMaint": "2024-11-16",
    "history": [
     "2023-11-19 — RAS — relevé conforme"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 0.7299226149868804,
      "_omega": 3.9170223400033155,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 1.9067489178394812,
      "_omega": 0.21799689524661428,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 5.429799012537547,
      "_omega": 1.4625039618661377,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.1413557537943093
   },
   {
    "id": "CEN-51",
    "name": "Perceuse Électrique",
    "type": "Perçage",
    "mtype": "drill",
    "x": 7.7,
    "z": 69.83,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 19,
    "lastMaint": "2024-02-28",
    "nextMaint": "2024-08-29",
    "history": [
     "2023-09-01 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 0.15299682124519973,
      "_omega": 3.9988084135978186,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 4.449325917970151,
      "_omega": 0.30305415053359597,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 3.362920037135788,
      "_omega": 1.9324784989150103,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.16387673982156073
   },
   {
    "id": "CEN-52",
    "name": "Mortaiseuse",
    "type": "Mortaisage",
    "mtype": "mill",
    "x": 32.89,
    "z": 71.69,
    "w": 4,
    "d": 3.5,
    "status": "ok",
    "criticality": "B",
    "age": 3,
    "lastMaint": "2024-06-07",
    "nextMaint": "2024-12-07",
    "history": [
     "2023-12-10 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.4,
      "_noise": 0,
      "_phase": 3.4017414911096595,
      "_omega": 3.7401305803592484,
      "_lastEvent": 0,
      "value": 1.4
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 41,
      "_noise": 0,
      "_phase": 0.018305638680577038,
      "_omega": 0.18370902098147968,
      "_lastEvent": 0,
      "value": 41
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 62,
      "_noise": 0,
      "_phase": 2.5157803751955,
      "_omega": 1.924709743609914,
      "_lastEvent": 0,
      "value": 62
     }
    ],
    "_wear": 0.164775875805644
   },
   {
    "id": "CEN-53",
    "name": "Banc d'essai",
    "type": "Essais",
    "mtype": "generic",
    "x": 0.3,
    "z": 71.06,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "A",
    "age": 9,
    "lastMaint": "2024-01-03",
    "nextMaint": "2024-07-04",
    "history": [
     "2023-07-07 — Graissage effectué"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 5.995437911169472,
      "_omega": 4.32830780618089,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 5.670680766150891,
      "_omega": 0.30609929498964683,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 5.252414395430202,
      "_omega": 1.6984748243348777,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.14245212902124585
   },
   {
    "id": "CEN-54",
    "name": "Ponceuse pour Bois",
    "type": "Ponçage",
    "mtype": "generic",
    "x": 48.17,
    "z": 72.07,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 9,
    "lastMaint": "2024-01-21",
    "nextMaint": "2024-07-22",
    "history": [
     "2023-07-25 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 4.592382044077438,
      "_omega": 5.142338778062897,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 5.98584527033235,
      "_omega": 0.22532972747763136,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 5.762142163693394,
      "_omega": 1.5451692891765976,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.1580016612459966
   },
   {
    "id": "CEN-55",
    "name": "Brosses Métalliques Électriques",
    "type": "Décaper",
    "mtype": "generic",
    "x": 7.29,
    "z": 73.24,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 23,
    "lastMaint": "2024-03-14",
    "nextMaint": "2024-09-13",
    "history": [
     "2023-09-16 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 2.686861823737598,
      "_omega": 3.07722696253054,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 2.1792190910690077,
      "_omega": 0.24996671164429796,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 4.0795774110962855,
      "_omega": 1.1620339051295057,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.14143224414771924
   },
   {
    "id": "CEN-56",
    "name": "Rodeuse",
    "type": "Formage",
    "mtype": "generic",
    "x": 1.21,
    "z": 74.46,
    "w": 4,
    "d": 3,
    "status": "danger",
    "criticality": "A",
    "age": 25,
    "lastMaint": "2024-04-26",
    "nextMaint": "2024-10-26",
    "history": [
     "2023-10-29 — Roulement à remplacer"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1.5,
      "_noise": 0,
      "_phase": 2.217228550372557,
      "_omega": 3.6338330584509673,
      "_lastEvent": 0,
      "value": 1.5
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 54,
      "_noise": 0,
      "_phase": 2.9952735324324995,
      "_omega": 0.36913011965574943,
      "_lastEvent": 0,
      "value": 54
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 67.5,
      "_noise": 0,
      "_phase": 2.277449725546464,
      "_omega": 1.812372306736703,
      "_lastEvent": 0,
      "value": 67.5
     }
    ],
    "_wear": 0.7260116728121189
   },
   {
    "id": "CEN-57",
    "name": "Banc d'essai",
    "type": "Essais",
    "mtype": "generic",
    "x": 57.44,
    "z": 73.81,
    "w": 4,
    "d": 3,
    "status": "danger",
    "criticality": "B",
    "age": 15,
    "lastMaint": "2024-01-07",
    "nextMaint": "2024-07-08",
    "history": [
     "2023-01-12 — Surcharge répétée",
     "2023-07-11 — Fuite hydraulique détectée"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1.5,
      "_noise": 0,
      "_phase": 1.8336926441510886,
      "_omega": 5.178881121127946,
      "_lastEvent": 0,
      "value": 1.5
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 54,
      "_noise": 0,
      "_phase": 3.1439814521139176,
      "_omega": 0.2307255650005983,
      "_lastEvent": 0,
      "value": 54
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 67.5,
      "_noise": 0,
      "_phase": 5.191909725265756,
      "_omega": 1.1057459353906869,
      "_lastEvent": 0,
      "value": 67.5
     }
    ],
    "_wear": 0.7572171473961294
   }
  ]
 },
 {
  "name": "Atelier DCA",
  "surface": "2 937 m²",
  "w": 52.22,
  "d": 67.12,
  "zones": [
   {
    "name": "Atelier Chaudronnerie",
    "x": 0,
    "z": 13.26,
    "w": 52.22,
    "d": 44.47,
    "color": 794416,
    "area": "S = 2 937,31 m²"
   },
   {
    "name": "Sanitaires",
    "x": 3.35,
    "z": 58.49,
    "w": 5.3,
    "d": 5.3,
    "color": 727077,
    "area": "S = 28,38 m²"
   },
   {
    "name": "Vestiaires",
    "x": 10.11,
    "z": 59.05,
    "w": 6.85,
    "d": 6.85,
    "color": 661026,
    "area": "S = 46,88 m²"
   },
   {
    "name": "Magasin",
    "x": 40.12,
    "z": 0.2,
    "w": 11.9,
    "d": 11.9,
    "color": 793902,
    "area": "S = 142,25 m²"
   }
  ],
  "equipment": [
   {
    "id": "DCA-01",
    "name": "Plyeuse",
    "type": "Pliage",
    "mtype": "press",
    "x": 30.48,
    "z": 13.08,
    "w": 4,
    "d": 4,
    "status": "warn",
    "criticality": "A",
    "age": 13,
    "lastMaint": "2024-03-25",
    "nextMaint": "2024-09-24",
    "history": [
     "2023-09-27 — Disque à 60% d'usure"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 171.1,
      "_noise": 0,
      "_phase": 6.206288205242508,
      "_omega": 1.594954312016134,
      "_lastEvent": 0,
      "value": 171.1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 51.919999999999995,
      "_noise": 0,
      "_phase": 5.956536997809427,
      "_omega": 0.2411188198526476,
      "_lastEvent": 0,
      "value": 51.9
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 44.839999999999996,
      "_noise": 0,
      "_phase": 4.038510804388541,
      "_omega": 1.7014551054249192,
      "_lastEvent": 0,
      "value": 44.8
     }
    ],
    "_wear": 0.4712005084925293
   },
   {
    "id": "DCA-02",
    "name": "Tronçonneuse",
    "type": "Découpe",
    "mtype": "saw",
    "x": 19.55,
    "z": 42.88,
    "w": 3.5,
    "d": 4,
    "status": "danger",
    "criticality": "A",
    "age": 5,
    "lastMaint": "2024-04-07",
    "nextMaint": "2024-10-07",
    "history": [
     "2023-10-10 — Fuite hydraulique détectée"
    ],
    "sensors": [
     {
      "label": "Vitesse lame",
      "unit": "m/s",
      "base": 22,
      "kind": "rpm",
      "_mean": 33,
      "_noise": 0,
      "_phase": 3.581064066735169,
      "_omega": 1.8607626534605475,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 35,
      "kind": "temp",
      "_mean": 52.5,
      "_noise": 0,
      "_phase": 1.2342586068184844,
      "_omega": 0.235665900728907,
      "_lastEvent": 0,
      "value": 52.5
     },
     {
      "label": "Tension",
      "unit": "N",
      "base": 410,
      "kind": "load",
      "_mean": 615,
      "_noise": 0,
      "_phase": 2.2523813239461634,
      "_omega": 2.189451184967238,
      "_lastEvent": 0,
      "value": 615
     }
    ],
    "_wear": 0.7775893879840718
   },
   {
    "id": "DCA-03",
    "name": "Rouleuse",
    "type": "Formage métal",
    "mtype": "mill",
    "x": 28.84,
    "z": 43.78,
    "w": 4,
    "d": 3.5,
    "status": "warn",
    "criticality": "B",
    "age": 25,
    "lastMaint": "2024-03-25",
    "nextMaint": "2024-09-24",
    "history": [
     "2023-03-31 — Résistance à surveiller",
     "2023-09-27 — Température en hausse"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1.4,
      "kind": "vib",
      "_mean": 1.652,
      "_noise": 0,
      "_phase": 0.18542631071201315,
      "_omega": 6.8499167223958,
      "_lastEvent": 0,
      "value": 1.7
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 41,
      "kind": "temp",
      "_mean": 48.379999999999995,
      "_noise": 0,
      "_phase": 0.07750943387132356,
      "_omega": 0.22047232210102038,
      "_lastEvent": 0,
      "value": 48.4
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 62,
      "kind": "load",
      "_mean": 73.16,
      "_noise": 0,
      "_phase": 0.9360379427264929,
      "_omega": 1.3308219054454253,
      "_lastEvent": 0,
      "value": 73.2
     }
    ],
    "_wear": 0.5107752212143145
   },
   {
    "id": "DCA-04",
    "name": "Perceuse Sur-Bâtis",
    "type": "Perçage",
    "mtype": "drill",
    "x": 10.64,
    "z": 49.31,
    "w": 3,
    "d": 3,
    "status": "ok",
    "criticality": "C",
    "age": 7,
    "lastMaint": "2024-06-11",
    "nextMaint": "2024-12-11",
    "history": [
     "2023-12-14 — Inspection préventive OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 0.9,
      "kind": "vib",
      "_mean": 0.9,
      "_noise": 0,
      "_phase": 5.282023063302655,
      "_omega": 4.392009689308654,
      "_lastEvent": 0,
      "value": 0.9
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 33,
      "kind": "temp",
      "_mean": 33,
      "_noise": 0,
      "_phase": 1.9517162310173908,
      "_omega": 0.3334455334222339,
      "_lastEvent": 0,
      "value": 33
     },
     {
      "label": "RPM",
      "unit": "tr/min",
      "base": 1200,
      "kind": "rpm",
      "_mean": 1200,
      "_noise": 0,
      "_phase": 4.407124017691025,
      "_omega": 1.082130995602801,
      "_lastEvent": 0,
      "value": 1200
     }
    ],
    "_wear": 0.14414258052753412
   },
   {
    "id": "DCA-05",
    "name": "Limeuse à Roche",
    "type": "Limage",
    "mtype": "generic",
    "x": 21.44,
    "z": 50.82,
    "w": 4,
    "d": 3,
    "status": "ok",
    "criticality": "B",
    "age": 19,
    "lastMaint": "2024-06-19",
    "nextMaint": "2024-12-19",
    "history": [
     "2023-12-22 — Lame vérifiée OK"
    ],
    "sensors": [
     {
      "label": "Vibration",
      "unit": "mm/s",
      "base": 1,
      "kind": "vib",
      "_mean": 1,
      "_noise": 0,
      "_phase": 5.983165896202592,
      "_omega": 4.522163325292578,
      "_lastEvent": 0,
      "value": 1
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 36,
      "kind": "temp",
      "_mean": 36,
      "_noise": 0,
      "_phase": 0.48914026274757894,
      "_omega": 0.20034146470028752,
      "_lastEvent": 0,
      "value": 36
     },
     {
      "label": "Charge",
      "unit": "%",
      "base": 45,
      "kind": "load",
      "_mean": 45,
      "_noise": 0,
      "_phase": 4.904051869128343,
      "_omega": 1.7328396700041127,
      "_lastEvent": 0,
      "value": 45
     }
    ],
    "_wear": 0.1487678829225896
   },
   {
    "id": "DCA-06",
    "name": "Guillotine Électrique",
    "type": "Découpe",
    "mtype": "press",
    "x": 29.14,
    "z": 53.07,
    "w": 4,
    "d": 4,
    "status": "ok",
    "criticality": "C",
    "age": 27,
    "lastMaint": "2024-04-08",
    "nextMaint": "2024-10-08",
    "history": [
     "2023-10-11 — Alignement contrôlé"
    ],
    "sensors": [
     {
      "label": "Pression",
      "unit": "bar",
      "base": 145,
      "kind": "load",
      "_mean": 145,
      "_noise": 0,
      "_phase": 5.982051076559141,
      "_omega": 1.4463871142557079,
      "_lastEvent": 0,
      "value": 145
     },
     {
      "label": "Température",
      "unit": "°C",
      "base": 44,
      "kind": "temp",
      "_mean": 44,
      "_noise": 0,
      "_phase": 0.5546535783392161,
      "_omega": 0.2521207580602566,
      "_lastEvent": 0,
      "value": 44
     },
     {
      "label": "Cycles/h",
      "unit": "#",
      "base": 38,
      "kind": "rpm",
      "_mean": 38,
      "_noise": 0,
      "_phase": 4.327406845260877,
      "_omega": 1.183042915862289,
      "_lastEvent": 0,
      "value": 38
     }
    ],
    "_wear": 0.15651882025382416
   }
  ]
 }
];

// Sanity inventory (plan-derived; see tools/plan_layout/README.md)
export const PLAN_META = {
  plan: 'P-01', ind: '01',
  dates: { 'Atelier DIS': '12/05/2024', 'Atelier DLOG': '12/05/2024',
           'Atelier DCA': '12/05/2024', 'Atelier Centrale': '01/04/2024' },
  machines: { 'Atelier DIS': 29, 'Atelier DLOG': 6, 'Atelier Centrale': 57, 'Atelier DCA': 6 },
  zones: { 'Atelier DIS': 8, 'Atelier DLOG': 12, 'Atelier Centrale': 10, 'Atelier DCA': 4 },
  positions: 'approximate (OCR)',
  states: 'simulated',
} as const;

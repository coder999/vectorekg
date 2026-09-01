"""Generate the site's vectorcardiogram datasets.

Two sources:
  * PTB      -- records the Frank XYZ leads directly, so X/Y/Z are measured.
  * PTB-XL   -- 12-lead only, so XYZ is derived with the Kors regression
                transform. Validated against PTB's simultaneous Frank leads
                at r = 0.96 (X), 0.98 (Y), 0.84 (Z); see validate_kors.py.

Both are high-pass filtered at 0.5 Hz first: PTB in particular has heavy
baseline wander, which would otherwise drag the whole loop around the
scene instead of leaving it centred on the origin.

Orientation: Frank +Y is INFERIOR and +Z is POSTERIOR, but the scene draws
y upward and puts V1 (anterior) at +z. So scene = (+X, -Y, -Z).
"""
import json
import os
import pathlib

import numpy as np
import wfdb
from scipy.signal import butter, filtfilt

# Repo-relative, so this runs from a clone anywhere.
OUT = str(pathlib.Path(__file__).resolve().parent.parent / "htdocs" / "js" / "data")

KORS = np.array([
    [ 0.38, -0.07, -0.13,  0.05, -0.01,  0.14,  0.06,  0.54],
    [-0.07,  0.93,  0.06, -0.02, -0.05,  0.06, -0.17,  0.13],
    [ 0.11, -0.23, -0.43, -0.06, -0.14, -0.20, -0.11,  0.31],
])
KORS_LEADS = ["i", "ii", "v1", "v2", "v3", "v4", "v5", "v6"]

SCALE = 30.0     # mV -> scene units, the same for every recording so
                 # amplitudes stay comparable between them
SECONDS = 10
TARGET_HZ = 250  # 4 ms per frame, matching the original 2012 tracing

# key, source, record locator, label, meta
RECORDS = [
    # Chosen for a textbook-normal frontal QRS axis (46 deg, balanced X/Y),
    # since this is the reference the other loops get compared against.
    ("normal",  "ptb",   ("patient150", "s0287lre"),
     "Healthy control",              "patient150/s0287lre"),
    ("acutemi", "ptb",   ("patient001", "s0010_re"),
     "Acute infero-lateral MI",      "81F · recorded Frank leads"),

    ("lbbb",    "ptbxl", "records500/10000/10709_hr",
     "Complete LBBB",                "64M"),
    ("rbbb",    "ptbxl", "records500/13000/13015_hr",
     "Complete RBBB",                "87M"),
    ("afib",    "ptbxl", "records500/12000/12542_hr",
     "Atrial fibrillation",          "83F"),
    ("aflutter","ptbxl", "records500/01000/01773_hr",
     "Atrial flutter",               "65M"),
    ("stemi",   "ptbxl", "records500/01000/01063_hr",
     "Acute MI, ST elevation",       "69M · anteroseptal + infero-lateral"),
    ("lvh",     "ptbxl", "records500/10000/10287_hr",
     "Left ventricular hypertrophy", "77F"),
    ("wpw",     "ptbxl", "records500/10000/10053_hr",
     "WPW pre-excitation",           "27F"),
]


def highpass(sig, fs, cut=0.5):
    b, a = butter(2, cut / (fs / 2), btype="high")
    return filtfilt(b, a, sig, axis=-1)


def xyz_from_ptb(pat, name):
    r = wfdb.rdrecord(name, pn_dir="ptbdb/" + pat)
    idx = {n: i for i, n in enumerate(r.sig_name)}
    sig = np.vstack([r.p_signal[:, idx[l]] for l in ("vx", "vy", "vz")])
    sig = sig[:, np.isfinite(sig).all(axis=0)]
    return sig, r.fs, r.comments


def xyz_from_ptbxl(path):
    d, name = os.path.split(path)
    r = wfdb.rdrecord(name, pn_dir="ptb-xl/1.0.3/" + d)
    idx = {n.lower(): i for i, n in enumerate(r.sig_name)}
    src = np.vstack([r.p_signal[:, idx[l]] for l in KORS_LEADS])
    src = src[:, np.isfinite(src).all(axis=0)]
    return KORS @ src, r.fs, r.comments


os.makedirs(OUT, exist_ok=True)
manifest = []

for key, source, loc, label, meta in RECORDS:
    if source == "ptb":
        sig, fs, comments = xyz_from_ptb(*loc)
        derived = False
    else:
        sig, fs, comments = xyz_from_ptbxl(loc)
        derived = True

    sig = highpass(sig, fs)

    step = max(1, int(round(fs / TARGET_HZ)))
    sig = sig[:, : int(SECONDS * fs) : step]

    x, y, z = sig * SCALE
    # Frank -> scene: +Y is inferior and +Z posterior; the scene draws y up
    # and puts anterior at +z.
    pts = [[i * 4, round(float(x[i]), 2), round(float(-y[i]), 2), round(float(-z[i]), 2)]
           for i in range(sig.shape[1])]

    body = ",\n".join("[" + ",".join(str(v) for v in p) + "]" for p in pts)
    js = (f"/* {label} -- {meta}. "
          f"{'Kors-derived from the 12-lead' if derived else 'Recorded Frank XYZ leads'}. */\n"
          f"window.VCG_DATA = window.VCG_DATA || {{}};\n"
          f"window.VCG_DATA['{key}'] = [\n{body}\n];\n")
    with open(f"{OUT}/{key}.js", "w") as f:
        f.write(js)

    peak = float(np.max(np.sqrt((sig * SCALE) ** 2).sum(axis=0) ** 0.5))
    size = os.path.getsize(f"{OUT}/{key}.js") / 1024
    manifest.append((key, label, len(pts), round(peak, 1), round(size, 1)))
    print(f"{key:<9} {label:<30} {len(pts):>5} pts  peak~{peak:>6.1f}  {size:>6.1f} KB")

print("\ntotal:", round(sum(m[4] for m in manifest), 1), "KB across", len(manifest), "files")
print(json.dumps([m[0] for m in manifest]))

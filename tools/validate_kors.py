"""Validate the Kors regression transform against ground truth.

PTB records BOTH the 12-lead ECG and the real Frank XYZ leads
simultaneously, so deriving XYZ from the 12-lead and correlating against
the recorded Frank leads measures how good the transform actually is.

PTB has heavy baseline wander, which would dominate a raw correlation, so
both signals are high-pass filtered (0.5 Hz) before comparing.
"""
import numpy as np
import wfdb
from scipy.signal import butter, filtfilt

KORS = np.array([
    [ 0.38, -0.07, -0.13,  0.05, -0.01,  0.14,  0.06,  0.54],  # X
    [-0.07,  0.93,  0.06, -0.02, -0.05,  0.06, -0.17,  0.13],  # Y
    [ 0.11, -0.23, -0.43, -0.06, -0.14, -0.20, -0.11,  0.31],  # Z
])
KORS_LEADS = ["i", "ii", "v1", "v2", "v3", "v4", "v5", "v6"]


def highpass(sig, fs, cut=0.5):
    b, a = butter(2, cut / (fs / 2), btype="high")
    return filtfilt(b, a, sig, axis=-1)


def load(rec):
    pat, name = rec.split("/")
    r = wfdb.rdrecord(name, pn_dir="ptbdb/" + pat)
    idx = {n: i for i, n in enumerate(r.sig_name)}
    truth = np.vstack([r.p_signal[:, idx[l]] for l in ("vx", "vy", "vz")])
    src = np.vstack([r.p_signal[:, idx[l]] for l in KORS_LEADS])
    # drop samples where anything is NaN
    ok = np.isfinite(truth).all(axis=0) & np.isfinite(src).all(axis=0)
    return truth[:, ok], src[:, ok], r.fs


RECORDS = [
    ("patient001/s0010_re", "acute infero-lateral MI"),
    ("patient122/s0312lre", "healthy control"),
    ("patient169/s0328lre", "healthy control"),
    ("patient182/s0308lre", "healthy control"),
    ("patient150/s0287lre", "healthy control"),
    ("patient233/s0459_re", "healthy control"),
]

print("Kors-derived XYZ vs. recorded Frank leads (0.5 Hz high-pass):\n")
print(f"{'record':<22} {'note':<24} {'r(X)':>6} {'r(Y)':>6} {'r(Z)':>6}")
print("-" * 68)

allr = []
for rec, note in RECORDS:
    try:
        truth, src, fs = load(rec)
    except Exception as e:
        print(f"{rec:<22} SKIP ({type(e).__name__})")
        continue
    truth = highpass(truth, fs)
    est = highpass(KORS @ src, fs)
    rs = [np.corrcoef(truth[i], est[i])[0, 1] for i in range(3)]
    allr.append(rs)
    print(f"{rec:<22} {note:<24} {rs[0]:>6.3f} {rs[1]:>6.3f} {rs[2]:>6.3f}")

if allr:
    m = np.mean(allr, axis=0)
    print("-" * 68)
    print(f"{'mean':<47} {m[0]:>6.3f} {m[1]:>6.3f} {m[2]:>6.3f}")

# ---- Which way is up? ----
print("\nMean QRS vector, healthy control (detrended, from real Frank leads):")
truth, _, fs = load("patient122/s0312lre")
truth = highpass(truth, fs)
mag = np.sqrt((truth ** 2).sum(axis=0))
qrs = mag > np.percentile(mag, 99.5)
mx, my, mz = truth[:, qrs].mean(axis=1)
print(f"   X = {mx:+.3f} mV   (+ = leftward)")
print(f"   Y = {my:+.3f} mV   (+ = inferior/downward)")
print(f"   Z = {mz:+.3f} mV   (+ = posterior)")
print("\n   A normal mean QRS axis is inferior + leftward, i.e. +X, +Y in")
print("   Frank coordinates. The scene draws y upward and puts aVF at -y,")
print("   so rendering anatomically requires scene_y = -frank_y.")

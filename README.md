# vectorEKG

A 12-lead ECG flattens the heart into twelve separate tracings. Transformed
to X, Y and Z, the same signal is a single vector sweeping a loop through
the chest — a **vectorcardiogram**. This site draws that loop in 3D, beat
by beat, and lets you rotate it.

Live at **[vectorekg.com](https://vectorekg.com)**.

Originally built by Mark Tuttle in 2012 as a medical student at The
University of Toledo College of Medicine. Flat HTML/JS on Three.js, no
backend, no build step.

## Recordings

Ten loops, chosen with the picker. All are 10 s at 250 samples/s and share
one mV-to-scene scale, so amplitudes are comparable *between* recordings —
LVH genuinely draws the biggest loop, an infarcted heart one of the
smallest.

The picker groups them by **how the XYZ leads were obtained**, which is a
real distinction and not a cosmetic one:

- **Recorded Frank leads** — [PTB Diagnostic ECG
  Database](https://physionet.org/content/ptbdb/1.0.0/). X, Y and Z are
  measured directly. Healthy control; acute infero-lateral MI.
- **Derived from the 12-lead** — [PTB-XL](https://physionet.org/content/ptb-xl/1.0.3/),
  which has no Frank leads, so XYZ comes from the Kors regression
  transform. Acute ST-elevation MI, complete LBBB, complete RBBB, atrial
  fibrillation, atrial flutter, LVH, WPW.

The tenth is the original 2012 tracing the site was built around.

Both databases are from [PhysioNet](https://physionet.org/) under the Open
Data Commons Attribution License, and are credited in the page itself — in
the footer and per recording. PTB-XL records were picked human-validated,
with the target SCP code at 100% confidence and no competing conduction or
rhythm diagnosis. "Acute MI with ST elevation" means PTB-XL's
`infarction_stadium1 = Stadium I`; most of its other MI records are *old*
infarct patterns and are not labelled acute here.

## Regenerating the data

`tools/gen_datasets.py` writes `htdocs/js/data/*.js` straight from
PhysioNet (needs `wfdb`, `numpy`, `scipy`). Each file loads on demand the
first time its recording is picked, so the page starts with only the
original tracing.

Two things it handles that are easy to get wrong, both found the hard way:

- **Orientation.** Frank +Y is *inferior* and +Z is *posterior*, but the
  scene draws y upward and puts V1 (anterior) at +z. XYZ therefore needs
  `(+X, -Y, -Z)`. Getting this wrong renders the vectorcardiogram upside
  down, which looks plausible until you notice the QRS pointing at aVR.
  The check that catches it: a healthy control's loop must sweep along the
  **lead II** vector, where a normal QRS axis belongs.
- **Baseline.** PTB has heavy baseline wander, which drags the whole loop
  around the scene instead of leaving it on the origin. Everything is
  high-pass filtered at 0.5 Hz.

`tools/validate_kors.py` checks the Kors implementation against ground
truth. PTB records the 12-lead *and* the Frank leads simultaneously, so
deriving XYZ from the former and correlating against the latter measures
the transform directly. Verified 2026-08-31 at r = 0.96 (X), 0.98 (Y),
0.84 (Z) over six records; Z is weakest, which is what the literature
reports. Re-run it if the transform is ever touched.

## Playback speed

The trace advances one 4 ms sample per `requestAnimationFrame`, so at ~60
fps it plays at roughly a quarter of real time. That is deliberate — it is
the pace the site has always run at, and it is easier to follow than real
time. Advancing by elapsed time instead would make it real-time and
frame-rate independent; don't "fix" it without meaning to.

## Deploying

Manual only — a push to `main` does not deploy. Ship from the Actions tab,
or:

```sh
gh workflow run deploy.yml
```

The workflow rsyncs `htdocs/` over SSH to an account restricted to a
forced command. Host, account and key are repository secrets
(`VPS_HOST`, `VPS_DEPLOY_USER`, `VPS_DEPLOY_KEY`), so no deployment target
appears in this repository.

## Credits

- ECG data: [PhysioNet](https://physionet.org/) — PTB Diagnostic ECG
  Database and PTB-XL, ODC-BY.
- Kors regression transform: Kors et al., *European Heart Journal*, 1990.
- 3D rendering: [Three.js](https://threejs.org/) (the 2012 vintage, vendored).

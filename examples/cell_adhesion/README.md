# Cell adhesion example (LMGC90)

Complete discrete model of a eukaryotic cell adhering on a substrate, based on the work of **Maxime Vassaux** (`m.vassaux@ucl.ac.uk`).

## What is generated

Two DATBOX configurations:

| Directory | Phase | Purpose |
|-----------|--------|---------|
| `DATBOX_SPRD/` | Spreading | Very stiff interactions; driven DOFs move focal adhesions toward the substrate |
| `DATBOX_STBL/` | Stabilisation | Calibrated elastic rods/wires and contact; realistic force readout |

### Constituents (complete model)

- Substrate (fixed rigid spheres)
- Nucleus membrane + inner nucleus particles
- Cell membrane (ventral / dorsal caps)
- Cytosol particles
- Focal adhesions (driven during spreading)
- **Microfilaments (MF)** network
- **Microtubules (MT)** network
- **Intermediate filaments (IF)** network
- **Stress fibres** (random chains between focal adhesions)

Interactions use `IQS_CLB`, `ELASTIC_ROD`, and `ELASTIC_WIRE` with phase-dependent stiffness.

## Requirements

- Python 3
- `pylmgc90` (pre module: `rigidSphere`, `granulo_Random`, `depositInBox3D`, `writeBodies`, …)
- NumPy

## Usage

```bash
python gen_sample.py <nsteps_sprd> <dt_sprd> <nsteps_stbl> <dt_stbl> <noutp>
```

Example:

```bash
python gen_sample.py 1000 1e-4 5000 1e-4 50
```

This only **writes** the DATBOX folders. You still need a chipy / `command.py` script for each phase (detectors for SPHER/PT3Dx, NLGS solver, etc.) consistent with your LMGC90 build.

## Notes

- Colours and law names respect the 5-character LMGC90 constraint.
- Bug fixed vs original: stress-fibre nearest-focal search used `coor_focals[2*j]` (2D stride); corrected to `coor_focals[3*j+…]` for 3D packed coordinates.
- IF network and stress fibres are **enabled** (they were commented out in some circulating copies).
- Runtime and particle count are high; start with smaller `nb_nodes_*` / `nb_focals` for tests if needed.

## Attribution

Original scientific model and script structure: Maxime Vassaux.
Packaged as a studio example without claiming authorship of the biophysics model.

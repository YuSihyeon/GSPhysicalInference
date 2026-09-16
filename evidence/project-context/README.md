# GS Embodied Physical Twin

Stage-1 experiment for binding exact hidden simulator physics to rigid bodies reconstructed with Gaussian Splatting. An OmniGibson R1 Pro agent combines a material prior, passive motion, and active system identification to reduce held-out future-motion prediction error.

Synthetic or analytic artifacts are engineering tests only. Research results require both `--require-real-gs` and `--require-omnigibson`.

## Windows OmniGibson environment

The verified simulator environment is the Miniconda environment `behavior` with
OmniGibson 3.9.2, Isaac Sim 5.1.0, CUDA-enabled PyTorch 2.7.0, and the
OmniGibson robot asset bundle. The restricted BEHAVIOR scene/object dataset is
not installed.

Isaac Sim 5.1 expects HDF5 1.14.6. On Windows, pin `h5py` to 3.15.1 because
h5py 3.16 bundles HDF5 2.0 and collides with Isaac Sim's sensor DLLs:

```powershell
conda activate behavior
python -m pip install -r constraints-omnigibson-win.txt
```

Keep OmniGibson's app data outside the OneDrive/non-ASCII workspace path. The
smoke test configures this automatically under `%LOCALAPPDATA%`:

```powershell
$env:OMNI_KIT_ACCEPT_EULA = "YES"
$env:OMNIGIBSON_HEADLESS = "True"
python .\scripts\smoke_omnigibson_r1pro.py
```

A successful run prints `R1PRO_SMOKE_OK` after creating an empty physics scene,
loading R1 Pro, resetting it, and stepping physics three times.

## Integrated rigid-body calibration run

The current integration run creates a multi-view RGB-D initialized Gaussian
cloud, derives a collider proxy from those Gaussians, binds one rigid body to
the Gaussian group, injects exact hidden simulator physics, and executes a
material prior, passive push, active force / friction / drop probes, and a
held-out GT-vs-inferred PhysX rollout:

```powershell
$env:OMNI_KIT_ACCEPT_EULA = "YES"
$env:OMNIGIBSON_HEADLESS = "True"
conda activate behavior
python .\scripts\run_omnigibson_rigid_probes.py --output .\outputs\stage1_run
```

`private/scene_gt.json` is the oracle-only answer file. Estimator-visible data
is written under `public/`, whose manifest contains only a hash of the GT.

This is an engine / estimator integration calibration, not yet the final
research experiment. R1 Pro is loaded in the same scene but does not yet make
the contacts; simulator force and kinematic-board actuators execute the probes.
The Gaussian cloud is initialized from aligned RGB-D observations rather than
photometrically optimized 3DGS. The first runs also show that a moving
kinematic incline can trigger dynamic slip before the nominal static-friction
limit, so static friction is currently treated as not reliably identifiable in
this setup. These limitations must remain visible in any reported result.

## Core paired PhysX pilot

The core experiment keeps one GS-derived geometry fixed and samples 12 exact
hidden-physics worlds. Within every world it pairs four evidence conditions:
material prior only, prior plus passive motion, fixed three-action probing, and
adaptive three-action probing. Identification and held-out action magnitudes
are disjoint.

```powershell
$env:OMNI_KIT_ACCEPT_EULA = "YES"
$env:OMNIGIBSON_HEADLESS = "True"
conda activate behavior
python .\scripts\run_core_paired_physx.py `
  --units 12 `
  --seed 20260831 `
  --output .\outputs\core_paired_physx_pilot_20260831_01
python .\scripts\report_core_paired_experiment.py `
  .\outputs\core_paired_physx_pilot_20260831_01
```

The completed pilot had 12/12 valid units. Passive evidence reduced mean
held-out translation NRMSE from 0.2882 to 0.1345. The preregistered adaptive
advantage was not supported: fixed-minus-adaptive AUC was -0.0275 with a 95%
paired-bootstrap interval of [-0.1499, 0.0599]. This negative result is retained
rather than tuned away. The largest failure occurred when the adaptive policy
skipped the drop probe and repeated a mass-sensitive probe, leaving restitution
poorly constrained for an oblique-drop evaluation.

Outputs include `public/report_summary.json`, `public/per_unit.csv`,
`public/core_experiment_results.png`, and `public/REPORT.md`. Exact GT remains
under each unit's `private/` directory. The pilot still uses RGB-D-initialized
Gaussians and simulator actuators; photometric 3DGS remains a follow-up stage.

## R1 Pro contact replication

The embodiment follow-up reuses representative `unit_005`, including its exact
hidden simulator mass, friction, restitution, and the same GS geometry hashes.
It holds a deterministic R1 Pro 28-DOF pose and advances the virtual base x joint
in 8 mm increments. The run passes only when PhysX reports an R1 finger/object
contact and the dynamic GS-bound object moves at least 2 cm:

```powershell
$env:OMNI_KIT_ACCEPT_EULA = "YES"
$env:OMNIGIBSON_HEADLESS = "True"
conda activate behavior
python .\scripts\run_r1pro_contact_replication.py `
  --pilot-root .\outputs\core_paired_physx_pilot_20260831_01 `
  --unit unit_005 `
  --output .\outputs\r1pro_contact_replication_20260831_23
```

The verified run first detected contact at step 35, recorded three
contact-positive steps, and displaced the object 0.1264 m. Exact GT is copied to
`private/source_scene_gt.json`; public files contain its SHA-256 only. The run
also writes `public/r1_contact_replication.mp4` from one direct simulator camera
capture per control step, with short before/after holds for visual context. It is
not synthesized by interpolating the three report still images. The run
uses zero gravity to isolate free-space hand/object contact, and the virtual base
is swept kinematically. It therefore validates R1 embodiment and collision
plumbing, not the adaptive identification policy or controller optimality.

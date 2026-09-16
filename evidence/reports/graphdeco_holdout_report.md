# Held-out 3DGS rendering report

## Evaluation contract

- Model: verified iteration-7,000 optimized PLY
- Validation views: 60
- Test views: 60
- Training/held-out filename overlap: 0
- Renderer: official Graphdeco Gaussian renderer
- Background: white
- Resolution scale: 1

Every record stores its reference path, rendered path, camera intrinsics, camera-from-world transform, and per-view metrics in `outputs/graphdeco_mustard_7000/holdout_renders/holdout_report.json`.

The 120 views are also encoded as a 20-second, 1,280 x 720, 12-fps side-by-side audit video at `outputs/graphdeco_mustard_7000/holdout_renders/heldout_real_vs_3dgs.mp4`. Each frame identifies the split, camera, angle, and foreground PSNR.

## Results

| Split | Views | Full-frame PSNR | Full-frame SSIM | Full-frame L1 | Reference-foreground PSNR | Reference-foreground L1 |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 60 | 32.8228 dB | 0.992635 | 0.00240849 | 16.9769 dB | 0.106981 |
| Test | 60 | 32.7417 dB | 0.992652 | 0.00240630 | 16.8405 dB | 0.106837 |

## Interpretation

The object-cropped comparisons show recognizable bottle geometry and label structure in frontal views. Top/bottom oblique views are visibly blurrier, with softened silhouette and surface detail.

The full-frame scores are inflated by the large white background. The foreground-only metrics and visual comparisons are the appropriate warning signal: this reconstruction is real and usable as the visual basis of the next experiment, but it is not yet a high-fidelity physical digital twin.

No mass, friction, or restitution has been inferred in this report. The next stage must derive the collision proxy from this optimized Gaussian artifact, inject exact hidden simulator properties through an oracle-only path, perform identifiable actions, and assess held-out future motion.

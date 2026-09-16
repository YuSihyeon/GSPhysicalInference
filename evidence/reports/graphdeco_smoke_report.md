# Graphdeco real-optimization smoke report

Date: 2026-08-31 (Asia/Seoul)

## Outcome

The pinned official Graphdeco trainer completed a real 10-iteration CUDA optimization of the 480-view YCB mustard training split. This was not a visualization of a primitive and not a relabeling of the RGB-D initialization.

Command settings:

```text
--iterations 10
--save_iterations 10
--test_iterations 10
--checkpoint_iterations 10
--white_background
--data_device cpu
-r 1
--disable_viewer
```

Observed training evidence:

```text
Reading camera 480/480
Number of points at initialisation : 50641
Training progress: 100% | 10/10
[ITER 10] Evaluating train: L1 0.009314085636287928 PSNR 24.056036758422852
[ITER 10] Saving Gaussians
[ITER 10] Saving Checkpoint
Training complete.
TRAIN_EXIT_CODE=0
```

## Independent artifact gate

- Initialization: `data/ycb/006_mustard_bottle/prepared/graphdeco_half/sparse/0/points3D.ply`
- Initialization SHA-256: `226498608a4a7712d86bfafabec0ba7668aea6431872c6aa516d708034af80d3`
- Optimized output: `outputs/graphdeco_smoke/point_cloud/iteration_10/point_cloud.ply`
- Optimized SHA-256: `4dc57496ff7f222ea3025edc107215cbcf2e79deb4981017b8d9e5ace8cd175e`
- Optimized Gaussian count: `50,641`
- Required optimized properties present: position, SH color coefficients, opacity, anisotropic scale, and rotation.
- Verification result: `verified=true`

The hashes differ and the optimized file has Graphdeco's Gaussian schema. Generated model files and full logs remain under the ignored `outputs/graphdeco_smoke` directory; the compact evidence is recorded here.

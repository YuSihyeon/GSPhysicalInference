# Official Graphdeco training report: YCB mustard bottle

## What was trained

- Source object: YCB `006_mustard_bottle`
- Training images: 480 calibrated RGB views
- Initialization: 50,641 RGB-D points from the prepared COLMAP dataset
- Renderer/trainer: official Graphdeco Gaussian Splatting
- Pinned revision: `54c035f7834b564019656c3e3fcc3646292f727d`
- Resolution scale: 1 (prepared 320 x 240 images; no automatic downscale)
- Optimization: 7,000 iterations, white background, images stored on CPU
- Wall time: 223.6567 seconds

## Verified artifact

- Optimized model: `outputs/graphdeco_mustard_7000/point_cloud/iteration_7000/point_cloud.ply`
- Gaussian count: 22,843
- Initialization SHA-256: `226498608a4a7712d86bfafabec0ba7668aea6431872c6aa516d708034af80d3`
- Optimized SHA-256: `47f9e428a0ee576c2a3c575a2853d3751e661350dac42cb7bf4580affd3ccb04`
- Verification: the output path is iteration 7,000, the PLY contains position, spherical-harmonic, opacity, scale, and rotation fields, and its hash differs from the initializer.

The model is therefore an actually optimized 3DGS artifact, not the RGB-D initialization renamed as a result.

## Training-set diagnostic

At iteration 7,000 the official trainer reported:

- mean L1: `0.0012939248234033586`
- mean PSNR: `38.73825149536133 dB`

These are training-view diagnostics only. Generalization is evaluated separately on camera views that never appeared in the COLMAP training image list.

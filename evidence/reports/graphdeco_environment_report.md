# Graphdeco CUDA environment report

Date: 2026-08-31 (Asia/Seoul)

## Purpose

This environment runs the official Graphdeco optimizer on the verified YCB mustard observations. It does not turn the RGB-D initialization into an alleged final reconstruction: only a Graphdeco-emitted `point_cloud/iteration_N/point_cloud.ply` is accepted as an optimized Gaussian artifact.

## Pinned source

- Repository: `https://github.com/graphdeco-inria/gaussian-splatting.git`
- Graphdeco: `54c035f7834b564019656c3e3fcc3646292f727d`
- SIBR viewers: `d8856f60c5384cc1975439193bb627d77d917d77`
- diff-gaussian-rasterization: `9c5c2028f6fbee2be239bc4c9421ff894fe4fbe0`
- rasterizer GLM: `5c46b9c07008ae65cb81ab79cd677ecc1934b903`
- fused-ssim: `1272e21a282342e89537159e4bad508b19b34157`
- simple-knn: `86710c2d4b46680c02301765dd79e465819c8f19`
- Workspace provenance clone: `vendor/gaussian-splatting` (ignored generated dependency)
- ASCII build mirror: `<LOCAL_PATH>`
- The root and every submodule reported `tracked_diff_exit=0` after compilation. No Graphdeco source was patched.

The ASCII build mirror is necessary because Ninja on this Windows host encoded the workspace's Korean `문서` path as `����` and consequently reported existing `.cu` files as missing. Both clones were checked against the exact revisions above.

## Runtime and compiler

- Conda environment: `<LOCAL_PATH>`
- Python: `3.11.16`
- PyTorch: `2.7.0+cu128`
- torchvision: `0.22.0+cu128`
- PyTorch CUDA runtime: `12.8`
- Conda CUDA Toolkit: `12.8.2`
- nvcc: `12.8.93`
- Visual Studio: `2022 Community 17.14.36`
- MSVC tools: `14.44.35207`
- GPU: `NVIDIA GeForce RTX 5060 Ti`
- Driver: `591.55`
- VRAM: `16,311 MiB`
- Compute capability: `12.0`
- Compiled CUDA architecture: `-gencode=arch=compute_120,code=sm_120`

Relevant Python packages:

```text
diff_gaussian_rasterization==0.0.0
fused_ssim==0.0.0
joblib==1.5.3
numpy==2.4.6
opencv-python==5.0.0.93
plyfile==1.1.5
simple_knn==0.0.0
tensorboard==2.21.0
torch==2.7.0+cu128
torchvision==0.22.0+cu128
tqdm==4.70.0
```

## Windows build adaptations

Two host-layout issues were isolated before the build succeeded:

1. `DISTUTILS_USE_SDK=1` is required after activating the Visual Studio developer environment.
2. Conda places CUDA import libraries in `Library/lib`, while PyTorch's Windows extension linker searches `CUDA_HOME/Library/lib/x64`. The environment's 82 `.lib` files (177,907,504 bytes) were mirrored into `Library/lib/x64`; no source file was modified.

Build variables:

```text
CUDA_HOME=<LOCAL_PATH>
TORCH_CUDA_ARCH_LIST=12.0
DISTUTILS_USE_SDK=1
```

## Execution verification

PyTorch CUDA boundary:

```text
torch 2.7.0+cu128
runtime 12.8
available True
gpu NVIDIA GeForce RTX 5060 Ti
capability (12, 0)
cuda_sum 28.0
```

Compiled extension execution (not import-only):

```text
distCUDA2 [1.0, 1.6666666269302368, 1.6666666269302368, 1.6666666269302368]
fused_ssim 1.0 2.307956492586527e-09
markVisible [False, False, False, True]
extensions_gpu_execution=PASS
```

This verifies execution of `simple_knn`, `fused_ssim`, and `diff_gaussian_rasterization` kernels on the RTX 5060 Ti.

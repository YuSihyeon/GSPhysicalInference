# YCB `006_mustard_bottle` source audit

Audit date: 2026-08-31  
Local source root: `data/ycb/006_mustard_bottle`  
Upstream: [official YCB Object and Model Set](https://ycb-benchmarks.s3.amazonaws.com/index.html)  
License: Creative Commons Attribution 4.0 International (CC BY 4.0)

## Result

The source gate passes. The official Berkeley capture contains the expected 600 high-resolution RGB observations and 600 RGB-D observations for `006_mustard_bottle`. Each modality is organized as five cameras observing the same 120 turntable angles from 0° through 357° in 3° increments. Masks, camera intrinsics/distortion, cross-camera extrinsics, and one reference-camera-to-table pose per angle are present. No mesh or aggregate YCB point cloud was downloaded or used.

The atomic experimental unit must be an **angle**, not an individual image. All five camera observations at a given angle must remain in the same train/validation/test partition to prevent same-pose leakage.

## Provenance and integrity

| Role | Official archive | Bytes | SHA-256 | Tar readable |
|---|---|---:|---|---|
| High-resolution RGB | `006_mustard_bottle_berkeley_rgb_highres.tgz` | 1,431,508,625 | `b67571728b8670003f9be620e48d4731afffb5a37f02a04938a7d3f8cc2c483c` | yes |
| RGB-D, masks, calibration | `006_mustard_bottle_berkeley_rgbd.tgz` | 657,272,400 | `5d9b1837eb58b0760463e99021a53fe6e82d5cd2457141945445ed6df06ff3f7` | yes |

Both archive lengths and hashes were recomputed independently after acquisition and match `source_manifest.json`. Every tar member passed the extraction-root containment check.

## Observed file structure

| Archive | JPG | PBM mask | HDF5 | Total files | Extracted bytes |
|---|---:|---:|---:|---:|---:|
| High-resolution RGB | 600 | 600 | 122 | 1,322 | 2,356,735,689 |
| RGB-D | 600 | 600 | 722 | 1,922 | 1,062,562,161 |

Representative paths:

- High-resolution image: `006_mustard_bottle/N1_0.jpg`
- High-resolution mask: `006_mustard_bottle/masks/N1_0_mask.pbm`
- RGB-D color image: `006_mustard_bottle/NP1_0.jpg`
- Raw depth map: `006_mustard_bottle/NP1_0.h5`
- RGB-D mask: `006_mustard_bottle/masks/NP1_0_mask.pbm`
- Per-angle pose: `006_mustard_bottle/poses/NP5_0_pose.h5`
- Shared calibration: `006_mustard_bottle/calibration.h5`
- Turntable metadata: `006_mustard_bottle/poses/turntable.h5`

The calibration file, all 120 per-angle pose files, and `turntable.h5` are byte-identical in the two archives.

## Capture geometry confirmed from files

| Field | High-resolution RGB | RGB-D |
|---|---|---|
| Camera IDs | `N1`–`N5` | `NP1`–`NP5` |
| Images per camera | 120 | 120 |
| Angle IDs | `0, 3, 6, …, 357` | `0, 3, 6, …, 357` |
| RGB size | 4272 × 2848 | 1280 × 1024 |
| Mask size | 4272 × 2848 | 1280 × 1024 |
| Depth size | none | 640 × 480, `uint16` |

Every camera has the complete 120-angle sequence. The PBM masks open as binary images with both background and foreground values.

## Calibration and pose contents

`calibration.h5` contains:

- RGB intrinsics: `{camera}_rgb_K`, shape `(3, 3)`, `float64`.
- RGB distortion: `{camera}_rgb_d`, shape `(5,)`, `float64`.
- RGB-D infrared/depth intrinsics: `{camera}_ir_K` and `{camera}_depth_K`, shape `(3, 3)`.
- Depth scale and bias: `{camera}_ir_depth_scale`, `{camera}_ir_depth_bias`, shape `(1,)`.
- Cross-camera transforms relative to the `NP5` reference camera: `H_{camera}_from_NP5`, shape `(4, 4)`.
- Infrared-camera transforms: `H_{camera}_ir_from_NP5`, shape `(4, 4)`.

For example, `NP1_rgb_K` has focal lengths approximately `(1080.920, 1080.921)` pixels, while `N1_rgb_K` has focal lengths approximately `(4597.930, 4597.932)` pixels. Distortion is nonzero, so images cannot be treated as ideal pinhole observations without undistortion or an equivalent distortion-aware conversion.

Each `poses/NP5_{angle}_pose.h5` contains:

- `H_table_from_reference_camera`, shape `(4, 4)`, a proper rigid transform (`det(R) ≈ 1`).
- `board_frame_offset`, shape `(3,)`.

The single `NP5` pose sequence is sufficient for every camera because the calibration supplies `H_{camera}_from_NP5`. For an object-fixed/table coordinate system, the candidate world-to-camera transform is:

`H_camera_from_table = H_camera_from_NP5 @ inverse(H_table_from_reference_camera)`

This convention still requires a projection-based verification test before conversion is accepted; the matrix names alone are not treated as proof.

`turntable.h5` contains `center` and `normal`, each shape `(3,)`. These values are retained as metadata and are not substituted for the per-angle rigid transforms.

The official YCB point-cloud script states that raw depth is converted to metres with `depth * camera_ir_depth_scale * 0.0001` and registered into the RGB frame using the infrared-to-RGB transform. The raw `NP1_0.h5` depth dataset is `(480, 640)` `uint16`; it contains both valid samples and zeros for missing depth.

## Inputs accepted for the next conversion stage

The YCB-to-3DGS converter may use only:

1. High-resolution RGB images and matching PBM masks for appearance training.
2. RGB-D color/depth pairs for geometric checks and initialization.
3. The audited calibration and per-angle pose HDF5 arrays.
4. A deterministic angle-level split manifest.

It may not use an official YCB mesh, a pre-fused YCB point cloud, or a hand-authored primitive as the reconstructed object. A point cloud generated directly from the allowed RGB-D observations is acceptable as an initialization, but the required reconstruction artifact remains an optimized Gaussian-splat PLY.

## Open risks and required gates

- Verify the transform direction numerically by projecting RGB-D points/mask support into at least two non-reference cameras.
- Undistort RGB images and masks with the supplied camera-specific coefficients before writing a pinhole COLMAP/Graphdeco model.
- Decide whether the first engineering fit uses all 600 high-resolution images or a documented downsample; this affects runtime but not the angle-level split.
- Quantify mask edge quality and reject frames with invalid calibration or unreadable data rather than silently replacing them.
- Keep the hidden physical ground-truth parameters out of all reconstruction and inference inputs. YCB visual data supplies geometry and appearance, not the experiment's hidden mass, friction, or restitution labels.

No missing required visual, mask, depth, or calibration field was found in this source audit.

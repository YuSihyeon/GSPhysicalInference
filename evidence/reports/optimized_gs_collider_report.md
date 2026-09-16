# Optimized 3DGS-derived collider report

## Frozen construction input

- Input type: optimized Graphdeco Gaussian PLY only
- Iteration: 7,000
- Input SHA-256: `47f9e428a0ee576c2a3c575a2853d3751e661350dac42cb7bf4580affd3ccb04`
- Total Gaussians: 22,843
- Retained after frozen opacity/spatial filtering: 11,359
- Density grid: 85 x 92 x 160 at 1.7889 mm
- Occupancy isovalue: 0.15

The official YCB mesh was not present when the density field and collider manifest were constructed. No source/evaluation-mesh argument exists in the builder API.

## Generated physics geometry

- Marching-cubes surface: 50,129 vertices, 101,518 faces, watertight
- PhysX proxy: one convex hull, 158 vertices, 312 faces, watertight
- Collider dimensions: 9.27 x 10.65 x 21.85 cm
- Collider volume: 0.00100713 m³
- Collider SHA-256: `7c67e9aa4ff0e5f2ccaf14741e27abfbeeb144ad1d1468ca7c14ca2480b50e66`

The convex hull is the physics-facing simplification. An attempted external quadric decimation was rejected because it made the originally watertight marching-cubes surface non-watertight.

## Evaluation-only comparison

After the geometry manifest was frozen, the official YCB Google 16k mesh was downloaded into an isolated `evaluation_only` directory. It was used only by a separate evaluator, with translation and one of four yaw rotations allowed; no scale was fitted.

| Metric | Density surface | Convex physics proxy |
|---|---:|---:|
| Symmetric Chamfer mean | 7.33 mm | 9.84 mm |
| Symmetric Chamfer p95 | 17.67 mm | 20.81 mm |
| Normal consistency | 0.539 | 0.830 |
| Scale L2 relative error | 21.56% | 21.56% |
| Volume relative error | 45.37% | 64.55% |

The largest error is depth: 10.65 cm versus the reference 6.66 cm (59.84% error). This is consistent with the blur and silhouette spread visible in oblique held-out 3DGS renders. The collider is a real GS-derived artifact, but its present geometry is not accurate enough to claim a high-fidelity real-object twin.

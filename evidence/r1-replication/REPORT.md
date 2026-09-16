# R1 Pro contact replication

- Validation: **PASS**
- First measured R1 finger/object contact: step 35
- Contact-positive steps: 3
- GS-bound object displacement: 0.1264 m
- Source GT hash: `778919fe2f06fc9ca8ff4cb6f19cbfd00765667cb3b9ed5676437674ccc5add9`
- GS collider hash: `1133f4433a8e05932b29fd2203bcac359407317551658f49343660b277515e66`
- Gaussian representation hash: `b6093f0572023a73f717808e34ef03e27309a46734b5f4c552d2d6004163a394`
- Direct simulator video: `r1_contact_replication.mp4` (71 frames, 15 FPS, 4.73 s)

The object uses the exact hidden mass, friction, and restitution from the paired pilot's `unit_005` world. The public folder exposes only its hash; the exact answer is copied to `private/source_scene_gt.json` so estimator inputs remain separated from evaluation answers.

This run validates embodiment and contact plumbing, not active-identification superiority. R1 Pro holds a deterministic 28-DOF pose while its virtual base x joint is swept in 8 mm increments. PhysX alone transfers the resulting finger contact impulse to the dynamic body. Gravity is zero for this free-space contact isolation test. The geometry is the same RGB-D-initialized Gaussian/collider proxy used in the core pilot, not a photometrically optimized 3DGS.
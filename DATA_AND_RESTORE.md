# 전체 데이터와 복원 범위

이 저장소는 YCB mustard bottle, Gaussian Splatting, PhysX/OmniGibson을 이용한 물성 추론 연구의 공개 증거를 담는다. 연구실 책상 `mydesk` 렌더링 연구와 구분되는 후속 실험이다. 공개 `evidence/`의 선별 소스·수치·영상과 별도로, 비공개 `ResearchCollection/05-GSPhysicalInference/`에는 전체 원 프로젝트와 원 데이터·중간 결과·가중치·정답 파일을 보존하는 계획이 있다.

공개 GitHub clone에는 비공개 `originals/`나 공유 runtime이 포함되지 않는다. 아래 경로는 컬렉션 배치 계약이며 2026-09-16 원본 조사 기준이다. **원본 존재 확인은 복사 완료, archive 무결성, 초기화 후 재현, USB 보관의 완료 확인과 다르다.** 실제 복사·검증 상태는 비공개 컬렉션의 `_control` 기록을 확인한다.

## 전체 원본 배치

| 프로젝트 폴더 기준 위치 | 내용 | 조사된 파일 수 / 논리 크기 |
|---|---|---:|
| `originals/vrlab_complete/` | VRLab 전체 main Git·소스·linked worktree·ignored data/vendor/output/환경 | 36,755 / 11,878,539,855 bytes |
| `originals/physical_ai_onedrive/` | 관련 Physical AI 루트. 조사 시 `.git`만 존재하며 HEAD는 unborn | 26 / 13,735,485 bytes |
| `originals/omnigibson_assets/` | 원 프로젝트 밖에 설치된 OmniGibson 설정 및 robot assets | 999 / 274,492,448 bytes |
| `originals/graphdeco_build_mirror/` | Windows ASCII 경로에서 빌드한 Graphdeco 별도 clone, submodule, CUDA build 상태 | 2,388 / 460,463,417 bytes |

실험 루트는 `originals/vrlab_complete/experiments/gs_embodied_physical_twin/`이다. 아래의 `data/`, `outputs/`, `scripts/` 등은 모두 이 실험 루트 기준이다. 실험 자체는 23,329개 파일 / 10,696,175,215 bytes이며 VRLab 합계에 이미 포함된다.

| 실험 하위 범위 | 파일 수 / bytes | 보존 이유 |
|---|---:|---|
| `data/` | 5,084 / 6,002,483,308 | 원 데이터 압축파일, 추출·준비 자료, split/camera/평가 자료 |
| `outputs/` | 717 / 193,392,342 | 성공·실패·중간 run, 원 영상, private oracle, 학습·추론·평가 결과 |
| `vendor/` | 11,281 / 4,275,547,385 | BEHAVIOR와 공식 Graphdeco source, Git/submodules |
| `.venv/` | 6,030 / 223,016,495 | 소형 estimator 환경의 당시 상태 |
| `src/`, `scripts/`, `tests/`, `configs/`, `docs/` | 전체 원본 | 공개 source-excerpts보다 넓은 구현·테스트·실행 정의 |

빌드 캐시와 환경을 포함한 논리 크기다. VRLab의 worktree/vendor를 다시 합산하지 않으며 이 표의 크기를 목적지 검증 결과로 사용하지 않는다.

## YCB 원 데이터와 준비 자료

대상은 `data/ycb/006_mustard_bottle/`이다. 로컬에 다음 원본 archive 두 개가 존재한다.

| 원본 archive | bytes |
|---|---:|
| `archives/006_mustard_bottle_berkeley_rgbd.tgz` | 657,272,400 |
| `archives/006_mustard_bottle_berkeley_rgb_highres.tgz` | 1,431,508,625 |

`extracted/`는 3,244파일 / 3,419,297,850 bytes, `prepared/`는 1,827파일 / 467,496,377 bytes, `evaluation_only/`는 8파일 / 25,685,939 bytes다. `source_manifest.json`에는 입력 출처·준비 과정의 추적 정보가 있다. 준비 자료에는 `graphdeco_half/` 외에 이름에 `INVALID`가 붙은 이전 mask/split 결과도 남아 있다. 이를 최종 학습 split과 혼합하지 않는다.

공식 reference geometry는 평가 전용이며 GS collider construction input으로 섞으면 실험 의미가 달라진다. 복원 시 `acquire_ycb_mustard.py`, `prepare_ycb_graphdeco.py`, config와 source manifest를 함께 보존하고, 최종 split과 실패한 준비 자료의 차이를 유지한다. 학습·validation·test 모두 한 물체의 서로 다른 시점이라는 범위도 유지한다.

## 학습 가중치와 전체 결과

`outputs/graphdeco_mustard_7000/`에서 다음 핵심 파일을 확인했다.

| 경로 | bytes | 의미 |
|---|---:|---|
| `chkpnt1000.pth` | 31,165,970 | 1,000 iteration 학습 checkpoint |
| `chkpnt7000.pth` | 16,468,114 | 7,000 iteration 학습 checkpoint |
| `point_cloud/iteration_7000/point_cloud.ply` | 5,666,594 | 실제 최적화된 Gaussian 파라미터 |
| `input.ply` | 1,367,540 | 학습 초기화 입력. 최적화 결과와 구분 |
| `training.log` | 166,138 | 학습 진행 기록 |

`cameras.json`, `cfg_args`, `exposure.json`, TensorBoard event와 verification도 같은 run에 있다. 렌더용 PLY만 보존하는 것과 학습을 이어갈 checkpoint·입력·config를 보존하는 것은 다르다. GPU나 compiler가 바뀐 환경에서 checkpoint 로드와 동일 학습 결과는 재검증해야 한다.

전체 outputs에는 stage1 run 01–08, core engineering 01–02와 pilot, R1 contact replication 01–23, GS contact 수정 과정, strict v1–v14가 포함된다. 최종값만 남기지 않는다. 핵심 결과 연결은 다음과 같다.

- `outputs/core_paired_physx_pilot_20260831_01/`: 12-unit paired 비교의 관측, per-unit 결과, 보고서, private oracle. adaptive 우월성이 지지되지 않은 결과를 유지한다.
- `outputs/r1pro_contact_replication_20260831_23/`: 실제 simulator 카메라와 초기 R1 접촉 재현.
- `outputs/graphdeco_mustard_7000/holdout_renders/`: validation/test 렌더 및 평가. 높은 full-frame 점수와 낮은 foreground 성능을 함께 해석한다.
- 같은 run의 `gs_density_collider/`: density surface, convex collider, manifest, reference 기하 평가. 깊이 오차가 컸던 결과도 보존한다.
- 같은 run의 `r1_contact_gs_strict_v14/`: raw robot 영상과 측정 PhysX pose에 GS를 합성한 영상. 접촉 PASS는 질량 식별 성공과 같지 않다.
- 같은 run의 `combined_estimate/`, `final_evaluation/`: frozen estimate와 미래 운동 평가. 최종 frozen estimate는 `strict_v14`가 아닌 앞선 `impulse_all_links` 입력에 연결되며 active mass measurement가 채택되지 않았다.

## Private oracle과 공개 자료

비공개 백업에는 `private/`, `scene_gt.json`, oracle/평가 전용 자료와 원래 summary를 포함한다. 원본의 `public/`라는 폴더명은 GitHub 공개 허가를 의미하지 않는다. 일부 per-unit CSV, summary, 평가 JSON 및 주석이 있는 그림·영상은 정확한 hidden GT 또는 역산 가능한 값을 담는다.

공개 evidence는 [공개 필터 기록](evidence/publication-filter.json)에 따라 정답과 역산 가능한 조합을 제거했다. 비공개 원본은 연구 기록을 위해 그대로 보존하되, 새 estimator 평가에 기존 정답을 입력하거나 public 저장소에 일괄 올리지 않는다. 새 blind trial은 oracle와 estimator 입력을 분리해 새 출력 경로에 만든다.

## 공유 실행 환경과 실제 버전

| 환경 | 조사 시점 또는 보존 보고서의 버전 | 역할 |
|---|---|---|
| `behavior` | Python 3.11.16, OmniGibson 3.9.2, Isaac Sim 5.1.0.0, PyTorch 2.7.0+cu128, NumPy 1.26.0, h5py 3.15.1 | PhysX oracle, R1 Pro, contact 실험 |
| `gs_graphdeco` | Python 3.11.16, PyTorch 2.7.0+cu128, torchvision 0.22.0+cu128, NumPy 2.4.6 | 3DGS 학습·렌더와 CUDA extension |
| Graphdeco source | `54c035f7834b564019656c3e3fcc3646292f727d` | vendor source와 별도 ASCII build mirror의 당시 HEAD |
| 당시 Windows build | CUDA Toolkit 12.8.2, nvcc 12.8.93, VS 2022 Community 17.14.36, MSVC 14.44.35207 | 환경 보고서의 실행 기록. 새 설치 보장 아님 |

`_shared/environments/snapshots/miniconda3-full.tar.zst`는 컬렉션 공용 Miniconda 전체 snapshot 계약이다. 별도 `_shared/environments/conda/`에는 `behavior` 및 `gs_graphdeco`의 environment YAML, explicit package 목록, pip 목록이 있다. 두 환경의 NumPy·DLL 구성이 달라 하나로 합치지 않는다. 원본 설치 경로·editable package·compiler·CUDA binary가 남아 있을 수 있어 압축 해제만으로 실행을 보장하지 않는다.

공유 `_shared/environments/snapshots/UE_5.7-full.tar.zst`는 컬렉션의 로봇/Unreal 연구용이다. 이 프로젝트의 확인된 물리 경로는 OmniGibson/Isaac Sim/PhysX이며 Unreal 설치로 대체되지 않는다. 관련 Visual Studio·SDK·NVIDIA driver는 공용 설치 정보와 [환경 보고서](evidence/reports/graphdeco_environment_report.md)를 함께 확인한다.

## 복원 순서

1. 컬렉션 manifest로 파일·해시 검증 상태를 확인한 뒤 전체 `vrlab_complete`와 외부 assets/build mirror를 새 작업 위치에 복사한다. `originals/`에서 직접 학습·실험을 재실행하지 않는다.
2. VRLab main `.git`와 `.worktrees/gs-physical-twin-stage1`을 함께 복원한다. main은 조사 시 remote가 없고 tracked 7개 변경, untracked 42개가 있었다. 새 clone이나 Git HEAD만으로 복구할 수 없다. 이동 후 worktree pointer는 작업 복사본에서 확인·수선한다.
3. 실험 `pyproject.toml`로 소형 estimator 환경을 만들고 tests를 확인한다. simulator·CUDA 학습에는 별도 `behavior`, `gs_graphdeco` 환경이 추가로 필요하다.
4. `behavior`에서 robot assets 경로와 `constraints-omnigibson-win.txt`를 적용하고 `scripts/smoke_omnigibson_r1pro.py`의 smoke 결과를 확인한다. 라이선스 동의는 복원 운영자가 해당 소프트웨어 조건을 확인한 뒤 처리한다.
5. `gs_graphdeco`에서 CUDA 사용 가능 여부와 rasterizer/simple-knn/fused-ssim 빌드를 확인한다. 한글·OneDrive 경로에서 Ninja 문제가 있었으므로 ASCII 작업 경로를 사용하고 preserved build mirror와 원 vendor source를 모두 유지한다.
6. 기존 optimized PLY의 validation/test 렌더를 새 출력 폴더에 생성하고 보존된 holdout 지표와 비교한다. 이후 collider/contact/held-out 평가를 단계별로 확인한다. mass impulse의 substep 누락 등 기존 한계를 그대로 기록한다.

## 미확보 또는 별도 외부 입력

`data/physion_plus/`에는 `training_bounds/physion_training_bounds.json`과 `rigid_target_properties.jsonl` 두 파일, 합계 1,061,465 bytes가 있다. 전체 Physion++ ZIP/PKL은 조사 범위에 없다. 당시 extraction script는 원격 archive를 HTTP Range로 읽었으므로 파생 통계만 보존되어도 원 데이터 전체 백업이라고 할 수 없다. 재수집은 보존 metadata의 URL/ETag와 현재 이용 조건을 확인해야 한다.

제한된 BEHAVIOR scene/object dataset은 설치되어 있지 않았다. 로컬 OmniGibson robot assets와 vendor source는 전체 scene/object corpus가 아니다. 외부 dataset 사용 조건과 third-party 코드는 [ATTRIBUTION.md](ATTRIBUTION.md)를 확인한다. 새 PC에서 전체 CUDA 학습, PhysX 실행, tests를 재수행한 기록은 아직 이 문서에 없다.

# GS 기반 물성 추론과 R1 Pro 접촉 연구

**복원된 외관에 물성을 연결하고, 관측과 능동 실험으로 보지 않은 미래 운동을 예측한다.**

[YCB · 3DGS · PhysX](#프로젝트-개요) · [영상 4개](#영상과-설명) · [구현](#구현-과정) · [결과](#결과와-분석) · [다음 실험](#한계와-다음-단계) · [재현](#재현과-자료-안내)

> **핵심 결론** — 12개 세계에서 수동 관측은 예측 오차를 줄였지만, 같은 예산의 적응적 탐색이 고정 탐색보다 낫다는 주가설은 지지되지 않았다. 실제 3DGS 학습과 로봇 접촉 연결은 확인했으며, 형상 오차와 질량 계측의 실패를 함께 보존했다.

## 프로젝트 개요

| 항목 | 내용 |
|---|---|
| 대상 | YCB `006_mustard_bottle` 한 형상과 서로 다른 숨긴 물성의 시뮬레이션 세계 |
| 질문 | 외관 복원에 관측·실험을 더하면 미래 운동을 얼마나 잘 예측할 수 있는가 |
| 실험 축 | 12-unit paired pilot → 실제 Graphdeco 학습 → GS collider → R1 Pro 접촉 → frozen 평가 |
| 도구 | Graphdeco 3DGS, OmniGibson, Isaac Sim/PhysX, R1 Pro |
| 기록 시점 | 2026년 8월 말 실험 기록 / 2026-09-16 선별 보존·수치 대조 |
| 현재 수준 | 시뮬레이션 연구 증거와 실패 분석; 고정밀 실물 twin이나 자율 조작의 완성 단계는 아님 |
| 상세 자료 | [기존 연구 보고서 전문](RESEARCH_REPORT.md) · [전체 데이터·복원 안내](DATA_AND_RESTORE.md) · [출처](ATTRIBUTION.md) |

<img src="evidence/strict-contact/r1_gs_contact_check.png" width="900" alt="R1 손가락이 GS 물체에 접근하고 접촉한 뒤 물체가 반응하는 비교 화면">

*최적화 GS를 측정된 PhysX pose에 맞춰 합성한 strict 접촉 결과. 접촉 검증 PASS와 질량 식별 성공은 별도 판정이다.*

## 영상과 설명

제목을 누르면 저장소의 MP4를 연다. 비교 영상과 시뮬레이터 원본의 제작 경로를 함께 표시했다.

| 영상 | 관찰할 내용 | 조건과 해석 |
|---|---|---|
| [실제 영상 ↔ 학습된 3DGS 렌더](evidence/optimized-gs/heldout_real_vs_3dgs.mp4) | 보지 않은 시점의 병·라벨·실루엣 | validation/test 120뷰, 비교 영상 20초·12fps; 물성 정확도와 별개 |
| [R1 Pro 초기 접촉 시연](evidence/r1-replication/r1_contact_replication.mp4) | 손가락 접촉 뒤 물체 이동 | RGB-D 초기 Gaussian, 영중력, 고정 28-DOF 자세와 kinematic base sweep; 71프레임·15fps |
| [엄격 접촉 · 시뮬레이터 원본](evidence/strict-contact/r1_controller_contact_raw.mp4) | 오른팔 접근과 손가락 접촉 | `strict_v14`, 영중력; 대상 물체는 raw 화면에서 숨김 처리 |
| [엄격 접촉 · GS 합성 시각화](evidence/strict-contact/r1_gs_contact_composite.mp4) | 측정 pose를 따라 렌더한 GS 물체의 반응 | 공식 Graphdeco 렌더와 robot 영상 합성, 84프레임·15fps; 임의 궤적 애니메이션과 구분 |

[초기 접촉 보고서](evidence/r1-replication/REPORT.md) · [strict 합성 입력·해시](evidence/strict-contact/r1_gs_contact_composite.json) · [학습 렌더 평가](evidence/reports/graphdeco_holdout_report.md)

## 연구 질문과 목표

보기 좋은 물체 복원만으로 질량, 정지마찰, 운동마찰, 반발계수가 결정되지는 않는다. 이 연구는 외관을 가진 강체에 불확실한 물성을 연결하고, 관측과 행동으로 그 불확실성을 줄이는 과정을 구성했다.

첫 질문은 **수동 운동 관측이 재질 prior보다 미래 운동 예측에 도움이 되는가**다. 두 번째는 **세 번의 탐색 기회에서 적응적으로 행동을 고르는 것이 고정 순서보다 유리한가**다. 후속 단계는 초기 Gaussian 표현을 실제 학습된 3DGS로 교체하고, simulator actuator의 작용을 로봇 손가락 접촉으로 연결하는 데 초점을 맞췄다.

평가 목표를 파라미터 오차 하나로 두지 않았다. 정답 물성을 가깝게 맞히는 것, 새로운 행동의 궤적을 예측하는 것, 로봇 접촉이 운동을 만드는 것은 서로 다른 성공 조건이다. [초기 설계와 실행 맥락](evidence/project-context/README.md)

| 평가 질문 | 필요한 증거 | 현재 상태 |
|---|---|---|
| 관측이 도움이 되는가 | 같은 세계에서 prior와 passive의 paired 비교 | 예측 오차 감소 기록 |
| 적응 탐색이 우수한가 | 같은 행동 예산의 fixed/adaptive AUC 비교 | 주가설 미지지 |
| 학습된 3DGS인가 | optimizer 실행·최종 PLY 필드·초기점과 다른 해시 | 후속 학습본에서 확인 |
| 로봇이 실제로 접촉했는가 | PhysX contact·운동 시작·접촉 link 검증 | 분리된 영중력 시험에서 확인 |
| 접촉으로 질량을 식별했는가 | 완전한 충격량 계측·유효 측정 gate | 엄격 접촉 run은 보고 불가 |

## 수행 내용과 기여 범위

이 저장소가 보여 주는 작업은 **실험 설계·실행 연결·검증·결과 해석**이다. 아래의 로컬 구현 근거와 외부 기술의 역할을 구분하며, 외부 엔진·모델 전체를 자체 개발 성과로 포함하지 않는다.

| 구분 | 수행·활용 내용 | 근거 |
|---|---|---|
| 관측·추론 연결 | prior, passive, force/friction/drop 관측을 입자 belief에 반영 | [belief](evidence/source-excerpts/belief.py), [관측](evidence/source-excerpts/observations.py) |
| 탐색과 비교 설계 | fixed/adaptive의 동일 예산, paired 세계, 행동 크기 분리, 실패 보존 | [selector](evidence/source-excerpts/selector.py), [통계](evidence/source-excerpts/statistics.py) |
| 학습·기하 연결 | YCB 준비, 공식 optimizer 실행, GS density에서 물리 proxy 구성 | [학습 보고서](evidence/reports/graphdeco_training_report.md), [collider 코드](evidence/source-excerpts/gs_density_collider.py) |
| 접촉 검증 | 허용 link, 운동 시작, 접촉 전 이동, 속도·흔들림 검사 | [접촉 코드](evidence/source-excerpts/r1_contact.py) |
| 추정치와 평가 연결 | frozen hash, 측정 수용 여부, final 입력 계보 감사 | [fusion](evidence/source-excerpts/estimate_fusion.py), [연결 감사](evidence/final-evaluation/frozen-estimate-audit.json) |
| 외부 기반 | Graphdeco 학습·렌더러, YCB 원자료, OmniGibson/Isaac Sim/PhysX와 R1 Pro 자산 | [자료 귀속](ATTRIBUTION.md) |

semantic/material prior는 불확실한 재질·채움 정도와 경험 통계를 사용한 가정이다. 별도 학습된 VLM이 물성을 성공적으로 추론했다는 기록은 없으며, 후속 fusion 코드도 약한 공학적 prior를 명시한다.

## 데이터와 선정 과정

### 하나의 물체, 서로 다른 평가 단위

| 입력·분할 | 선정과 사용 | 해석 경계 |
|---|---|---|
| YCB mustard bottle RGB-D | 초기 Gaussian과 학습 초기점 구성 | RGB-D 초기화 자체는 photometric 3DGS 학습이 아님 |
| 보정된 RGB 480뷰 | 320×240으로 Graphdeco 학습 | 한 물체의 다중 시점 데이터 |
| validation 60뷰 / test 60뷰 | 학습 파일명과 겹침 0, 공식 renderer로 평가 | 다른 물체에 대한 일반화와 구분 |
| hidden-physics 12세계 | 한 형상을 고정하고 물성을 달리한 paired pilot | 독립 표본은 세계 12개; 프레임을 표본 수로 늘리지 않음 |
| 대표 `unit_005` | pilot와 같은 형상 해시·숨긴 물성으로 R1 접촉 전달 확인 | 정책 우월성의 재검증이 아닌 접촉 재현 |
| 공식 YCB reference mesh | collider manifest 고정 뒤 평가 전용 비교 | construction 입력과 분리; scale fitting 없음 |

입력 원본은 Berkeley RGB-D·고해상도 RGB archive와 준비 자료로 나뉜다. 실패한 이전 mask/split의 `INVALID` 자료도 전체 보존본에 남아 있어 최종 split과 혼합하지 않는다. [원자료·split·checkpoint 위치](DATA_AND_RESTORE.md)

Physion++는 추출한 물성 통계 파일만 확인되었고 전체 corpus는 확보 범위에 없다. 제한된 BEHAVIOR scene/object dataset도 설치 기록이 없다. robot assets 보유와 전체 환경 데이터 보유를 구분한다.

### 동일 실험으로 합치지 않는 네 계보

1. **Core pilot:** RGB-D 초기 Gaussian + simulator actuator + 12세계 비교.
2. **초기 R1 접촉:** 같은 초기 형상 + 고정 자세 + 영중력 base sweep.
3. **Optimized GS strict 접촉:** 실제 학습 PLY + GS collider + 오른팔 Cartesian IK.
4. **Frozen 최종 평가:** 고정 추정치의 별도 oracle 평가. active 입력은 `strict_v14` 이전의 `impulse_all_links` run이다.

## 구현 과정

### 1. 관측·추론·행동 선택

재질 prior에서 입자 belief를 만들고 passive motion으로 갱신한 뒤, fixed 또는 adaptive 조건에서 세 번의 probe를 수행한다. 식별과 held-out 평가의 행동 크기를 분리하고, 정답은 oracle 쪽에 둔다.

adaptive 점수는 예측 관측의 분산을 센서 노이즈로 정규화한 `sum(log1p(variance / sigma²))`에서 행동 비용과 위험 패널티를 뺀 값이다. 동일 행동은 반복하지 않지만 magnitude가 다르면 같은 종류를 재선택한다. 미래 궤적 오차의 감소를 직접 최적화하는 목적함수는 아니다. [선택 구현](evidence/source-excerpts/selector.py)

### 2. 실제 3DGS 학습과 holdout 렌더

RGB-D 초기점 **50,641개 → 공식 optimizer 7,000 iteration → 최종 Gaussian 22,843개**로 진행했다. 기록된 학습 wall time은 223.6567초다. 최종 PLY에는 위치·구면조화·opacity·scale·rotation이 있고 초기점 파일과 해시가 다르다.

학습 PSNR 38.7383dB와 별도로 validation/test를 렌더했다. source revision은 `54c035f7834b564019656c3e3fcc3646292f727d`이며, Windows 한글/OneDrive 경로의 Ninja 문제는 ASCII build mirror로 우회한 기록이 있다. [학습](evidence/reports/graphdeco_training_report.md) · [환경](evidence/reports/graphdeco_environment_report.md)

### 3. GS에서 충돌 형상 구성

최적화 PLY만 construction input으로 사용하고 opacity·공간 필터로 **11,359개**를 남겼다. 약 1.7889mm voxel, 85×92×160 density grid, isovalue 0.15에서 marching cubes를 수행했다.

표면은 50,129 vertices·101,518 faces이며 watertight다. 물리용 단일 convex hull은 158 vertices·312 faces다. 외부 decimation은 watertight 상태를 깨뜨려 채택하지 않았다. [고정 construction manifest](evidence/collider/geometry_manifest.json)

<img src="evidence/collider/gs_collider_diagnostic.png" width="850" alt="GS density 표면과 물리용 convex hull의 크기와 형상을 비교한 진단 그림">

*렌더 품질과 물리 형상 품질을 나누어 검사한다. 표면이 닫혀 있다는 사실만으로 정확한 부피·깊이가 보장되지는 않는다.*

### 4. 접촉과 질량 계측을 별도 검증

초기 접촉은 28-DOF 자세를 고정하고 가상 base x를 8mm씩 이동한다. 첫 접촉 step 35, contact-positive 3 step, 변위 0.126386m가 기록되었다. 영중력 자유공간에서 충돌 전달을 분리한 시험이다. [초기 summary](evidence/r1-replication/r1_contact_summary.json)

`strict_v14`는 base zero command·gravity compensation과 오른팔 Cartesian IK의 1.5mm 이동을 사용한다. 물체에 직접 외력을 주지 않고 오른쪽 손가락 끝 접촉만 허용한다. wrist camera housing을 제외한 robot collision을 활성화했다.

첫 접촉 step 23, 운동 시작 step 29, 최종 변위 **16.677mm**, 접촉 시 visual gap **3.767mm**로 strict validation은 PASS다. 그러나 마지막 physics substep의 impulse만 읽어 누적 충격량이 불완전하다. `valid_for_reporting=false`, 질량 상대 오차 **88.72%**이므로 질량 식별 성공으로 보고하지 않는다. [strict summary](evidence/strict-contact/r1_contact_summary.public.json)

### 5. 추정치를 고정한 미래 운동 평가

추정치를 먼저 고정하고 해시를 기록한 뒤 별도 PhysX oracle에서 평가한다. frozen 파일 해시는 평가와 일치하지만, 연결된 active mass measurement는 `accepted=false`여서 질량 posterior는 prior와 같다. [frozen 입력 연결](evidence/final-evaluation/frozen-estimate-audit.json)

## 결과와 분석

### 관측의 효과와 적응 탐색의 부정 결과

| 조건 | 12세계 평균 held-out translation NRMSE ↓ |
|---|---:|
| prior only | 0.288226 |
| prior + passive | 0.134466 |
| fixed 최종 | 0.150530 |
| adaptive 최종 | 0.146359 |

**지표 정의:** 각 궤적의 3차원 위치 RMSE를 물체 extent의 최댓값으로 나눈 뒤, impulse와 oblique-drop 두 행동의 NRMSE를 평균한다. breakaway ramp는 별도 힘 상대 오차를 계산하며 이 translation 평균에 포함되지 않는다. 전체 보존본 `evaluation.py`와 `run_core_paired_physx.py`에서 정의를 대조했다. [코드 복원 위치](DATA_AND_RESTORE.md)

**AUC 정의:** passive 직후와 active 1·2·3회 뒤의 오차 곡선을 간격 1의 사다리꼴로 적분한다. 작을수록 좋으며 최종 endpoint와 다른 지표다. 세계별 `fixed AUC − adaptive AUC`가 양수일 때 adaptive가 유리하다. [집계 구현](evidence/source-excerpts/statistics.py)

prior→passive의 paired 평균 감소는 **0.153760**, 원 95% bootstrap 구간은 **[0.086585, 0.228931]**이다. 주 비교 AUC 차이는 **−0.027459**, 95% 구간 **[−0.149871, 0.059862]**, 양측 exact sign-flip **p=0.794434**다. adaptive 8승/fixed 4승이어도 우월성은 지지되지 않는다. [수치 summary](evidence/core-pilot/report_summary.json)

조건별 평균·AUC 차이·2¹²개 부호 조합의 p값은 2026-09-16 보존 검토에서 다시 계산해 일치했다. bootstrap 구간은 당시 결과를 인용했으며 새로 실행하지 않았다. [재계산 기록](evidence/numeric-verification.json) · [GT 제거 per-unit CSV](evidence/core-pilot/per-unit-errors.csv)

가장 큰 adaptive 손실 `unit_005`는 `incline:2 → vertical_accel:1.5 → vertical_accel:0.8`을 선택해 낙하를 건너뛰었다. 원 보고서는 반발계수 불확실성과 posterior 상관이 oblique-drop 실패로 이어졌다고 해석한다. 이 설명의 인과 경로를 이번 정리에서 다시 시뮬레이션한 것은 아니다. [실패 분석 원문](evidence/core-pilot/REPORT.md)

passive보다 active 최종 평균이 오히려 높다는 사실도 남는다. 정보 추가만으로 개선이 보장되지 않으며, 명목 정지마찰과 breakaway 유효 계수의 평균 차이 약 0.20355는 설정값과 행동상의 물성 차이를 보여 준다.

### 학습된 외관과 물리 형상의 차이

| 렌더 평가 | Full-frame PSNR ↑ | Full-frame SSIM ↑ | Reference-foreground PSNR ↑ |
|---|---:|---:|---:|
| validation 60뷰 | 32.8228dB | 0.992635 | 16.9769dB |
| test 60뷰 | 32.7417dB | 0.992652 | 16.8405dB |

PSNR은 [0,1] RGB의 MSE로 계산하며 foreground는 reference의 RGB 중 하나라도 250/255 미만인 픽셀이다. 표는 per-view 지표의 split 평균이며 SSIM은 공식 구현을 사용한다. 흰 배경의 큰 비중 때문에 full-frame 점수만으로 병의 형상 정확도를 판단하지 않는다. [평가 조건](evidence/reports/graphdeco_holdout_report.md) · [per-view JSON](evidence/optimized-gs/holdout_report.json)

| 기하 평가 | Density surface | Convex physics proxy |
|---|---:|---:|
| 평균 symmetric Chamfer ↓ | 7.326mm | 9.842mm |
| p95 Chamfer ↓ | 17.667mm | 20.809mm |
| Normal consistency ↑ | 0.5392 | 0.8302 |
| 크기 벡터 L2 상대 오차 ↓ | 21.56% | 21.56% |
| 부피 상대 오차 ↓ | 45.37% | 64.55% |

각 mesh에서 50,000점을 표본화하고 평행이동·네 방향 yaw 중 정렬을 허용하되 scale은 맞추지 않았다. Chamfer는 양방향 최근접 표면 거리, normal consistency는 대응 법선의 일치 정도다. 부피 오차는 reference 대비 절대 상대 차이이며, density 표면은 과소·convex proxy는 과대였다. [기하 평가 JSON](evidence/collider/ycb_geometry_evaluation.json)

특히 깊이는 **10.65cm 대 reference 6.66cm**, 상대 오차 **59.84%**다. 사선 렌더의 번진 실루엣과 기하 오차는 방향이 일치하지만, 그 인과를 별도 실험으로 분리한 결과는 아니다. 현재 collider로 고정밀 실물 twin을 주장할 수 없다. [collider 보고서](evidence/reports/optimized_gs_collider_report.md)

### Frozen 추정치의 최종 평가

| 지표 | 저장된 결과 | 읽는 기준 |
|---|---:|---|
| 질량 / 정지마찰 상대 오차 | 27.57% / 33.20% | 정답 대비 절대 차이의 백분율 |
| 운동마찰 / 반발계수 상대 오차 | 16.87% / 25.38% | 정답 대비 절대 차이의 백분율 |
| guided slide 위치 RMSE | 6.039mm / 55샘플 | 동일 시각 3차원 위치 차이 norm의 RMS |
| oblique drop 위치 RMSE | 9.033mm / 73샘플 | 동일 시각 3차원 위치 차이 norm의 RMS |

한 물체·한 frozen estimate·동일 엔진의 지정된 궤적 결과다. 수십 %의 물성 오차와 수 mm의 짧은 미래 위치 오차는 공존한다. 최종 질량은 접촉 측정으로 갱신되지 않았고, 최신 strict 영상과 같은 end-to-end run도 아니다. [공개 평가 요약](evidence/final-evaluation/evaluation.public.json)

## 한계와 다음 단계

아래 채택 기준은 **앞으로 수행할 실험의 제안**이다. 이미 달성한 수치나 사후에 바꾼 성공 기준으로 해석하지 않는다.

| 우선순위 | 다음 실험 | 통과·채택 기준 |
|---|---|---|
| P0 · 계측 | 모든 physics substep impulse를 누적하고 독립 momentum balance와 비교 | 불완전 계측은 강제 거부; 완전성 flag와 `valid_for_reporting`을 fusion gate에 연결하고 거부 테스트 통과 |
| P0 · 계보 | input·contact·estimate·oracle·영상을 단일 run ID/해시로 연결 | 영상에 사용한 run과 frozen estimate 입력 해시가 일치하고 모든 연결을 기계적으로 검증 |
| P1 · 탐색 | 미래 궤적 위험 감소 selector와 물성별 최소 probe 조건 비교 | 새 blind 세계·같은 예산에서 사전 고정한 AUC 차이의 95% 구간이 0보다 큼; 실패 세계도 보고 |
| P1 · 기하 | silhouette/depth 보완 및 여러 collider 구성 비교 | 독립 test에서 깊이·부피·Chamfer와 미래 운동 오차를 함께 개선하고 수치·출처 고정 |
| P2 · 접촉 | 정상 중력·다양한 자세·다른 물체로 확장 | 접촉 link·무접촉 운동·계측 유효성 기준을 유지하고 반복 성공률·실패 원인 보고 |
| P2 · 외부 검증 | 다른 엔진 또는 실측 궤적과 비교 | 물체·세션 단위 분리, 파라미터 오차와 운동 예측 오차를 별도 집계 |

현재 한계는 한 형상, 같은 PhysX 안의 추론·평가, 움직이는 경사판의 nominal/effective friction 차이, 외관과 collider 오차, 영중력 접촉의 제한된 조건이다. fusion의 기존 status/residual gate가 `valid_for_reporting` 자체를 검사하지 않는 점도 보존 코드에서 확인된다.

## 재현과 자료 안내

| 읽고 싶은 내용 | 경로와 범위 |
|---|---|
| 변경 전 상세 서술 | [RESEARCH_REPORT.md](RESEARCH_REPORT.md) — 기존 README를 바이트 그대로 보존 |
| 공개 실행 근거 | [evidence](evidence/) — 보고서, 선별 소스 15개, JSON/CSV, 그림, 영상 4개 |
| 전체 원본·가중치 | [DATA_AND_RESTORE.md](DATA_AND_RESTORE.md) — private 보존 위치, split, checkpoint, 환경, 복원 순서 |
| 공개에서 제외한 값 | [publication-filter](evidence/publication-filter.json) — hidden GT와 역산 가능한 필드 제외 |
| 외부 기술·데이터 귀속 | [ATTRIBUTION.md](ATTRIBUTION.md) |

재현은 별도 작업 복사본에서 **manifest 확인 → `behavior`/`gs_graphdeco` 환경 분리 복원 → robot/CUDA smoke → holdout 렌더 → collider → contact → 새 blind 평가** 순으로 진행한다. 당시 OmniGibson 3.9.2, Isaac Sim 5.1.0, PyTorch 2.7.0+cu128과 h5py 3.15.1 constraint는 현재 설치 검증 결과와 구분한다.

전체 보존본에는 원 프로젝트, YCB archive·준비 자료, 1,000/7,000 iteration checkpoint, 최적화 PLY, 실패 run, private oracle, 외부 robot assets와 ASCII build mirror가 있다. 공개 clone에는 이들과 모든 dependency가 없으므로 곧바로 실행되는 package가 아니다.

2026-09-16 확인은 수치 재계산·소스 구문·주요 이미지·파일 해시·입력 연결 대조 범위다. GPU 재학습, PhysX 전체 재실행, 새 PC 복원, USB 전송·외부 사본 검증은 완료 기록에 포함하지 않는다. 원본 `public/` 폴더 이름만으로 공개 범위를 넓히지 않고, 새 실험은 기존 정답을 추론기에 넣지 않는 독립 blind trial로 기록한다.

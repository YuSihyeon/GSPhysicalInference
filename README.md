# GS 기반 물성 추론과 R1 Pro 접촉 연구


**독립 연구 저장소:** [GitHub](https://github.com/YuSihyeon/GSPhysicalInference) · [전체 데이터와 복원 범위](DATA_AND_RESTORE.md) · [영상 갤러리](https://yusihyeon.github.io/GSPhysicalInference/gallery.html)

이 자료는 **GS로 복원한 강체에 물성을 연결하고, 관측과 능동 실험으로 보지 않은 미래 운동을 예측하려는 후속 연구**다. 실제 연구실/mydesk의 공간 복원과 구분되는 **YCB mustard bottle·OmniGibson·PhysX·R1 Pro** 실험 계열이다. 분석 대상은 2026년 8월 말에 작성된 로컬 코드·보고서·결과이며, 2026-09-16에 선별 보존했다. 관련 연구는 각각 독립 저장소로 정리했으며 이 저장소는 해당 연구의 기록만 다룬다.

핵심 결론은 세 가지다. **수동 관측을 추가한 물성 추론은 12개 세계의 미래 운동 오차를 줄였다. 적응적 탐색이 같은 예산의 고정 탐색보다 낫다는 주가설은 지지되지 않았다. 실제 최적화한 3DGS와 로봇 접촉 후속 실험은 존재하지만, 형상 정확도와 접촉 기반 질량 계측의 한계 때문에 고정밀 물리 디지털 트윈 완성으로 소개할 수 없다.**

## 1. 연구 질문과 설계 의도

외관이 복원되어도 질량·정지마찰·운동마찰·반발계수는 영상만으로 정해지지 않는다. 이 연구는 재질 prior, passive motion, active probing의 정보를 순차적으로 결합하고, 단순 파라미터 정답 맞히기와 **보지 않은 행동의 미래 운동 예측**을 구분한다. 정답 물성은 시뮬레이터 oracle에만 두고, 추론기에 보이는 자료와 평가용 정답을 분리하려 했다. [원 프로젝트 설명](evidence/project-context/README.md)

현재 selector의 점수는 입자 posterior가 예측하는 측정 분산을 센서 노이즈로 정규화한 `sum(log1p(variance / sigma²))`에서 행동 비용과 위험 패널티를 뺀 값이다. 같은 행동은 반복하지 않지만, magnitude가 다른 같은 종류의 행동은 다시 선택할 수 있다. **직접 미래 궤적 위험의 감소를 최적화하는 selector는 아니다.** [selector 코드](evidence/source-excerpts/selector.py)

| 구성 | 실제 역할 | 근거와 선택의 한계 |
|---|---|---|
| OmniGibson / Isaac Sim / PhysX | 로봇·강체·접촉 및 hidden-physics 세계의 실행과 평가 | 같은 엔진에서 추론 관측과 평가를 수행한 self-consistency 한계가 있음 |
| R1 Pro | 팔/손가락 접촉이 물체 운동으로 전달되는지 확인 | 초기 pilot에서는 같은 장면에 로봇이 있어도 탐색 접촉은 simulator actuator가 수행 |
| RGB-D 초기 Gaussian 표현 | 초기 pilot의 고정 형상과 collider 구성 | 학습한 photometric 3DGS와 동일하지 않음 |
| 공식 Graphdeco 3DGS | YCB 다중 시점 RGB를 이용한 실제 photometric optimization | 학습 출력과 initializer의 경로·필드·해시를 분리해 검증 |
| GS density → marching cubes → convex hull | 학습한 Gaussian만으로 물리 충돌 형상 구성 | 물리 엔진용 단순화가 실제 형상·부피를 왜곡할 수 있음 |
| 입자 belief와 분석적 probe estimator | 질량·마찰·반발계수의 관측 해석과 실험 선택 | 정확한 정답 물성 회복과 실제 운동 예측은 일치하지 않을 수 있음 |
| semantic/material prior | 불확실한 재질·채움 정도와 경험적 데이터 통계의 초기 가정 | 별도의 학습된 VLM 추론을 입증하는 기록은 없음. 후속 fusion 코드는 약한 공학적 prior를 명시 |

## 2. 단계별 진행 과정과 증거 수준

### A. 엔진 통합과 RGB-D 기반 초기 보정

초기 통합은 정렬된 RGB-D에서 Gaussian cloud를 만들고 GS 유래 collider를 붙인 강체에 숨긴 물성을 주입한 뒤, prior·passive push·force/friction/drop probe와 held-out PhysX rollout을 연결했다. R1 Pro가 실제 접촉을 만드는 단계는 아니었다. 움직이는 kinematic incline가 nominal 정지마찰 한계보다 먼저 동적 미끄러짐을 유발할 수 있다는 문제가 남았다.

원 보고서는 이 단계의 Gaussian을 최적화된 3DGS라고 부르지 않으며, synthetic/analytic 산출물은 engineering test로 제한한다. 따라서 이 결과를 photometric 복원과 자율 로봇 실험이 모두 완성된 단일 시스템으로 묶으면 과장이다.

### B. 12개 hidden-physics 세계의 paired pilot

형상은 하나로 고정하고 정확한 숨긴 물성이 다른 12개 세계를 준비했다. 각 세계에서 동일한 형상, passive 관측, 센서 노이즈, held-out 행동을 공유하면서 네 조건을 비교한다.

1. prior only
2. prior + passive motion
3. 고정된 세 번의 active probe
4. adaptive selector가 고른 세 번의 active probe

식별에 쓰는 행동 크기와 평가 행동 크기를 분리하고, impulse·breakaway ramp·oblique drop의 미래 운동을 평가했다. 독립 단위는 세계 12개이며, 같은 세계 안의 시간 샘플이나 네 조건을 독립 표본으로 세지 않는다. [실험 보고서](evidence/core-pilot/REPORT.md)

| 조건 | 평균 held-out translation NRMSE |
|---|---:|
| prior only | 0.288226 |
| prior + passive | 0.134466 |
| fixed 최종 | 0.150530 |
| adaptive 최종 | 0.146359 |

prior→passive의 paired 평균 차이는 0.153760이고 원 결과의 95% bootstrap 구간은 [0.086585, 0.228931]이다. 반면 주 비교인 **fixed AUC − adaptive AUC**는 −0.027459, 95% bootstrap 구간 **[−0.149871, 0.059862]**, 양측 exact sign-flip p=**0.794434**다. adaptive의 승리 세계 수는 8, fixed는 4지만 평균 효과와 불확실성을 무시하고 “adaptive가 우수하다”고 결론내릴 수 없다. endpoint 평균과 여러 단계의 AUC도 서로 다른 지표다. [기계 판독 summary](evidence/core-pilot/report_summary.json)

이번 정리에서는 공개 가능한 오차 열만 추출해 조건별 평균, AUC 평균 차이, 2¹²개 부호 조합의 exact sign-flip p를 다시 계산했다. 저장된 보고서와 일치한다. bootstrap 구간은 원 결과를 인용했으며 이번 조사에서 bootstrap을 다시 실행한 것은 아니다. [재계산 기록](evidence/numeric-verification.json), [GT를 제외한 per-unit 오차](evidence/core-pilot/per-unit-errors.csv)

**실패 분석:** 가장 큰 adaptive 손실은 `unit_005`에서 발생했다. 선택 순서는 `incline:2 → vertical_accel:1.5 → vertical_accel:0.8`로, 낙하 probe를 선택하지 않았다. 원 보고서는 관측하지 못한 반발계수의 불확실성이 oblique-drop 예측으로 전파되었다고 해석한다. selector 코드도 질량 민감 행동을 다른 크기로 재선택할 수 있으므로 이 설명과 일치한다. 다만 posterior 상관의 전체 인과 경로를 이번 조사에서 다시 시뮬레이션한 것은 아니다.

nominal 정지마찰과 breakaway에서 얻은 유효 계수의 평균 차이는 약 0.20355였다. 물성 정답과 움직임 예측을 나눠 평가해야 한다는 실험상의 이유다. 추가 active 정보가 평균 오차를 항상 개선한 것도 아니다. fixed와 adaptive의 최종 평균은 passive만 사용한 평균보다 약간 높다.

### C. R1 Pro의 접촉 전달 재현

대표 `unit_005`의 같은 GS 형상 해시와 숨긴 물성을 사용해 실제 R1 finger/object 접촉을 만들었다. 28자유도 자세를 유지하고 가상 base x를 8mm씩 움직인다. 접촉은 step 35에서 처음 관측되고 3개 step이 contact-positive이며 물체는 **0.126386m** 이동했다. [접촉 summary](evidence/r1-replication/r1_contact_summary.json)

![R1 접촉과 물체 이동](evidence/r1-replication/r1_contact_result.png)

[원 simulator 영상](evidence/r1-replication/r1_contact_replication.mp4)은 제어 step마다 직접 카메라를 캡처한 71프레임·15FPS·약 4.73초 자료다. 보고서의 세 장짜리 정지 이미지를 보간해서 만든 영상은 아니다. 이 실행은 **중력 0인 자유공간 접촉 분리 시험**, **kinematic base sweep**, **RGB-D 초기 Gaussian 형상**을 사용한다. 로봇 접촉과 물리 전달 연결을 확인하지만 adaptive identification의 우월성이나 정상 중력에서의 자율 조작을 검증하지 않는다. [원 보고서](evidence/r1-replication/REPORT.md)

### D. YCB 물체의 실제 Graphdeco 3DGS 학습

초기 표현의 한계를 보완하기 위해 YCB `006_mustard_bottle`의 보정된 RGB 480장을 320×240 해상도로 준비하고, RGB-D 초기점 50,641개에서 공식 Graphdeco optimizer를 7,000 iteration 수행했다. 출력 Gaussian은 **22,843개**, 학습 wall time은 기록상 **223.6567초**다. 소스 revision은 `54c035f7834b564019656c3e3fcc3646292f727d`로 기록되어 있다. [학습 보고서](evidence/reports/graphdeco_training_report.md)

출력은 `iteration_7000` PLY이며 위치·구면조화·opacity·scale·rotation 필드를 갖고 초기점 파일과 해시가 다르다. 단순 RGB-D 초기점을 최종 학습본으로 이름만 바꾼 결과와 구분하는 근거다. 대형 PLY와 checkpoint는 이 공개 묶음에 복사하지 않고 보고서와 해시를 남겼다.

환경 보고서는 당시 RTX 5060 Ti, PyTorch 2.7.0+cu128, CUDA 12.8, 공식 CUDA extension 실행을 기록한다. 한글/OneDrive 경로의 Ninja 인코딩 문제는 ASCII build mirror로 우회했고, CUDA import library 경로 차이도 환경 배치로 해결했다. 이는 당시 재현 정보이며 현재 설치 환경을 새로 검증한 결과는 아니다. [환경 보고서](evidence/reports/graphdeco_environment_report.md)

### E. 보지 않은 시점의 렌더 평가

학습 목록과 겹치지 않는 validation 60장, test 60장을 공식 Gaussian renderer로 평가했다. 겹치는 파일명은 0이다. 같은 한 물체의 시점 분리이므로 여러 물체에 대한 일반화 평가로 읽어서는 안 된다.

| 구분 | Full-frame PSNR | SSIM | 물체 foreground PSNR |
|---|---:|---:|---:|
| validation 60뷰 | 32.8228dB | 0.992635 | 16.9769dB |
| test 60뷰 | 32.7417dB | 0.992652 | 16.8405dB |

큰 흰 배경이 full-frame 점수를 높이므로 foreground 지표와 실제 외곽선 비교를 같이 봐야 한다. 원 보고서도 정면의 병과 라벨은 알아볼 수 있지만 위·아래 사선 시점이 흐리고 실루엣이 번진다고 기록한다. 학습 PSNR 38.7383dB만으로 형상 정확도를 주장하지 않는다. [holdout 보고서](evidence/reports/graphdeco_holdout_report.md), [전체 per-view 수치](evidence/optimized-gs/holdout_report.json), [실사 대 GS 비교 영상](evidence/optimized-gs/heldout_real_vs_3dgs.mp4)

### F. 실제 GS에서 collider 구성과 기하 오차 평가

최적화된 Gaussian PLY만을 construction input으로 사용했다. opacity/공간 필터를 고정해 22,843개 중 11,359개를 남기고, 약 1.7889mm voxel의 85×92×160 density grid와 isovalue 0.15에서 marching cubes 표면을 얻었다. 표면은 50,129 vertices·101,518 faces·watertight이며, 물리용 단일 convex hull은 158 vertices·312 faces다. decimation 시도가 watertight 특성을 깨뜨려 배제되었다는 기록이 있다. [construction manifest](evidence/collider/geometry_manifest.json)

![최적화 GS 밀도 표면과 물리용 convex hull](evidence/collider/gs_collider_diagnostic.png)

원 보고서는 construction manifest를 고정한 뒤 공식 YCB mesh를 평가 전용으로 가져와 비교했다고 설명한다. 평가 정렬은 평행이동과 네 방향 yaw 중 선택을 허용하고 scale fitting은 하지 않는다. 이번 조사에서 manifest·보고서·평가 수치를 대조했으며, 모든 과거 프로세스의 실행 순서를 별도 포렌식으로 입증한 것은 아니다.

| 형상 평가 | Density surface | Convex physics proxy |
|---|---:|---:|
| 평균 symmetric Chamfer | 7.326mm | 9.842mm |
| p95 Chamfer | 17.667mm | 20.809mm |
| normal consistency | 0.5392 | 0.8302 |
| 크기 벡터 L2 상대 오차 | 21.56% | 21.56% |
| 부피 상대 오차 | 45.37% | 64.55% |

가장 큰 문제는 깊이이다. collider의 깊이는 **10.65cm**, 공개 YCB reference는 **6.66cm**로 상대 오차 **59.84%**다. 시각적으로 병처럼 보이는 것과 충돌·관성·부피 추정에 필요한 정확한 기하는 다르다. 이 collider는 실제 GS 유래라는 출처를 갖지만 현재 형상으로 고정밀 real-object twin을 주장할 수 없다는 원 보고서 결론이 수치와 일치한다. [기하 평가 JSON](evidence/collider/ycb_geometry_evaluation.json), [원 collider 보고서](evidence/reports/optimized_gs_collider_report.md)

### G. 최적화 GS 형상의 엄격한 손가락 접촉 검증

`strict_v14`는 초기 base-sweep 데모와 다르다. base에는 zero command와 gravity compensation을 사용하고 오른팔 Cartesian IK를 1.5mm씩 진행한다. 물체에 직접 외력을 가하지 않고 로봇 접촉으로만 운동을 전달한다. 오른쪽 wrist camera housing을 제외한 robot collision을 켜고, 검증은 **오른쪽 손가락 끝 접촉만 허용**한다.

기록상 첫 손가락 접촉 step은 23, 물체 운동 시작 step은 29, 최종 변위는 **16.677mm**, 접촉 시 visual gap은 **3.767mm**다. 접촉 전에 물체가 움직였는지, 손가락 이외의 link가 닿았는지, 속도가 지나치게 큰지, 손의 가로 흔들림이 큰지 등을 검사해 strict validation이 PASS이다. [정답을 제거한 접촉 summary](evidence/strict-contact/r1_contact_summary.public.json), [검증 코드](evidence/source-excerpts/r1_contact.py)

![R1 손가락 접근·접촉·반응](evidence/strict-contact/r1_gs_contact_check.png)

**영상의 구성:** [raw simulator 영상](evidence/strict-contact/r1_controller_contact_raw.mp4)에서 대상 물체는 물리 엔진 안에서 보이지 않도록 되어 있다. [GS 합성 영상](evidence/strict-contact/r1_gs_contact_composite.mp4)은 측정한 PhysX 물체 pose에 맞춰 공식 Graphdeco GS를 렌더링해 robot 영상과 합성했다. 물체 궤적을 임의로 생성했다는 뜻은 아니지만, raw simulator가 직접 Gaussian을 동일 파이프라인으로 렌더링한 것과는 구분해야 한다. 84프레임·15FPS이며, [합성 manifest](evidence/strict-contact/r1_gs_contact_composite.json)에 renderer 입력과 collider 해시가 연결되어 있다.

**접촉 PASS와 질량 추론 성공은 다르다.** 이 run의 mass-identification은 `valid_for_reporting=false`이다. 한 제어 프레임의 여러 physics substep 중 마지막 substep에서만 contact impulse를 읽어 전체 충격량을 누락한다는 이유가 명시되어 있다. 질량 상대 오차도 88.72%로 기록되었다. 작은 momentum residual이 나와도 측정된 충격량 자체가 불완전하면 좋은 질량 추정이 아니다. 이 run 역시 중력 없는 접촉 분리 시험이다.

### H. Frozen estimate와 최종 미래 운동 평가

최종 평가 파일은 추정치를 고정하고 해시를 기록한 다음 별도 PhysX oracle에서 평가하는 protocol을 명시한다. 실제 frozen estimate 파일 SHA-256이 evaluation의 `frozen_estimate_sha256`과 일치한다. 해당 frozen estimate의 **active mass measurement는 accepted=false이고 질량 posterior는 prior와 같다.** 따라서 최종 질량을 로봇 접촉으로 성공적으로 식별했다고 표현하면 안 된다.

또한 입력 commitment를 따라가면 이 frozen estimate에 연결된 active 입력은 `strict_v14`가 아니라 이전 `r1_contact_gs_unit_000_impulse_all_links`이다. 최종 평가와 가장 보기 좋은 접촉 영상을 동일 실험의 완전한 end-to-end 결과처럼 합치는 것을 피해야 한다. [출처 연결 감사](evidence/final-evaluation/frozen-estimate-audit.json)

| 최종 평가 지표 | 저장된 값 |
|---|---:|
| 질량 상대 오차 | 27.57% |
| 정지마찰 상대 오차 | 33.20% |
| 운동마찰 상대 오차 | 16.87% |
| 반발계수 상대 오차 | 25.38% |
| held-out guided slide 위치 RMSE | 6.039mm / 55샘플 |
| held-out oblique drop 위치 RMSE | 9.033mm / 73샘플 |

위치는 해당 한 물체·한 frozen estimate·동일 엔진의 지정된 평가에 대한 오차다. 수십 퍼센트의 파라미터 오차와 수 mm의 짧은 미래 위치 오차가 공존하므로, 이 지표들을 바꾸어 쓰지 않는다. [블라인드 정답을 제외한 평가 요약](evidence/final-evaluation/evaluation.public.json)

## 3. 실패를 보존한 이유와 개선 우선순위

| 남은 문제 | 현재 증거가 보여 주는 의미 | 후속 개선 제안 |
|---|---|---|
| adaptive 우월성 미지지 | 8/12 승리와 평균 효과·AUC 불확실성은 다름 | held-out trajectory-risk reduction을 직접 고려하는 selector를 별도 후속 조건으로 비교 |
| 낙하 probe 누락 | 질량 정보만 반복 얻으면 반발에 민감한 평가에서 실패 가능 | 물성 종류별 최소 탐색 조건을 명시해 새로운 실험으로 평가 |
| nominal/effective friction 차이 | 설정값 회복과 실제 운동 예측을 분리해야 함 | 고정 경사·초기화 조건·접촉법선/마찰 결합의 영향 분석 |
| collider 깊이·부피 과대 | 외관과 물리 형상의 오차가 이후 prior와 동역학에 전파될 수 있음 | foreground/silhouette·depth 보완, 여러 collider 구성의 물리 오차 비교 |
| 충격량 일부 substep 누락 | residual만으로 계측 타당성을 판정하면 안 됨 | 모든 physics substep impulse를 누적하고 독립 momentum balance 검증 |
| fusion 코드의 검증 계약 | 보존 script는 status와 residual gate를 사용하며 `valid_for_reporting` flag 자체를 검사하지 않음 | 측정의 보고 가능성·완전성 flag를 gate에 연결하고 잘못된 측정 거부 테스트 추가 |
| frozen 평가와 최신 영상 연결 차이 | 최신 접촉 시연이 final estimate 생성에 사용된 것은 아님 | 단일 run ID/commitment graph로 input·estimate·oracle·영상 묶기 |
| 한 형상·같은 엔진 | 실세계/다른 물체 일반화를 입증하지 못함 | 여러 실물 형상, 다른 초기 조건·엔진·실측 궤적으로 외부 검증 |

위 항목은 이번 아카이브의 코드·결과 분석과 향후 제안이다. 보존 소스의 로직을 임의로 수정하거나 보고서 수치를 개선하기 위한 재튜닝은 하지 않았다.

## 4. 재현과 보존 범위

당시 simulator 환경은 OmniGibson 3.9.2, Isaac Sim 5.1.0, PyTorch 2.7.0으로 기록되어 있고 Windows HDF5 충돌을 피하기 위한 h5py 3.15.1 constraint가 남아 있다. BEHAVIOR의 제한된 scene/object dataset은 설치되지 않았다는 기록이다. 이는 당시 환경 설명이며 이번 아카이브에서 전체 simulator·CUDA 학습을 재실행하지 않았다. [환경 constraint](evidence/project-context/constraints-omnigibson-win.txt)

이 공개 묶음은 **증거 아카이브**다. 소스 발췌 15개는 estimator·selector·GS construction·접촉 검증과 fusion의 구현 근거이며, oracle·대형 학습 자산·외부 dependency가 빠져 있어 독립 실행 package로 제시하지 않는다. 완전한 재현에는 원 프로젝트의 데이터 준비, 고정된 Graphdeco revision, simulator 환경, 별도의 새로운 blind oracle 구축이 필요하다. 보존된 정답을 estimator에 다시 주입해 재현하는 방식은 실험 목적과 다르다.

공개 보존 내역:

- prior/passive/fixed/adaptive의 aggregate 수치와 GT 열을 제거한 per-unit 오류 표.
- 초기 R1 접촉 재현의 보고서·summary·직접 simulator 영상.
- 실제 GS 학습·holdout·collider 문서, per-view 수치, 비교 영상, 기하 평가와 진단 그림.
- strict 접촉의 raw/composite 영상과 출처 metadata, 보고 불가 질량 결과의 이유.
- final evaluation의 상대 오차·미래 운동 오차와 frozen input 연결 감사.

**`public/`라는 이름만 믿고 원본을 전부 공개하지 않았다.** 실제로 core per-unit CSV에는 hidden GT 열이 있고, strict-contact summary와 final evaluation에도 정확한 물성 정답이 들어 있었다. 이 아카이브는 GT 숫자뿐 아니라 estimate와 absolute error의 조합으로 정답을 역산할 수 있는 필드도 제외했다. nominal hidden-parameter scatter가 있는 원 core 그림과 exact-GT 주석이 포함될 수 있는 final dashboard/video 역시 복사하지 않았다. 숨긴 물성값이 없는 대체 표·검증된 자료를 사용한다. [공개 필터 내역](evidence/publication-filter.json)

`private/`, oracle 정답 파일, 평가 전용 원본 mesh, 대형 PLY/checkpoint, training data, vendor, 가상환경·캐시는 공개 묶음에 없다. `evidence/source-map.json`은 로컬 원본경로와 원본/복사본 해시를 연결하는 비공개 인덱스이며 `.gitignore`에 넣었다. 공개 문서·JSON의 개인 절대경로는 placeholder로 바꾸고 원본은 그대로 두었다.

이번 확인 범위는 공개 수치 재계산, 원 artifact와 문서 대조, 소스 구문 분석, 주요 이미지 확인, frozen hash와 입력 해시의 일치 확인이다. 원본 영상 전체의 프레임별 포렌식, GPU 재학습, PhysX 재실행, 새로 설치한 환경에서의 전체 테스트는 수행하지 않았다.

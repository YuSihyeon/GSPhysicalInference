# GS-bound Physical Digital Twin: 핵심 PhysX pilot 결과

## 한 줄 결론

Semantic/material prior에 passive inverse physics를 더하면 보지 않은 미래 운동 예측은 뚜렷하게 좋아졌지만, 현재 adaptive selector가 같은 3회 예산의 fixed schedule보다 낫다는 주가설은 이 pilot에서 **지지되지 않음**.

## 실험

- 독립 hidden-GT 단위: 12개, 실패 0개
- 모든 조건은 동일한 GS-derived geometry, passive 관측, 센서 노이즈, held-out 행동을 공유
- 비교: prior only → prior+passive → fixed active 3회 / adaptive active 3회
- 평가: 식별에 쓰지 않은 impulse, breakaway ramp, oblique drop의 미래 운동

## 핵심 수치

- 평균 translation NRMSE: prior `0.2882` → passive `0.1345` → fixed `0.1505` / adaptive `0.1464`
- fixed AUC − adaptive AUC: 평균 `-0.0275`, 95% bootstrap CI `[-0.1499, 0.0599]`, exact sign-flip p=`0.794`
- adaptive 승리 8개, fixed 승리 4개

## 왜 adaptive가 안정적으로 이기지 못했는가

가장 큰 실패 단위는 `unit_005`였다. Adaptive는 `incline:2,vertical_accel:1.5,vertical_accel:0.8`를 선택해 낙하 probe를 수행하지 않았다. 그 결과 반발계수 오류가 held-out oblique drop으로 직접 전파됐다. 현재 selector의 점수는 단일 관측의 파라미터 정보량에 가깝고, 실제 held-out 미래 운동 위험을 충분히 반영하지 못한다. 또한 입자 posterior의 재표본화가 재질 prior의 파라미터 상관을 증폭해 관측하지 않은 반발계수까지 이동시키는 현상이 확인됐다.

## 정지마찰에서 확인된 문제

설정한 nominal static friction과 실제 breakaway에서 계산한 effective coefficient의 평균 차이는 `0.2035`였다. 따라서 nominal GT 값 회복과 실제 운동 예측 성능은 별도로 평가해야 한다.

## 해석 범위

이 결과는 **pilot evidence**이며 확정적 결론이 아니다. 현재 복원은 photometric 3DGS 학습본이 아니라 RGB-D-initialized Gaussian 표현이고, 한 가지 GS geometry만 사용했다. 상호작용은 simulator actuator가 만들었으며 R1 Pro는 아직 접촉 제어를 하지 않았다. 추론과 평가가 같은 PhysX를 공유한다는 self-consistency 한계도 남는다.

## 다음 실험

1. selector를 expected held-out trajectory-risk reduction으로 바꾸고, 서로 다른 물성 종류를 최소 한 번씩 탐색하도록 하는 조건을 탐색적 후속 실험으로 비교한다.
2. 결과를 고정한 뒤 대표 GT 단위에서 R1 Pro가 실제 접촉으로 같은 probe를 재현한다.
3. photometric 3DGS와 여러 GS-derived collider로 geometry 일반화를 검증한다.
